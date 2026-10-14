import pandas as pd
import streamlit as st
from urllib.parse import quote_plus
from intel import COLUMNS, brief, csv_bytes, demo_rows, import_csv, merge_rows, normalize, search_fda, today
from official_search import official_vendor, search_official
from dossier import ITEMS, FIELDS, add_evidence, comparison_brief, dossier_brief, import_evidence_csv, profile_table, seed_evidence

st.set_page_config(page_title='PathoIntel v0.4', layout='wide')
st.title('PathoIntel v0.4')
st.caption('搜索官网 → 核对原文 → 记录产品事实 → 与达科为对比 → 导出')
line = st.sidebar.text_input('当前研究产品线', 'EBER/CISH', max_chars=80).strip()
st.sidebar.caption('我司基准：达科为。可切换产品线；请在离开前导出证据 CSV，回来时可导入恢复。')
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
for key in ('ev_vendor', 'ev_product', 'ev_url'):
    st.session_state.setdefault(key, '')
rid = st.session_state.reset_id

def add_rows(data):
    merged, count = merge_rows(st.session_state.records, data)
    st.session_state.records = merged
    st.success(f'新增 {count} 条；重复项 {len(data)-count} 条。新增资料均待核。')

st.header('1｜搜索并核对官网资料')
st.caption('输入任意产品或厂商名称。搜索结果是待核候选，不是已确认的产品事实。')
with st.form(f'web-{rid}'):
    query = st.text_input('产品／厂商关键词', 'EBER', max_chars=80)
    domain = st.text_input('限定官网域名（可选）', placeholder='例如 diagnostics.roche.com', max_chars=200)
    web_submit = st.form_submit_button('搜索并整理网页结果')
search_query = query.strip() + (f' site:{domain.strip()}' if domain.strip() else ' pathology product official')
st.link_button('在浏览器打开实时搜索结果', 'https://www.bing.com/search?q=' + quote_plus(search_query))
st.caption('如云端搜索服务暂不可用，可用上方按钮在浏览器搜索引擎查看实时结果，再将核对后的事实录入下方“补充证据”。')
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
    idx = st.selectbox('选择要核对的网页', range(len(st.session_state.website_results)), format_func=lambda i: st.session_state.website_results[i]['页面标题'], key='web-choice')
    chosen = st.session_state.website_results[idx]
    st.link_button('打开这条网页的原文', chosen['链接'])
    if st.button('用这条来源录入产品事实'):
        st.session_state.ev_vendor = official_vendor(chosen['链接']) or ''
        st.session_state.ev_product = st.session_state.get('website_query', query).strip()
        st.session_state.ev_url = chosen['链接']
        st.rerun()

st.subheader('核对原文后，逐条记录事实')
st.caption('每条事实对应一个来源。产品名称请写具体试剂或设备型号；价格注明地区、日期、单位与口径；备案注明主体、证号、地区与状态。')
with st.form('evidence-form'):
    ev_vendor = st.text_input('厂商 *', key='ev_vendor', max_chars=200)
    ev_product = st.text_input('试剂或设备产品名称／型号 *', key='ev_product', max_chars=200)
    ev_item = st.selectbox('信息项目', ITEMS)
    ev_content = st.text_area('原文支持的具体事实 *', max_chars=2000)
    ev_url = st.text_input('来源 URL *', key='ev_url', max_chars=2000)
    ev_note = st.text_input('来源说明／地区／版本／页码', max_chars=500)
    reviewed = st.checkbox('我已打开并核对原文；本条内容不是搜索摘要推断')
    ev_submit = st.form_submit_button('保存到产品证据卡')
if ev_submit:
    if not reviewed:
        st.error('请先打开并核对原文，再保存产品事实。')
    else:
        try:
            st.session_state.dossier_records = add_evidence(st.session_state.dossier_records, {'产品线': line, '厂商': ev_vendor, '产品名称': ev_product, '信息项目': ev_item, '内容': ev_content, '来源URL': ev_url, '来源说明': ev_note}, reviewed=True)
            st.success('已保存；下方产品证据卡、对比和简报已更新。')
        except ValueError as error:
            st.error(str(error))

st.header(f'2｜{line} 产品证据卡与达科为对比')
st.caption('初始 EBER/CISH 证据来自厂商公开产品页或说明书。每项保留来源链接；价格和注册备案未在已录入来源中确认时显示待核。')
evidence = st.session_state.dossier_records
line_data = evidence[evidence['产品线'] == line]
t_profiles, t_compare, t_sources, t_brief = st.tabs(['产品证据卡', '达科为对比', '证据台账与恢复', '产品线资料汇编'])
with t_profiles:
    profiles = profile_table(evidence, line)
    if profiles.empty:
        st.info('当前产品线尚无证据。请在上方搜索并录入第一条事实。')
    else:
        st.dataframe(profiles, hide_index=True, width='stretch')
        card_idx = st.selectbox('查看具体产品及其逐项来源', range(len(profiles)), format_func=lambda i: f"{profiles.iloc[i]['厂商']}｜{profiles.iloc[i]['产品名称']}")
        card = profiles.iloc[card_idx]
        card_facts = line_data[(line_data['厂商'] == card['厂商']) & (line_data['产品名称'] == card['产品名称'])]
        st.dataframe(card_facts[['信息项目', '内容', '来源URL', '来源说明', '获取日期', '证据状态']], hide_index=True, width='stretch', column_config={'来源URL': st.column_config.LinkColumn('打开原文')})
        st.download_button('导出产品卡 CSV', csv_bytes(profiles), 'pathointel_product_cards.csv', 'text/csv')
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
        brief_text = comparison_brief(evidence, line, rival)
        st.download_button('下载达科为对比简报', brief_text.encode('utf-8-sig'), 'pathointel_dakewe_comparison.txt', 'text/plain')
    else:
        st.info('当前产品线尚无竞品证据；请先在“补充证据”录入达科为和竞品资料。')
with t_sources:
    st.dataframe(line_data, hide_index=True, width='stretch', column_config={'来源URL': st.column_config.LinkColumn('来源')})
    st.download_button('导出当前产品线证据 CSV', csv_bytes(line_data.reindex(columns=FIELDS)), 'pathointel_product_evidence.csv', 'text/csv', disabled=line_data.empty)
    st.download_button('备份全部产品线证据 CSV', csv_bytes(evidence.reindex(columns=FIELDS)), 'pathointel_all_evidence.csv', 'text/csv')
    restore_file = st.file_uploader('从此前导出的产品证据 CSV 恢复（最多 1 MB）', type=['csv'], max_upload_size=1, key='restore-evidence')
    if st.button('恢复证据', disabled=restore_file is None):
        try:
            st.session_state.dossier_records, count = import_evidence_csv(evidence, restore_file.getvalue())
            st.success(f'恢复 {count} 条新证据；重复项已跳过。')
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
