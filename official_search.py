"""Search pathology product pages on general web engines."""
import re
from urllib.parse import urlsplit

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

def search_official(keyword, domain=''):
    keyword = keyword.strip()
    if len(keyword) < 2 or len(keyword) > 80 or not re.fullmatch(r'[\w\s\-（）()·.]+', keyword):
        raise ValueError('请输入 2–80 字的公开产品或厂商关键词。')
    domain = domain.strip().lower()
    if domain and (len(domain) > 200 or not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}', domain)):
        raise ValueError('域名格式无效，请只输入域名，例如 diagnostics.roche.com。')
    query = f'{keyword} site:{domain}' if domain else f'{keyword} 病理 产品 官网'
    try:
        from ddgs import DDGS
        found = DDGS(timeout=12).text(query, region='cn-zh', max_results=30, backend='auto')
    except Exception as error:
        raise ValueError('官网搜索服务暂不可用；没有添加资料，请稍后重试。') from error
    rows, seen = [], set()
    for item in found or []:
        url = str(item.get('href', '')).strip()
        parts = urlsplit(url)
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or url in seen:
            continue
        if domain and not (parts.hostname.lower() == domain or parts.hostname.lower().endswith('.' + domain)):
            continue
        seen.add(url)
        vendor = official_vendor(url)
        rows.append({'来源核验': f'已识别厂商域名：{vendor}' if vendor else '官网身份待核', '网站域名': parts.hostname.lower(), '页面标题': str(item.get('title', ''))[:200], '搜索摘要（待核）': str(item.get('body', ''))[:400], '链接': url})
    rows.sort(key=lambda row: not row['来源核验'].startswith('已识别'))
    return rows[:8]
