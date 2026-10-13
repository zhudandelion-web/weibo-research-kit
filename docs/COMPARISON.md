# 同类项目与本项目定位

检查日期：2026-10-13。以下是仓库公开文档对比，未做竞争产品的长期同条件实测；搜索未覆盖所有仓库。

| 项目 | 已公开能力 | 与本项目的关系 |
| --- | --- | --- |
| [qinyuanpei/mcp-server-weibo](https://github.com/qinyuanpei/mcp-server-weibo) | 默认访客模式，内容/用户搜索、动态、热搜、评论；MCP和CLI；可选CLI扫码登录 | 本项目直接依赖它。底层采集能力归功于上游 |
| [Panniantong/mcp-server-weibo](https://github.com/Panniantong/mcp-server-weibo) | 上述项目的fork，提供微博数据及MCP配置 | 属于同一代码家族，不能计作独立技术路线 |
| [RicterZ/mcp-server-weibo](https://github.com/RicterZ/mcp-server-weibo) | 微博MCP；上游注明引用其扫码协议实现 | 本项目不开放扫码登录 |
| [DevinChen2014/weibo-mcp](https://github.com/DevinChen2014/weibo-mcp) | 托管微博MCP、分页评论/回复、用户、转发、视频转写等；API Key认证 | 仓库公开连接文档，业务实现私有；不等于可免费自行运行源码 |
| [tamnd/weibo-cli](https://github.com/tamnd/weibo-cli) | Go CLI、多格式导出、`--db`写库、限速和重试；部分用户功能要求Cookie | SQLite和导出不是本项目独家能力 |
| [bidabrain/weiboX](https://github.com/bidabrain/weiboX) | Android免登录浏览、本地关注和Room缓存，可选Cookie | 面向浏览体验，而非标准MCP研究记录 |

本项目公开的是一个轻量研究层：七个访客工具、明确的空结果和截断状态、采集批次与历史正文快照、本地批次/作者检索、JSONL及保护后的CSV导出、通用安装及独立验证。不能据此声称全市场独家、爬取更深、永不被拦截或比托管竞品更稳定。

发布判断：适合免费alpha，面向需要可追溯材料的AI用户、记者和研究者。先验证别人能否独立安装、持续使用，以及是否需要批次快照。当前不适合定位为成熟商业SaaS。后续优先补外部用户安装证据和持续可用性记录；无需先扩展多平台或收集用户账号登录凭据。
