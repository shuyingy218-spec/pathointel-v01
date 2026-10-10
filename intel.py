"""Public evidence helpers: no credentials or persistent user storage."""
import io
import ipaddress
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

import pandas as pd

COLUMNS = ['产品名称', '厂商', '产品类别', '应用场景', '参考价格（万元）', '核心特点', '来源URL', '获取日期', '来源方式', '核验状态', '数据性质', '记录编号', '决定日期']


def today():
    return datetime.now(timezone(timedelta(hours=8))).date().isoformat()


def demo_rows():
    values = [('示例超声 A', '甲', '影像设备', '门诊', '18', '便携式设计'), ('示例监护 B', '乙', '监护设备', '病房', '6', '多参数监测'), ('示例检验 C', '丙', '检验设备', '检验科', '25', '小型自动化')]
    return pd.DataFrame([{**dict(zip(COLUMNS[:6], [f'{n}（虚构）', f'示例厂商{v}（虚构）', c, s, p, f'{f}（虚构）'])), '来源URL': 'https://github.com/shuyingy218-spec/pathointel-v01', '获取日期': today(), '来源方式': '虚构示例', '核验状态': '待核（虚构）', '数据性质': '虚构演示', '记录编号': f'DEMO-{i}', '决定日期': ''} for i, (n, v, c, s, p, f) in enumerate(values, 1)], columns=COLUMNS)


def public_url(value):
    parts = urlsplit(value)
    if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password:
        raise ValueError('来源URL必须是无账号密码的公开 http/https 链接。')
    host = parts.hostname.lower()
    if '.' not in host or host.endswith(('.local', '.internal')) or host == 'localhost':
        raise ValueError('请提供公开来源链接。')
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError('请提供公开来源链接。')
    return value


def normalize(frame, mode):
    if len(frame) == 0 or len(frame) > 500:
        raise ValueError('每次提交应包含 1–500 行。')
    if not {'产品名称', '来源URL'}.issubset(frame.columns):
        raise ValueError('必须包含“产品名称”和“来源URL”两列。')
    data = frame.reindex(columns=COLUMNS, fill_value='').fillna('').astype(str)
    for col in COLUMNS:
        data[col] = data[col].str.strip()
        if data[col].str.len().gt(2000).any():
            raise ValueError('单个字段不能超过 2000 字符。')
    if data['产品名称'].eq('').any() or data['来源URL'].eq('').any():
        raise ValueError('产品名称和来源URL不能为空；本次未导入任何行。')
    for value in data['来源URL']:
        public_url(value)
    data['获取日期'] = data['获取日期'].replace('', today())
    for value in data['获取日期']:
        try:
            date = datetime.strptime(value, '%Y-%m-%d').date()
            if date.isoformat() != value or value > today():
                raise ValueError()
        except ValueError as error:
            raise ValueError('获取日期必须是 YYYY-MM-DD，且不能晚于今天。') from error
    data['来源方式'] = mode
    data['核验状态'] = '待核'
    data['数据性质'] = '公开资料（待核）'
    return data


def merge_rows(existing, incoming):
    combined = pd.concat([existing, incoming], ignore_index=True)
    # ponytail: bounded session data; persistent multiuser storage would need a database.
    unique = combined.drop_duplicates(['产品名称', '厂商', '来源URL', '记录编号'], keep='first')
    if len(unique) > 500:
        raise ValueError('当前会话最多 500 行，请导出后清空再继续。')
    return unique.reset_index(drop=True), len(unique) - len(existing)


def import_csv(content):
    if len(content) > 1_000_000:
        raise ValueError('CSV 文件不能超过 1 MB。')
    try:
        frame = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False, encoding='utf-8-sig')
    except (ValueError, UnicodeError, pd.errors.ParserError) as error:
        raise ValueError('无法读取 CSV，请使用 UTF-8 编码及标准列名。') from error
    if frame.columns.duplicated().any() or any(re.fullmatch(r'.+\.\d+', str(c)) for c in frame.columns):
        raise ValueError('CSV 不能有重复列名。')
    return normalize(frame, 'CSV导入')


def csv_bytes(frame):
    safe = frame.copy().fillna('').astype(str)
    for col in safe:
        safe[col] = safe[col].map(lambda v: "'" + v if v.lstrip().startswith(('=', '+', '-', '@')) or v.startswith(('\t', '\r', '\n')) else v)
    return safe.to_csv(index=False).encode('utf-8-sig')


def search_fda(keyword):
    keyword = keyword.strip()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 -]{1,79}', keyword) or not keyword.split():
        raise ValueError('请输入 2–80 字符的公开英文产品名或厂商名，仅支持字母、数字、空格和连字符。')
    terms = ' AND '.join(f'(device_name:{word} OR applicant:{word})' for word in keyword.split())
    url = 'https://api.fda.gov/device/510k.json?' + urlencode({'search': terms, 'limit': 5, 'sort': 'decision_date:desc'})
    request = Request(url, headers={'User-Agent': 'PathoIntel/0.2', 'Accept': 'application/json'})
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read(2_000_000))
    except HTTPError as error:
        if error.code == 404:
            return pd.DataFrame(columns=COLUMNS)
        raise ValueError('FDA 检索暂不可用或达到共享限额，请稍后重试；没有添加数据。') from error
    except (URLError, TimeoutError, OSError, ValueError) as error:
        raise ValueError('FDA 检索失败，请稍后重试或手动录入公开资料；没有添加数据。') from error
    if not isinstance(payload, dict) or not isinstance(payload.get('results'), list):
        raise ValueError('FDA 响应格式异常，没有添加数据。')
    rows = []
    for item in payload['results'][:5]:
        if not isinstance(item, dict):
            continue
        number = str(item.get('k_number', ''))
        if not re.fullmatch(r'K\d{6}', number) or not item.get('device_name'):
            continue
        rows.append({'产品名称': item['device_name'], '厂商': item.get('applicant', ''), '产品类别': 'FDA 510(k)记录', '应用场景': '待核', '核心特点': f"FDA决定：{item.get('decision_description', '待核')}；不推断性能或临床用途", '来源URL': f'https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID={number}', '获取日期': today(), '记录编号': number, '决定日期': str(item.get('decision_date', ''))})
    return normalize(pd.DataFrame(rows), '联网检索') if rows else pd.DataFrame(columns=COLUMNS)


def brief(frame):
    start = (datetime.fromisoformat(today()).date() - timedelta(days=6)).isoformat()
    recent = frame[(frame['获取日期'] >= start) & (frame['数据性质'] != '虚构演示')]
    lines = [f'PathoIntel v0.2｜每周竞品资料简报草稿（{start} 至 {today()}）', '范围：当前筛选中，最近7天获取的公开资料；获取日期不是新闻发生日期。', '以下资料均待核；不代表市场全貌或临床建议。', f'资料数：{len(recent)}', '']
    for _, row in recent.iterrows():
        lines += [f"产品：{row['产品名称']}｜厂商：{row['厂商'] or '待核'}", f"记录：{row['核心特点'] or '待补充'}", f"来源：{row['来源URL']}", f"获取日期：{row['获取日期']}｜来源方式：{row['来源方式']}｜{row['核验状态']}", '']
    lines += ['需人工填写：', '1. 本周值得关注的变化（附证据）：', '2. 对我方产品的影响（假设及依据）：', '3. 待核问题及下一步：']
    return '\n'.join(lines)
