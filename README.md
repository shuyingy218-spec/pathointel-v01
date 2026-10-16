# PathoIntel v0.5

[公开网页](https://pathointel-v01.streamlit.app/) · 病理产品公开资料检索、逐项证据、达科为对比和每周简报。

## 先完成一条调研流程

1. 在“找官网并录入”输入产品、型号或厂商；也可限定官网域名。网页内无密钥检索会返回候选页面，搜索源限流时明确报错。搜索摘要不能直接写成产品事实。
2. 打开原文，核对具体试剂或设备型号，再逐条填写组成、技术特点、产品布局、价格、备案等字段。没有来源支持的字段保留“未公开／待人工核验”。
3. 在“产品与达科为对比”查看产品卡和逐项来源，选择竞品厂商并下载对比简报。
4. 在“周报与备份”下载本周简报和**全部产品线证据 Excel（.xlsx）**；CSV 仍可选。下次打开网页时导入 Excel 或 CSV 恢复。预置资料不计入本周新增。

网页不会自动保存编辑内容：当前会话关闭、断开或服务重启可能清空新增记录。每次录入后请下载证据 Excel 或 CSV。请勿输入患者、个人或内部敏感信息。

## 范围

- 预置 EBER/CISH 资料来自列出的厂商产品页或说明书，记录厂商表述和未核实项；设备页面本身不能证明特定试剂货号兼容。
- 附加工具保留 3 条明确标为虚构的通用产品示例和美国 FDA 510(k) 查询。FDA 510(k) 不等于中国注册备案，也不覆盖全部医疗器械。
- 网页内搜索使用 [ddgs](https://github.com/deedy5/ddgs)，无需搜索 API 密钥；云端网络或搜索源限流会使结果不可用。此时可以通过网页上的外部搜索入口查看候选，再手动录入经核对的原文链接。无结果不代表产品不存在。
- 当前不接 n8n、AI API、付费搜索接口或持久数据库。

## 本地运行与验证

```text
git clone https://github.com/shuyingy218-spec/pathointel-v01.git
cd pathointel-v01
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
python -m unittest discover -p "test_*.py"
python test_intel.py
```

依赖版本在 `requirements.txt` 固定。网页部署使用 Streamlit Community Cloud，推送至 GitHub 后自动更新。

## 研究方法

[PathoIntel Product Research](skills/pathointel-product-research/SKILL.md) 规定逐项来源、试剂和设备型号、价格与注册证据、达科为对比和导出验收。它参考 [Anthropic competitive-brief](https://github.com/anthropics/knowledge-work-plugins/blob/main/product-management/skills/competitive-brief/SKILL.md) 与 [K-Dense market-research-reports](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/market-research-reports/SKILL.md) 的方法；这些 skill 本身不提供网页搜索服务。
