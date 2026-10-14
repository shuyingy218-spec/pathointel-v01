"""Field-level, source-linked EBER/CISH product evidence."""
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
    ('达科为', '达科为 EBER 配套试剂（待核）', '目标试剂', '当前核对的 NS40 设备页未列出具体 EBER 试剂货号；需另查产品目录或说明书，不能据此推断有无自有 EBER 试剂。', 'https://cn.dakewemedical.com/ihc-ish-instruments/NS40_IHC_Stainer.html'),
]

def seed_evidence():
    return pd.DataFrame([['EBER/CISH', vendor, product, item, content, url, '厂商公开网页/说明书；页面地区与版本待复核', today(), '厂商表述，待独立核验'] for vendor, product, item, content, url in PUBLIC_FACTS], columns=FIELDS)

def add_evidence(existing, row):
    values = {field: str(row.get(field, '')).strip() for field in FIELDS}
    if any(not values[field] for field in ['产品线', '厂商', '产品名称', '内容', '来源URL']):
        raise ValueError('产品线、厂商、产品名称、内容和来源URL均必填。')
    if values['信息项目'] not in ITEMS or any(len(value) > 2000 for value in values.values()):
        raise ValueError('信息项目无效或字段超过 2000 字。')
    public_url(values['来源URL'])
    values['获取日期'], values['证据状态'] = today(), '人工录入，待核'
    result = pd.concat([existing, pd.DataFrame([values], columns=FIELDS)], ignore_index=True)
    result = result.drop_duplicates(['产品线', '厂商', '产品名称', '信息项目', '内容', '来源URL'])
    if len(result) > 500:
        raise ValueError('本会话最多保存 500 条证据。')
    return result.reset_index(drop=True)

def profile_table(evidence, line):
    subset = evidence[evidence['产品线'] == line]
    vendors = list(dict.fromkeys(['达科为', *subset['厂商'].tolist()]))
    rows = []
    for vendor in vendors:
        row = {'厂商': vendor}
        for item in ITEMS:
            claims = subset[(subset['厂商'] == vendor) & (subset['信息项目'] == item)]['内容'].drop_duplicates()
            row[item] = '\n'.join(claims) if len(claims) else '未公开／待人工核验'
        rows.append(row)
    return pd.DataFrame(rows)

def dossier_brief(evidence, line):
    subset = evidence[evidence['产品线'] == line]
    lines = [f'PathoIntel｜{line} 产品资料简报草稿｜{today()}', '范围：当前录入资料；获取日期不是产品发布或新闻发生日期。', '我司基准：达科为。事实保留来源，不自动判断优劣。', '']
    for _, row in subset.iterrows():
        lines.extend([f"{row['厂商']}｜{row['产品名称']}｜{row['信息项目']}", row['内容'], f"来源：{row['来源URL']}｜{row['来源说明']}", f"获取：{row['获取日期']}｜{row['证据状态']}", ''])
    lines.extend(['待补：价格单位/地区/时间/口径；注册备案主体/证号/地区/状态；设备与试剂版本兼容性。', '待人工填写：本周变化、对达科为的影响、需验证事项。', '高阶提纲：市场细分、需求采购、厂商布局与渠道、价格准入、竞争变化、机会风险。'])
    return '\n'.join(lines)
