# PathoIntel v0.4

[打开公开演示网页](https://pathointel-v01.streamlit.app/) · 病理产品资料检索、来源整理与达科为竞品对比。

## 功能

- 输入任意产品或厂商名称，点击“在浏览器打开实时搜索结果”，由 Bing 按当前关键词进行联网检索；可选限定厂商官网域名。搜索会在新标签页显示结果。
- 云端也会尝试将搜索结果整理回网页。选择结果可打开原文，并预填来源链接和已识别厂商；核对后逐条录入事实。若云端搜索源暂不可用，可通过 Bing 入口核对后手动填写链接。
- EBER/CISH 初始资料按厂商、目标试剂、配套设备、组成、技术特点、产品布局、价格、注册备案分类，每条保留来源链接。现有来源没有支持的信息标为“未公开／待人工核验”。
- 产品证据卡按“厂商＋具体产品”分开，支持达科为与竞品逐项对照、带来源的对比简报，以及证据 CSV 备份和导入恢复。另有通用资料台账、筛选和 FDA 510(k) 查询。
- 台账中的 3 条通用示例均为虚构。EBER/CISH 产品资料来自列出的厂商网页或说明书，属于厂商表述，须核对地区、版本和兼容性。

## 使用流程

1. 在网页顶部输入 EBER、厂商名称或产品型号，点击“搜索并整理网页结果”。
2. 从搜索结果打开官网原文。选中结果并点击“用这条来源录入产品事实”，网页会预填链接和可识别厂商；也可以手动填写来源。
3. 核对型号和内容后，在同一页面逐项填写事实并勾选原文核对。搜索摘要本身不能当作事实。分别录入达科为和竞品，再查看按具体产品分开的证据卡与横向对比。
4. 下载产品证据 CSV 备份。在新的会话中可从“证据台账与恢复”导入此前备份；对比简报可单独下载。价格请注明地区、日期、单位和口径；备案请注明证号、主体、地区及状态。没有公开凭证时保留待核。

## 范围与限制

浏览器搜索会向 Bing 发送关键词并在新标签页展示实时结果；产品页内的自动结果整理依赖 ddgs 搜索库，可能受 Streamlit 云端网络策略或搜索源限流影响。美国监管查询只覆盖 FDA 510(k)，不代表中国注册备案，也不覆盖所有器械、新闻或市场信息。网页不提供临床建议。

手动录入和导入的数据只保存在当前运行会话内存，不写入仓库或数据库；刷新、断开或服务重启可能清空，请及时导出。不要输入患者、个人或内部敏感信息。

## 可复用研究 skill

[PathoIntel Product Research](skills/pathointel-product-research/SKILL.md) 定义跨产品线复用的官网核对、逐项证据、达科为对比和导出验收流程。它参考 [Anthropic competitive-brief](https://github.com/anthropics/knowledge-work-plugins/blob/main/product-management/skills/competitive-brief/SKILL.md) 与 [K-Dense market-research-reports](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/market-research-reports/SKILL.md) 的方法，网页搜索和表格操作由本仓库代码实现。

## 本地运行

    git clone https://github.com/shuyingy218-spec/pathointel-v01.git
    cd pathointel-v01
    python -m pip install -r requirements.txt
    streamlit run streamlit_app.py

依赖：Streamlit、pandas、ddgs。无需 n8n、AI API 或搜索 API 密钥。
