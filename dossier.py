"""Field-level pathology product evidence and reproducible comparison exports."""
import io
from datetime import datetime, timedelta

import pandas as pd
from intel import public_url, today

ITEMS = ['目标试剂', '配套自动化设备', '组成', '技术特点', '产品布局', '价格与口径', '注册备案情况']
FIELDS = ['产品线', '厂商', '产品名称', '信息项目', '内容', '来源URL', '来源说明', '获取日期', '证据状态']

PUBLIC_FACTS = [
    ('Roche', 'VENTANA EBER Probe', '目标试剂', '厂商产品页列出 VENTANA EBER Probe。页面和货号需按销售地区核对。', 'https://diagnostics.roche.com/global/en/products/lab/ventana-eber-probe-pid00000975.html'),
    ('Roche', 'VENTANA EBER Probe', '组成', '厂商页列出 DIG 标记 EBER 探针、Magenta ISH DIG Detection Kit 与 ISH TSA Ancillary Kit。', 'https://diagnostics.roche.com/global/en/products/lab/ventana-eber-probe-pid00000975.html'),
    ('Roche', 'VENTANA EBER Probe', '配套自动化设备', '厂商页说明用于 BenchMark IHC/ISH 仪器；具体型号兼容性需按说明书核对。', 'https://diagnostics.roche.com/global/en/products/lab/ventana-eber-probe-pid00000975.html'),
    ('Leica', 'BOND EBER Probe PB0589', '目标试剂', '厂商产品页列出 BOND EBER Probe PB0589。具体地区版本需核对。', 'https://shop.leicabiosystems.com/ko/ihc-ish/ish-probes-molecular-pathology/pid-bond-eber-probe'),
    ('Leica', 'BOND EBER Probe PB0589', '组成', '厂商页列出即用型 EBER 探针 PB0589（5.5 mL），配合 Anti-Fluorescein Antibody 与 BOND Polymer Refine 检测体系。', 'https://shop.leicabiosystems.com/ko/ihc-ish/ish-probes-molecular-pathology/pid-bond-eber-probe'),
    ('中杉金桥', 'EBER 检测试剂盒 ISH-7001UM', '目标试剂', '厂商产品页列出 EBER 检测试剂盒 ISH-7001UM，规格 100 测试/盒。', 'https://zsbio.com/product/ISH-7001UM'),
    ('中杉金桥', 'EBER 检测试剂盒 ISH-7001UM', '组成', '厂商页说明为地高辛标记 EBER1/EBER2 探针、HRP 抗地高辛抗体与 DAB 显色；规格 100 测试/盒。', 'https://zsbio.com/product/ISH-7001UM'),
    ('中杉金桥', 'EBER 检测试剂盒 ISH-7001UM', '配套自动化设备', '厂商页说明机用试剂配合辅助试剂用于 UltraPATH；型号与版本兼容性待说明书核验。', 'https://zsbio.com/product/ISH-7001UM'),
    ('赛诺特', 'EBER Probe（自动化）', '目标试剂', '厂商 IFU 列出自动化 EBER Probe 试剂；提供 50/100 测试包装。', 'https://www.celnovte.com/wp-content/uploads/2022/05/EBER-for-Automated-IFU.pdf'),
    ('赛诺特', 'EBER Probe（自动化）', '组成', '厂商 IFU 列出探针、抗地高辛抗体、polymer、DAB 组分等；提供 50/100 测试包装。', 'https://www.celnovte.com/wp-content/uploads/2022/05/EBER-for-Automated-IFU.pdf'),
    ('赛诺特', 'EBER Probe（自动化）', '配套自动化设备', 'IFU 仅写 IHC automated system，未确认具体 CNT 型号。', 'https://www.celnovte.com/wp-content/uploads/2022/05/EBER-for-Automated-IFU.pdf'),
    ('达科为', 'PathDR. NS40', '配套自动化设备', '官网列出 IHC、ISH、ICC、双染及多染项目；页面未证明与特定 EBER 探针货号兼容。', 'https://cn.dakewemedical.com/ihc-ish-instruments/NS40_IHC_Stainer.html'),
    ('达科为', 'PathDR. NS40', '技术特点', '官网列出可调加样量 100/150 μL、双机械臂、满载 40 片运行约 2.5 小时。', 'https://cn.dakewemedical.com/ihc-ish-instruments/NS40_IHC_Stainer.html'),
]

def seed_evidence():
    return pd.DataFrame([['EBER/CISH', vendor, product, item, content, url, '厂商公开网页/说明书；页面地区与版本待复核', today(), '厂商表述，待独立核验'] for vendor, product, item, content, url in PUBLIC_FACTS], columns=FIELDS)

def add_evidence(existing, row, reviewed=False):
    values = {field: str(row.get(field, '')).strip() for field in FIELDS}
    if any(not values[field] for field in ['产品线', '厂商', '产品名称', '内容', '来源URL']):
        raise ValueError('产品线、厂商、产品名称、内容和来源URL均必填。')
    if values['信息项目'] not in ITEMS or any(len(value) > 2000 for value in values.values()):
        raise ValueError('信息项目无效或字段超过 2000 字。')
    public_url(values['来源URL'])
    values['获取日期'] = today()
    values['证据状态'] = '已人工核对原文' if reviewed else '人工录入，待核'
    result = pd.concat([existing, pd.DataFrame([values], columns=FIELDS)], ignore_index=True)
    result = result.drop_duplicates(['产品线', '厂商', '产品名称', '信息项目', '内容', '来源URL'])
    if len(result) > 500:
        raise ValueError('本会话最多保存 500 条证据。')
    return result.reset_index(drop=True)

def profile_table(evidence, line):
    subset = evidence[evidence['产品线'] == line]
    rows = []
    for (vendor, product), facts in subset.groupby(['厂商', '产品名称'], sort=False):
        row = {'厂商': vendor, '产品名称': product}
        for item in ITEMS:
            claims = facts[facts['信息项目'] == item]['内容'].drop_duplicates()
            row[item] = '\n'.join(claims) if len(claims) else '未公开／待人工核验'
        row['来源数'] = facts['来源URL'].nunique()
        rows.append(row)
    return pd.DataFrame(rows, columns=['厂商', '产品名称', *ITEMS, '来源数'])

def import_evidence_csv(existing, content):
    """Restore an exported evidence ledger without replacing seeded facts."""
    if not content or len(content) > 1_000_000:
        raise ValueError('证据 CSV 不能为空或超过 1 MB。')
    try:
        frame = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False, encoding='utf-8-sig')
    except (ValueError, UnicodeError, pd.errors.ParserError) as error:
        raise ValueError('无法读取证据 CSV，请使用 UTF-8 编码。') from error
    if len(frame) == 0 or len(frame) > 500 or list(frame.columns) != FIELDS:
        raise ValueError('证据 CSV 必须保留导出的 9 列原顺序，且包含 1–500 行。')
    frame = frame.fillna('').astype(str)
    for field in FIELDS:
        frame[field] = frame[field].str.strip()
        if frame[field].str.len().gt(2000).any():
            raise ValueError('单个证据字段不能超过 2000 字。')
    for field in ['产品线', '厂商', '产品名称', '信息项目', '内容', '来源URL', '获取日期', '证据状态']:
        if frame[field].eq('').any():
            raise ValueError(f'证据 CSV 的“{field}”不能为空。')
    if not frame['信息项目'].isin(ITEMS).all():
        raise ValueError('证据 CSV 包含无效的信息项目。')
    for url in frame['来源URL']:
        public_url(url)
    for value in frame['获取日期']:
        try:
            if datetime.strptime(value, '%Y-%m-%d').date().isoformat() != value or value > today():
                raise ValueError()
        except ValueError as error:
            raise ValueError('获取日期必须是 YYYY-MM-DD，且不能晚于今天。') from error
    combined = pd.concat([existing, frame], ignore_index=True)
    unique = combined.drop_duplicates(['产品线', '厂商', '产品名称', '信息项目', '内容', '来源URL'])
    if len(unique) > 500:
        raise ValueError('当前会话最多保存 500 条证据；本次未导入。')
    return unique.reset_index(drop=True), len(unique) - len(existing)

def comparison_brief(evidence, line, rival):
    """One-product-line, two-vendor brief with source links and explicit gaps."""
    scoped = evidence[evidence['产品线'] == line]
    lines = [f'PathoIntel｜{line}｜达科为 vs {rival}', f'生成日期：{today()}｜范围：当前会话已录入的公开来源', '每项为厂商表述或人工核对记录；不据此自动判断产品优劣。', '']
    gaps = []
    for item in ITEMS:
        lines.append(f'【{item}】')
        for vendor in ['达科为', rival]:
            facts = scoped[(scoped['厂商'] == vendor) & (scoped['信息项目'] == item)]
            if facts.empty:
                lines.append(f'{vendor}：未公开／待人工核验')
                gaps.append(f'{vendor}：{item}')
            else:
                for _, fact in facts.iterrows():
                    lines.append(f"{vendor}｜{fact['产品名称']}：{fact['内容']}")
                    lines.append(f"  来源：{fact['来源URL']}｜获取：{fact['获取日期']}｜{fact['证据状态']}")
        lines.append('')
    lines.append('待补证据：' + ('；'.join(gaps) if gaps else '无空缺字段；仍需核对型号、地区和版本。'))
    lines.append('分析判断与下一步：请人工填写，明确依据及待验证事项。')
    return '\n'.join(lines)

def dossier_brief(evidence, line):
    subset = evidence[evidence['产品线'] == line]
    lines = [f'PathoIntel｜{line} 产品资料简报草稿｜{today()}', '范围：当前录入资料；获取日期不是产品发布或新闻发生日期。', '我司基准：达科为。事实保留来源，不自动判断优劣。', '']
    for _, row in subset.iterrows():
        lines.extend([f"{row['厂商']}｜{row['产品名称']}｜{row['信息项目']}", row['内容'], f"来源：{row['来源URL']}｜{row['来源说明']}", f"获取：{row['获取日期']}｜{row['证据状态']}", ''])
    lines.extend(['待补：价格单位/地区/时间/口径；注册备案主体/证号/地区/状态；设备与试剂版本兼容性。', '待人工填写：本周变化、对达科为的影响、需验证事项。', '高阶提纲：市场细分、需求采购、厂商布局与渠道、价格准入、竞争变化、机会风险。'])
    return '\n'.join(lines)


def weekly_dossier_brief(evidence, line):
    """Report newly reviewed facts, without presenting built-in examples as news."""
    start = (datetime.strptime(today(), '%Y-%m-%d').date() - timedelta(days=6)).isoformat()
    scoped = evidence[evidence['产品线'] == line]
    recent = scoped[
        (scoped['获取日期'] >= start)
        & (scoped['证据状态'] == '已人工核对原文')
    ]
    lines = [
        f'PathoIntel｜{line}｜每周竞品资料简报',
        f'记录窗口：{start} 至 {today()}（按核对日期，不代表产品发布日期）',
        f'本周新增已核对证据：{len(recent)} 条；覆盖厂商：{recent["厂商"].nunique()} 家',
        '预置演示资料不计入本周新增。以下为资料整理，不自动判断优劣。',
        '',
        '【本周新增】',
    ]
    if recent.empty:
        lines.append('暂无本周新增且已核对原文的证据。')
    else:
        for _, row in recent.iterrows():
            lines.extend([
                f"{row['厂商']}｜{row['产品名称']}｜{row['信息项目']}：{row['内容']}",
                f"来源：{row['来源URL']}｜说明：{row['来源说明'] or '未填写'}",
            ])
    lines.extend(['', '【当前资料缺口】'])
    profiles = profile_table(evidence, line)
    if profiles.empty:
        lines.append('尚无本产品线资料。')
    else:
        for _, row in profiles.iterrows():
            missing = [item for item in ITEMS if row[item] == '未公开／待人工核验']
            if missing:
                lines.append(f"{row['厂商']}｜{row['产品名称']}：{'、'.join(missing)}")
        if not any(row[item] == '未公开／待人工核验' for _, row in profiles.iterrows() for item in ITEMS):
            lines.append('七个字段均有录入内容；仍需复核地区、版本和证据有效性。')
    lines.extend([
        '',
        '【人工判断与下周动作】',
        '本周值得关注的变化（需附来源）：',
        '对达科为的影响（判断及依据）：',
        '优先核对的价格、备案、试剂与设备兼容性：',
    ])
    return '\n'.join(lines)
