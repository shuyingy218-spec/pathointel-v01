import pandas as pd
import streamlit as st
from intel import COLUMNS, brief, csv_bytes, demo_rows, import_csv, merge_rows, normalize, search_fda, today
from official_search import search_official
from dossier import ITEMS, add_evidence, dossier_brief, profile_table, seed_evidence

st.set_page_config(page_title='PathoIntel v0.3', layout='wide')
st.title('PathoIntel v0.3')
st.caption('病理产品资料工作台 · 官网联网搜索 · 达科为产品对比')
line = st.sidebar.text_input('当前研究产品线', 'EBER/CISH', max_chars=80).strip()
st.sidebar.caption('我司基准：达科为。可切换至其他产品线。当前数据仅保存在会话中，请下载留存。')
if not line:
    st.info('请填写产品线名称。')
    st.stop()
st.warning('公开资料研究工具，不提供临床建议。初始 3 条通用表格数据为虚构示例；价格及备案缺口标为待核。请勿录入敏感信息。')
st.caption('会话数据不会写入 GitHub 或持久保存；刷新/重启可能清空。搜索关键词会发送至公开网页搜索服务或 FDA。')
if 'records' not in st.session_state:
    st.session_state.records = demo_rows()
    st.session_state.search_results = pd.DataFrame(columns=COLUMNS)
st.session_state.setdefault('website_results', [])
st.session_state.setdefault('dossier_records', seed_evidence())
st.session_state.setdefault('reset_id', 0)
rid = st.session_state.reset_id

def add_rows(data):
    merged, count = merge_rows(st.session_state.records, data)
    st.session_state.records = merged
    st.success(f'新增 {count} 条；重复项 {len(data)-count} 条。新增资料均待核。')

st.header('1｜病理产品官网资料联网搜索')
st.caption('输入任意产品或厂商名称。搜索结果来自网页搜索服务；优先标出已识别的厂商域名。请打开原文核实后再录入。')
with st.form(f'web-{rid}'):
    query = st.text_input('产品／厂商关键词', 'EBER', max_chars=80)
    domain = st.text_input('限定官网域名（可选）', placeholder='例如 diagnostics.roche.com', max_chars=200)
    web_submit = st.form_submit_button('联网搜索官网资料')
if web_submit:
    st.session_state.website_results = []
    try:
        with st.spinner('正在联网搜索…'):
            st.session_state.website_results = search_official(query, domain)
        st.session_state.website_query = query
        if not st.session_state.website_results:
            st.info('本次没有可展示结果；这不代表产品不存在。可改用厂商全称或型号。')
    except ValueError as error:
        st.error(str(error))
if st.session_state.website_results:
    st.caption(f"搜索日期：{today()}。摘要未经核验；已识别域名不代表网页主张已核实。")
    st.dataframe(pd.DataFrame(st.session_state.website_results), hide_index=True, width='stretch', column_config={'链接': st.column_config.LinkColumn('打开来源')})
    idx = st.selectbox('选择一条来源加入通用来源台账', range(len(st.session_state.website_results)), format_func=lambda i: st.session_state.website_results[i]['页面标题'], key='web-choice')
    if st.button('加入来源台账'):
        chosen = st.session_state.website_results[idx]
        try:
            add_rows(normalize(pd.DataFrame([{'产品名称': chosen['页面标题'] or st.session_state.get('website_query','搜索结果'), '厂商': '', '产品类别': line, '核心特点': '搜索摘要（待核）：' + chosen['搜索摘要（待核）'], '来源URL': chosen['链接']}]), '官网候选搜索'))
        except ValueError as error:
            st.error(str(error))

st.header(f'2｜{line} 产品资料与达科为对比')
st.caption('初始 EBER/CISH 证据来自厂商公开产品页或说明书。每项保留来源链接；价格和注册备案未在已录入来源中确认时显示待核。')
evidence = st.session_state.dossier_records
line_data = evidence[evidence['产品线'] == line]
t_profiles, t_compare, t_sources, t_add, t_brief = st.tabs(['产品画像', '达科为对比', '证据明细', '补充证据', '产品线简报'])
with t_profiles:
    profiles = profile_table(evidence, line)
    st.dataframe(profiles, hide_index=True, width='stretch')
    st.download_button('导出产品画像 CSV', csv_bytes(profiles), 'pathointel_profiles.csv', 'text/csv')
with t_compare:
    rivals = list(dict.fromkeys(v for v in line_data['厂商'] if v != '达科为'))
    if rivals:
        rival = st.selectbox('对比厂商', rivals)
        for item in ITEMS:
            with st.expander(item, expanded=item in ['目标试剂','配套自动化设备']):
                for vendor in ['达科为', rival]:
                    st.markdown(f'**{vendor}**')
                    matches = line_data[(line_data['厂商'] == vendor) & (line_data['信息项目'] == item)]
                    if matches.empty:
                        st.caption('待核：尚未录入该项目的来源证据。')
                    else:
                        st.dataframe(matches[['产品名称','内容','来源URL','来源说明','证据状态']], hide_index=True, width='stretch', column_config={'来源URL': st.column_config.LinkColumn('来源')})
        st.caption('并列展示来源内容，不自动判定优劣；不同型号、地区和条件不可直接比较。')
    else:
        st.info('当前产品线尚无竞品证据；请先在“补充证据”录入达科为和竞品资料。')
with t_sources:
    st.dataframe(line_data, hide_index=True, width='stretch', column_config={'来源URL': st.column_config.LinkColumn('来源')})
    st.download_button('导出产品证据 CSV', csv_bytes(line_data), 'pathointel_product_evidence.csv', 'text/csv')
with t_add:
    st.caption('打开来源原文后，每条事实单独录入。价格请注明地区、日期、单位和口径；备案请注明证号、主体、地区和状态。')
    with st.form('evidence-form'):
        ev_vendor = st.text_input('厂商', max_chars=200)
        ev_product = st.text_input('试剂或自动化设备名称', max_chars=200)
        ev_item = st.selectbox('信息项目', ITEMS)
        ev_content = st.text_area('来源明确支持的内容', max_chars=2000)
        source_options = ['手动填写'] + [r['链接'] for r in st.session_state.website_results]
        ev_source = st.selectbox('搜索来源（或手动填写）', source_options)
        ev_url = st.text_input('来源 URL', max_chars=2000)
        ev_note = st.text_input('来源说明／版本／页码', max_chars=500)
        ev_submit = st.form_submit_button('保存证据')
    if ev_submit:
        try:
            st.session_state.dossier_records = add_evidence(evidence, {'产品线': line, '厂商': ev_vendor, '产品名称': ev_product, '信息项目': ev_item, '内容': ev_content, '来源URL': ev_url if ev_source == '手动填写' else ev_source, '来源说明': ev_note})
            st.rerun()
        except ValueError as error:
            st.error(str(error))
with t_brief:
    report = dossier_brief(evidence, line)
    st.text(report)
    st.download_button('下载产品线简报草稿', report.encode('utf-8-sig'), 'pathointel_product_brief.txt', 'text/plain')
    st.caption('分析提纲：市场细分、需求采购、厂商布局渠道、价格与准入、竞争变化、机会风险和验证动作。')

st.header('3｜公开资料台账、筛选和导出')
with st.expander('手动录入或 CSV 导入'):
    with st.form(f'manual-{rid}'):
        name = st.text_input('产品名称 *', max_chars=200)
        vendor = st.text_input('厂商', max_chars=200)
        category = st.text_input('产品类别', max_chars=100)
        scene = st.text_input('应用场景', max_chars=100)
        notes = st.text_area('公开资料摘要', max_chars=1500)
        url = st.text_input('公开来源 URL *', max_chars=2000)
        acquired = st.date_input('获取日期', value=pd.Timestamp(today()).date())
        submitted = st.form_submit_button('添加公开资料')
    if submitted:
        try:
            add_rows(normalize(pd.DataFrame([{'产品名称':name,'厂商':vendor,'产品类别':category,'应用场景':scene,'核心特点':notes,'来源URL':url,'获取日期':acquired.isoformat()}]), '手动录入'))
        except ValueError as error:
            st.error(str(error))
    st.download_button('下载 CSV 模板', csv_bytes(pd.DataFrame(columns=COLUMNS)), 'pathointel_template.csv', 'text/csv')
    upload = st.file_uploader('导入 UTF-8 CSV（最多 1 MB／500 行）', type=['csv'], max_upload_size=1, key=f'csv-{rid}')
    if st.button('导入 CSV', disabled=upload is None):
        try:
            add_rows(import_csv(upload.getvalue()))
        except ValueError as error:
            st.error(str(error))
with st.expander('FDA 510(k) 检索｜美国记录'):
    st.caption('只覆盖 FDA 510(k)，不覆盖中国备案或全网消息。')
    with st.form(f'fda-{rid}'):
        fda_query = st.text_input('公开英文产品／厂商关键词', 'microscope', max_chars=80)
        fda_submit = st.form_submit_button('检索 FDA 记录')
    if fda_submit:
        try:
            st.session_state.search_results = search_fda(fda_query)
        except ValueError as error:
            st.error(str(error))
    if not st.session_state.search_results.empty:
        st.dataframe(st.session_state.search_results, hide_index=True, width='stretch', column_config={'来源URL': st.column_config.LinkColumn('来源')})
        if st.button('加入当前会话台账'):
            add_rows(st.session_state.search_results)
records = st.session_state.records
c1, c2, c3 = st.columns(3)
category_filter = c1.selectbox('产品类别', ['全部', *sorted(v for v in records['产品类别'].unique() if v)], key=f'cat-{rid}')
mode_filter = c2.selectbox('来源方式', ['全部', *records['来源方式'].unique()], key=f'mode-{rid}')
scene_filter = c3.selectbox('应用场景', ['全部', *sorted(v for v in records['应用场景'].unique() if v)], key=f'scene-{rid}')
filtered = records
if category_filter != '全部': filtered = filtered[filtered['产品类别'] == category_filter]
if mode_filter != '全部': filtered = filtered[filtered['来源方式'] == mode_filter]
if scene_filter != '全部': filtered = filtered[filtered['应用场景'] == scene_filter]
st.caption(f'当前 {len(filtered)} / {len(records)} 条；演示数据均明确标为虚构。')
st.dataframe(filtered, hide_index=True, width='stretch', column_config={'来源URL': st.column_config.LinkColumn('来源')})
st.download_button('导出当前台账 CSV', csv_bytes(filtered), 'pathointel_public_evidence.csv', 'text/csv', disabled=filtered.empty)
weekly = brief(filtered)
with st.expander('每周竞品资料简报'):
    st.text(weekly)
    st.download_button('下载每周简报 TXT', weekly.encode('utf-8-sig'), 'pathointel_weekly_brief.txt', 'text/plain')
if st.button('清空本会话并恢复 3 条虚构示例'):
    st.session_state.clear()
    st.session_state.reset_id = rid + 1
    st.rerun()
