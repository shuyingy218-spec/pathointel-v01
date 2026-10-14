"""Search public pathology product pages and label recognized vendor domains."""
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

OFFICIAL_DOMAINS = {
    'leicabiosystems.com': 'Leica Biosystems',
    'roche.com': 'Roche Diagnostics',
    'zsbio.com': '中杉金桥',
    'celnovte.com': '赛诺特',
    'gzlbp.com': '安必平',
    'dakewemedical.com': '达科为',
}


def official_vendor(url):
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
        return None
    host = parts.hostname.lower().rstrip('.')
    for domain, vendor in OFFICIAL_DOMAINS.items():
        if host == domain or host.endswith('.' + domain):
            return vendor
    return None


def _bing_rss(query):
    url = 'https://www.bing.com/search?' + urlencode({'format': 'rss', 'q': query})
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0 PathoIntel/0.3', 'Accept': 'application/rss+xml, application/xml'})
    with urlopen(request, timeout=9) as response:
        root = ET.fromstring(response.read(1_000_000))
    return [{'title': item.findtext('title', ''), 'href': item.findtext('link', ''), 'body': item.findtext('description', '')} for item in root.findall('./channel/item')]


def search_official(keyword, domain=''):
    keyword = keyword.strip()
    if len(keyword) < 2 or len(keyword) > 80 or not re.fullmatch(r'[\w\s\-（）()·.]+', keyword):
        raise ValueError('请输入 2–80 字的公开产品或厂商关键词。')
    domain = domain.strip().lower()
    if domain and (len(domain) > 200 or not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}', domain)):
        raise ValueError('域名格式无效，请只输入域名，例如 diagnostics.roche.com。')
    query = f'{keyword} site:{domain}' if domain else f'{keyword} 病理 产品 官网'
    found = []
    try:
        found = _bing_rss(query)
    except Exception:
        pass
    if not found:
        try:
            from ddgs import DDGS
            for backend in ('bing', 'brave'):
                try:
                    found = DDGS(timeout=5).text(query, max_results=20, backend=backend)
                    if found:
                        break
                except Exception:
                    continue
        except ImportError:
            pass
    if not found:
        raise ValueError('当前云端无法连接网页搜索源；没有添加资料。请使用本页“在浏览器打开实时搜索结果”入口查看搜索结果。')

    rows, seen = [], set()
    for item in found:
        url = str(item.get('href', item.get('url', ''))).strip()
        parts = urlsplit(url)
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or url in seen:
            continue
        host = parts.hostname.lower()
        if domain and host != domain and not host.endswith('.' + domain):
            continue
        seen.add(url)
        vendor = official_vendor(url)
        rows.append({'来源核验': f'已识别厂商域名：{vendor}' if vendor else '官网身份待核', '网站域名': host, '页面标题': str(item.get('title', ''))[:200], '搜索摘要（待核）': str(item.get('body', ''))[:400], '链接': url})
    rows.sort(key=lambda row: not row['来源核验'].startswith('已识别'))
    return rows[:8]
