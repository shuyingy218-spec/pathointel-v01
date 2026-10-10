# PathoIntel v0.2

[公开演示网页](https://pathointel-v01.streamlit.app/) · 通用医疗产品竞争情报最小工作台。

## 使用

初始3条数据均为虚构。展开录入区，手动添加公开资料，或下载CSV模板后导入。产品名称和来源URL必填；获取日期留空时取当天。UTF-8 CSV最多1 MB、500行。新资料一律待核，缺失内容不编造。每条保留来源URL、获取日期、来源方式、核验状态；FDA记录另含编号和决定日期。

展开检索区，输入公开英文产品/厂商关键词（例如 microscope），真实查询美国FDA 510(k)记录，按决定日期排序最多5条，查看来源后加入当前会话。按产品名称、厂商、来源URL和记录编号去重。失败或无结果不添加资料。

表格支持类别、来源方式和应用场景组合筛选、中文CSV导出。统计卡片区分公开资料与虚构示例。简报模板只列出当前筛选中最近7天获取的公开资料，并提供人工填写问题；获取日期不是新闻发生日期，不自动生成商业或医疗结论。

## 范围、依赖和费用

仅覆盖[openFDA Device 510(k)](https://open.fda.gov/apis/device/510k/)，不覆盖中国注册、所有医疗器械或全网新闻。官方文档注明月度更新。真实检索本地和云端均需可连接 api.fda.gov。

本版无密钥调用已实际验证，无新增付费服务、AI API或凭据。[官方无密钥限额](https://open.fda.gov/apis/authentication/)为每IP每分钟240次、每日1000次；云端共享IP可能受限。每次点击一个请求、15秒超时、不自动重试或定时查询。限额和可用性由FDA决定。

## 隐私与限制

**仅输入合法公开资料，禁止内部、患者、个人或其他敏感信息。** 录入/导入内容仅在当前Streamlit会话服务器内存保存，不写数据库、磁盘、全局缓存或GitHub；刷新、断开、重启可能丢失，请及时导出。其他浏览器会话不会看到你的会话资料。查询的公开关键词会发送给FDA。

来源URL未经内容核验，所有结果待核。应用只查询固定FDA接口，不抓取用户填写的URL。CSV导出转义常见Excel公式前缀。监管记录不能直接解释为性能、临床适用性或市场份额。

## 运行与测试

Python 3.12：

    pip install -r requirements.txt
    python test_intel.py
    streamlit run streamlit_app.py

检查覆盖录入/导入、空值和无效链接、筛选/CSV、去重、来源保留、检索成功/无结果/失败、简报、会话隔离和重置。测试夹具均为虚构。

## 发布与回滚

仍使用同一仓库main分支、streamlit_app.py入口、同一Cloud应用。v0.1回滚分支：[v0.1-backup](https://github.com/shuyingy218-spec/pathointel-v01/tree/v0.1-backup)，提交2cee6da79233673851cdadd7f4d8b8bd1187b790。如需回滚，把Cloud部署分支改为v0.1-backup，或恢复该提交的入口文件到main。

沿用[Streamlit官方最小示例](https://github.com/streamlit/streamlit-example)结构。无n8n、AI API、登录、持久数据库或推送。
