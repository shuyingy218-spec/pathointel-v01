"""A source-first pathology product research desk for public information."""
from html import escape
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

from dossier import (
    FIELDS,
    ITEMS,
    add_evidence,
    comparison_brief,
    dossier_brief,
    import_evidence_csv,
    profile_table,
    seed_evidence,
    weekly_dossier_brief,
)
from intel import COLUMNS, csv_bytes, demo_rows, search_fda, today
from official_search import official_vendor, search_official

st.set_page_config(page_title="PathoIntel｜病理产品竞争情报", layout="wide")
st.markdown(
    """
    <style>
    .block-container {max-width: 1120px; padding-top: 1.8rem; padding-bottom: 4rem;}
    h1, h2, h3 {letter-spacing: -.02em;}
    [data-testid="stMetric"] {border: 1px solid #dce5ef; border-radius: 12px; padding: .7rem 1rem;}
    [data-testid="stAlert"] {border-radius: 12px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.session_state.setdefault("dossier_records", seed_evidence())
st.session_state.setdefault("website_results", [])
st.session_state.setdefault("search_error", "")
st.session_state.setdefault("website_query", "")
st.session_state.setdefault("fda_results", pd.DataFrame(columns=COLUMNS))
for field in ("ev_vendor", "ev_product", "ev_url"):
    st.session_state.setdefault(field, "")

line = st.sidebar.text_input("研究产品线", "EBER/CISH", max_chars=80).strip()
st.sidebar.caption("比较基准：达科为")
st.sidebar.info("本版不自动保存。录入后请下载证据 CSV；下次打开网页时导入恢复。")
if not line:
    st.info("请先在左侧填写研究产品线。")
    st.stop()

evidence = st.session_state.dossier_records
scoped = evidence[evidence["产品线"] == line]
profiles = profile_table(evidence, line)

st.title("PathoIntel")
st.caption("病理产品公开资料工作台 · 搜官网 → 核对原文 → 保存证据 → 对比 → 出简报")
st.info("当前使用无密钥网页搜索，可能受搜索源限流影响。搜索摘要只是线索；产品事实须打开原文核对。")
notice = st.session_state.pop("flash_notice", "")
if notice:
    st.success(notice)

m1, m2, m3 = st.columns(3)
m1.metric("已收录厂商", scoped["厂商"].nunique())
m2.metric("产品／设备卡", len(profiles))
m3.metric("本会话人工核对", len(scoped[scoped["证据状态"] == "已人工核对原文"]))

search_tab, product_tab, brief_tab = st.tabs(["① 找官网并录入", "② 产品与达科为对比", "③ 周报与备份"])

with search_tab:
    st.subheader("查找公开官网资料")
    st.caption("可输入任意厂商、产品或型号；结果中的“官网身份待核”需要你打开原网页确认。")
    with st.form("web-search"):
        query = st.text_input("产品／厂商关键词", "EBER", max_chars=80)
        domain = st.text_input("限定官网域名（可选）", placeholder="例如 diagnostics.roche.com", max_chars=200)
        search_clicked = st.form_submit_button("搜索官网结果", type="primary")
    fallback_query = query.strip() + (f" site:{domain.strip()}" if domain.strip() else " 病理 产品 官网")
    st.link_button("在搜索引擎核对更多结果 ↗", "https://www.bing.com/search?q=" + quote_plus(fallback_query))

    if search_clicked:
        st.session_state.website_results = []
        st.session_state.search_error = ""
        try:
            with st.spinner("正在检索公开网页…"):
                st.session_state.website_results = search_official(query, domain)
            st.session_state.website_query = query.strip()
        except ValueError as error:
            st.session_state.search_error = str(error)

    if st.session_state.search_error:
        st.error(st.session_state.search_error)
    elif st.session_state.website_results:
        st.success(f"找到 {len(st.session_state.website_results)} 条候选网页 · 检索日期 {today()}")
        for index, result in enumerate(st.session_state.website_results):
            with st.container(border=True):
                st.markdown(f"**{escape(result['页面标题'] or result['链接'])}**")
                st.caption(f"{result['网站域名']} · {result['来源核验']}")
                if result["搜索摘要（待核）"]:
                    st.write(result["搜索摘要（待核）"])
                link_col, use_col = st.columns(2)
                link_col.link_button("打开官网原文 ↗", result["链接"])
                if use_col.button("用此来源录入", key=f"use-source-{index}"):
                    st.session_state.ev_vendor = official_vendor(result["链接"]) or ""
                    st.session_state.ev_product = ""
                    st.session_state.ev_url = result["链接"]
                    st.rerun()
    else:
        st.caption("输入关键词后搜索。没有返回结果时，不推断产品不存在。")

    st.divider()
    st.subheader("核对原文后记录一条产品事实")
    st.caption("请填写具体试剂或设备型号。每条证据只记录一个字段；价格写明地区、货币、单位、日期和口径，备案写明证号及辖区。")
    with st.form("evidence-form", clear_on_submit=False):
        vendor = st.text_input("厂商 *", key="ev_vendor", max_chars=200)
        product = st.text_input("试剂／设备名称和型号 *", key="ev_product", max_chars=200)
        item = st.selectbox("信息项目", ITEMS)
        content = st.text_area("原文支持的具体事实 *", max_chars=2000)
        source_url = st.text_input("原文链接 *", key="ev_url", max_chars=2000)
        source_note = st.text_input("地区／版本／页码等说明", max_chars=500)
        reviewed = st.checkbox("我已打开并核对原文；这条事实不是从搜索摘要推断的")
        save_clicked = st.form_submit_button("保存到产品证据卡", type="primary")
    if save_clicked:
        if not reviewed:
            st.error("请先核对原文并勾选确认。")
        else:
            try:
                before = len(st.session_state.dossier_records)
                st.session_state.dossier_records = add_evidence(
                    st.session_state.dossier_records,
                    {
                        "产品线": line,
                        "厂商": vendor,
                        "产品名称": product,
                        "信息项目": item,
                        "内容": content,
                        "来源URL": source_url,
                        "来源说明": source_note,
                    },
                    reviewed=True,
                )
                added = len(st.session_state.dossier_records) - before
                st.session_state.flash_notice = (
                    "已加入当前会话。请在“周报与备份”下载证据 CSV。"
                    if added else "这条证据已存在，未重复添加。"
                )
                st.rerun()
            except ValueError as error:
                st.error(str(error))

with product_tab:
    st.subheader(f"{line} 产品与设备")
    st.caption("预置资料为带链接的厂商公开表述；未核实的价格、备案或兼容性明确留空。")
    evidence = st.session_state.dossier_records
    scoped = evidence[evidence["产品线"] == line]
    profiles = profile_table(evidence, line)
    if profiles.empty:
        st.info("当前产品线尚无证据。请先在“找官网并录入”保存一条事实。")
    else:
        st.dataframe(
            profiles[["厂商", "产品名称", "来源数"]],
            hide_index=True,
            width="stretch",
        )
        card_index = st.selectbox(
            "查看产品证据卡",
            range(len(profiles)),
            format_func=lambda i: f"{profiles.iloc[i]['厂商']}｜{profiles.iloc[i]['产品名称']}",
        )
        selected = profiles.iloc[card_index]
        card_facts = scoped[
            (scoped["厂商"] == selected["厂商"])
            & (scoped["产品名称"] == selected["产品名称"])
        ]
        for item_name in ITEMS:
            matches = card_facts[card_facts["信息项目"] == item_name]
            with st.container(border=True):
                st.markdown(f"**{item_name}**")
                if matches.empty:
                    st.caption("未公开／待人工核验")
                else:
                    for fact_index, (_, fact) in enumerate(matches.iterrows(), 1):
                        st.write(fact["内容"])
                        st.caption(f"{fact['证据状态']} · 获取 {fact['获取日期']} · {fact['来源说明']}")
                        st.link_button(f"查看本项原文 {fact_index} ↗", fact["来源URL"])

        st.divider()
        st.subheader("达科为与竞品逐项对照")
        rivals = sorted(v for v in scoped["厂商"].unique() if v != "达科为")
        if not rivals:
            st.info("请先录入竞品证据。")
        else:
            rival = st.selectbox("对比厂商", rivals)
            for item_name in ITEMS:
                with st.expander(item_name, expanded=item_name in ("目标试剂", "配套自动化设备")):
                    left, right = st.columns(2)
                    for column, name in ((left, "达科为"), (right, rival)):
                        column.markdown(f"**{name}**")
                        matches = scoped[
                            (scoped["厂商"] == name)
                            & (scoped["信息项目"] == item_name)
                        ]
                        if matches.empty:
                            column.caption("未公开／待人工核验")
                        else:
                            for _, fact in matches.iterrows():
                                column.write(f"{fact['产品名称']}：{fact['内容']}")
                                column.caption(f"{fact['证据状态']} · {fact['来源URL']}")
            st.caption("并列展示来源内容；不同产品型号、地区及版本不能直接据此判定优劣。")
            comparison = comparison_brief(evidence, line, rival)
            st.download_button(
                "下载达科为对比简报 TXT",
                comparison.encode("utf-8-sig"),
                "pathointel_comparison.txt",
                "text/plain",
            )

with brief_tab:
    evidence = st.session_state.dossier_records
    st.subheader("本周竞品资料简报")
    st.caption("只把本周新增、且你已核对原文的记录算作新增；预置资料不冒充本周新闻。")
    weekly = weekly_dossier_brief(evidence, line)
    st.text(weekly)
    st.download_button(
        "下载本周简报 TXT",
        weekly.encode("utf-8-sig"),
        "pathointel_weekly_brief.txt",
        "text/plain",
    )

    st.divider()
    st.subheader("备份与恢复")
    st.warning("本版没有数据库。新增记录只在当前会话里；离开前下载 CSV，下次打开网页后在这里导入。")
    st.download_button(
        "下载全部产品线证据 CSV",
        csv_bytes(evidence.reindex(columns=FIELDS)),
        "pathointel_all_evidence.csv",
        "text/csv",
        type="primary",
    )
    restored_file = st.file_uploader(
        "导入此前下载的证据 CSV（最多 1 MB）",
        type=["csv"],
        max_upload_size=1,
        key="restore-evidence",
    )
    if st.button("恢复证据", disabled=restored_file is None):
        try:
            st.session_state.dossier_records, count = import_evidence_csv(
                st.session_state.dossier_records, restored_file.getvalue()
            )
            st.session_state.flash_notice = f"恢复 {count} 条新证据；重复记录已跳过。"
            st.rerun()
        except ValueError as error:
            st.error(str(error))
    with st.expander("查看完整产品线资料汇编"):
        st.text(dossier_brief(st.session_state.dossier_records, line))
    with st.expander("查看全部证据与来源"):
        st.dataframe(
            st.session_state.dossier_records[
                st.session_state.dossier_records["产品线"] == line
            ],
            hide_index=True,
            width="stretch",
            column_config={"来源URL": st.column_config.LinkColumn("打开原文")},
        )

    with st.expander("附加工具：虚构通用示例与美国 FDA 510(k)"):
        st.caption("以下三个通用产品均为虚构演示。FDA 510(k) 只覆盖美国该类记录，不能代替中国注册备案查询。")
        st.dataframe(demo_rows(), hide_index=True, width="stretch")
        st.download_button(
            "下载通用示例 CSV", csv_bytes(demo_rows()), "pathointel_demo.csv", "text/csv"
        )
        with st.form("fda-search"):
            fda_keyword = st.text_input("英文 FDA 产品／厂商关键词", "microscope", max_chars=80)
            fda_clicked = st.form_submit_button("查询 FDA 510(k)")
        if fda_clicked:
            try:
                st.session_state.fda_results = search_fda(fda_keyword)
            except ValueError as error:
                st.error(str(error))
        if not st.session_state.fda_results.empty:
            st.dataframe(
                st.session_state.fda_results,
                hide_index=True,
                width="stretch",
                column_config={"来源URL": st.column_config.LinkColumn("来源")},
            )
