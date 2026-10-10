import pandas as pd
import streamlit as st

st.set_page_config(page_title="PathoIntel v0.1", layout="wide")
st.title("PathoIntel v0.1")
st.caption("通用医疗产品竞争分析 · 公开演示")
st.warning("以下 3 条产品及全部参数均为虚构，仅用于功能演示，不代表真实厂商、性能、价格或医疗建议。")

products = pd.DataFrame([
    {"产品名称": "示例超声 A（虚构）", "厂商": "示例厂商甲（虚构）", "产品类别": "影像设备", "应用场景": "门诊", "参考价格（万元）": 18, "核心特点": "便携式设计（虚构）", "数据性质": "虚构演示"},
    {"产品名称": "示例监护 B（虚构）", "厂商": "示例厂商乙（虚构）", "产品类别": "监护设备", "应用场景": "病房", "参考价格（万元）": 6, "核心特点": "多参数监测（虚构）", "数据性质": "虚构演示"},
    {"产品名称": "示例检验 C（虚构）", "厂商": "示例厂商丙（虚构）", "产品类别": "检验设备", "应用场景": "检验科", "参考价格（万元）": 25, "核心特点": "小型自动化（虚构）", "数据性质": "虚构演示"},
])

category = st.selectbox("产品类别", ["全部", *products["产品类别"].unique()])
scene = st.selectbox("应用场景", ["全部", *products["应用场景"].unique()])
filtered = products
if category != "全部":
    filtered = filtered[filtered["产品类别"] == category]
if scene != "全部":
    filtered = filtered[filtered["应用场景"] == scene]

st.caption(f"当前显示 {len(filtered)} / {len(products)} 条虚构产品")
st.dataframe(filtered, hide_index=True, width="stretch")
if filtered.empty:
    st.info("没有符合当前筛选条件的产品，请将筛选条件改为“全部”。")
st.download_button(
    "导出当前筛选结果 CSV",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="pathointel_fictional_products.csv",
    mime="text/csv",
    disabled=filtered.empty,
)
