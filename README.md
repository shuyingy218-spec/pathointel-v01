# PathoIntel v0.1

通用医疗产品竞争分析的最小 Streamlit 公开演示。

**全部 3 条产品、厂商、价格和特点均为虚构，不代表任何真实医疗产品或医疗建议。** 每行和导出的 CSV 都保留虚构标记。

## 功能

- 仅 3 条虚构产品数据。
- 按产品类别和应用场景筛选表格，两个条件共同生效。
- CSV 导出当前筛选结果；采用 UTF-8 BOM，方便 Excel 显示中文。
- 无匹配结果时显示提示并禁用导出。

## 本地运行

建议 Python 3.12。

```sh
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 部署

将本目录文件放入 GitHub 仓库根目录；当前源码仓库设为私有，部署前需由所有者授权 Streamlit 读取。在 [Streamlit Community Cloud](https://share.streamlit.io/) 登录并选择 Create app，指定仓库、实际分支名称及入口 `streamlit_app.py`，然后 Deploy。必要时由仓库所有者完成 GitHub 授权。部署成功后，使用 Cloud 提供的实际 `.streamlit.app` 地址分享。

## 验收

默认显示 3 行；选择影像设备后显示 1 行；同时选择病房后显示 0 行并禁用导出；恢复全部后显示 3 行。CSV 行数应与筛选表格一致，且包含虚构标记。

## 模板来源与范围

沿用 [Streamlit 官方 streamlit-example](https://github.com/streamlit/streamlit-example) 的 `streamlit_app.py`、`requirements.txt` 和 README 最小结构，使用其 Streamlit + pandas 组合；业务代码为本演示新写，无需原示例的图表依赖。

本版不接 n8n、AI API、真实数据源、数据库或登录系统。
