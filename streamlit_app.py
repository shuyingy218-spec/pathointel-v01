import pandas as pd
import streamlit as st

from intel import COLUMNS, brief, csv_bytes, demo_rows, import_csv, merge_rows, normalize, search_fda, today

st.set_page_config(page_title='PathoIntel v0.2', layout='wide')
st.title('PathoIntel v0.2')
st.caption('医疗产品竞争情报工作台 · 公开资料最小演示')
st.warning('请勿输入内部、患者、个人或其他敏感信息。初始 3 条数据全部虚构；新增公开资料均待核。不提供临床建议。')
st.caption('录入和导入内容只保存在当前浏览器会话的服务器内存，不写入 GitHub，不持久保存。刷新、断开或服务重启可能丢失，请及时导出。联网检索会将你提交的公开关键词发送给 FDA。')
if 'records' not in st.session_state:
    st.session_state.records = demo_rows()
    st.session_state.search_results = pd.DataFrame(columns=COLUMNS)


def add(data):
    merged, count = merge_rows(st.session_state.records, data)
    st.session_state.records = merged
    st.success(f'新增 {count} 条；忽略重复 {len(data) - count} 条。所有新增资料均待核。')


with st.expander('录入或导入公开资料'):
    with st.form('manual'):
        name = st.text_input('产品名称 *', max_chars=200)
        vendor = st.text_input('厂商', max_chars=200)
        category = st.text_input('产品类别', max_chars=100)
        scene = st.text_input('应用场景', max_chars=100)
        notes = st.text_area('公开资料摘要（请勿填敏感内容）', max_chars=1500)
        source = st.text_input('公开来源URL *', max_chars=2000)
        acquired = st.date_input('获取日期', value=pd.Timestamp(today()).date())
        submitted = st.form_submit_button('添加公开资料')
    if submitted:
        try:
            add(normalize(pd.DataFrame([{'产品名称': name, '厂商': vendor, '产品类别': category, '应用场景': scene, '核心特点': notes, '来源URL': source, '获取日期': acquired.isoformat()}]), '手动录入'))
        except ValueError as error:
            st.error(str(error))
    st.download_button('下载 CSV 模板', csv_bytes(pd.DataFrame(columns=COLUMNS)), 'pathointel_template.csv', 'text/csv')
    st.caption('UTF-8 CSV，必填列：产品名称、来源URL。获取日期留空时使用当天；导入一律标记为待核。最多 1 MB／500 行。')
    upload = st.file_uploader('上传公开资料 CSV', type=['csv'], max_upload_size=1)
    if st.button('导入 CSV', disabled=upload is None):
        try:
            add(import_csv(upload.getvalue()))
        except ValueError as error:
            st.error(str(error))

with st.expander('真实联网检索｜FDA 510(k)公开记录'):
    st.caption('仅查美国 FDA 510(k)记录；不覆盖中国注册、所有产品或全网新闻。按决定日期排序，最多返回5条。结果不代表搜索穷尽，也不代表产品性能。无需新密钥或付费；共享配额或网络异常会导致失败。')
    with st.form('search'):
        keyword = st.text_input('公开英文产品／厂商关键词', placeholder='microscope', max_chars=80)
        search = st.form_submit_button('检索 FDA 公开记录')
    if search:
        st.session_state.search_results = pd.DataFrame(columns=COLUMNS)
        try:
            with st.spinner('正在查询 FDA 官方记录…'):
                st.session_state.search_results = search_fda(keyword)
            if st.session_state.search_results.empty:
                st.info('没有找到匹配的有效记录。未添加数据，不推断该产品不存在。')
        except ValueError as error:
            st.error(str(error))
    results = st.session_state.search_results
    if not results.empty:
        st.dataframe(results, hide_index=True, width='stretch', column_config={'来源URL': st.column_config.LinkColumn('来源URL')})
        if st.button('将这批检索结果加入当前会话'):
            try:
                add(results)
            except ValueError as error:
                st.error(str(error))

records = st.session_state.records
left, right, third = st.columns(3)
category = left.selectbox('筛选产品类别', ['全部', *sorted(v for v in records['产品类别'].unique() if v)])
mode = right.selectbox('筛选来源方式', ['全部', *records['来源方式'].unique()])
scene = third.selectbox('筛选应用场景', ['全部', *sorted(v for v in records['应用场景'].unique() if v)])
filtered = records
if category != '全部':
    filtered = filtered[filtered['产品类别'] == category]
if mode != '全部':
    filtered = filtered[filtered['来源方式'] == mode]
if scene != '全部':
    filtered = filtered[filtered['应用场景'] == scene]
st.caption(f'当前显示 {len(filtered)} / {len(records)} 条；摘要统计按当前筛选计算。')
a, b, c = st.columns(3)
a.metric('公开资料（待核）', int((filtered['数据性质'] != '虚构演示').sum()))
b.metric('虚构示例', int((filtered['数据性质'] == '虚构演示').sum()))
c.metric('公开来源数', filtered.loc[filtered['数据性质'] != '虚构演示', '来源URL'].nunique())
st.dataframe(filtered, hide_index=True, width='stretch', column_config={'来源URL': st.column_config.LinkColumn('来源URL')})
if filtered.empty:
    st.info('没有符合当前筛选条件的资料，请选择“全部”。')
st.download_button('导出当前筛选结果 CSV', csv_bytes(filtered), 'pathointel_public_evidence.csv', 'text/csv', disabled=filtered.empty)
with st.expander('每周竞品资料简报｜基础模板'):
    report = brief(filtered)
    st.text(report)
    st.download_button('下载简报草稿 TXT', report.encode('utf-8-sig'), 'pathointel_weekly_brief.txt', 'text/plain')
if st.button('清空本会话，恢复 3 条虚构示例'):
    st.session_state.records = demo_rows()
    st.session_state.search_results = pd.DataFrame(columns=COLUMNS)
    st.rerun()
