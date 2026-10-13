# ChatGPT 网页、桌面和手机接入

本地安装完成后，可在支持本地 stdio 的 AI 客户端直接接入。网页版和手机端需要一个它们能调用的远端连接，源码下载本身不会自动安装到你的 ChatGPT 账户。

账户级配置依赖该账户实际提供的自定义 MCP / 私人隧道入口。先检查入口是否可用；未验证所有账户、套餐、地区和手机版本。官方说明：[自定义 MCP](https://developers.openai.com/api/docs/guides/custom-mcp-server)、[安全隧道](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)、[插件使用范围](https://learn.chatgpt.com/docs/plugins)。

## 私人隧道路径

1. 在 OpenAI 平台的 Tunnels 设置创建关联自己 ChatGPT 工作区的隧道。
2. 创建 Restricted 运行密钥，只选 Tunnels Read + Use。按官方说明保存在私有文件，避免聊天、命令参数、源码或日志中出现明文。
3. 从 [OpenAI 官方发布页](https://github.com/openai/tunnel-client/releases) 取得对应操作系统客户端，验证提供的校验和。
4. 用自己安装的 `weibo-research serve` 作为 MCP command。参考 `examples/tunnel.yaml.example` 替换所有占位符；此配置不含现成 ID 或密钥。运行官方客户端的 `doctor` 和 `run`，核对 ready 状态。
5. 在自己 ChatGPT 的插件设置选择 Tunnel、填写自己的 Tunnel ID，再创建并连接插件。此路径中 No authentication 仅表示本地只读 MCP 无额外认证；访问受到私人隧道所属工作区约束。不要把无认证服务暴露成公共网络端点。
6. 开一个新对话，明确选择此插件，搜索少量关键词并确认返回原帖链接；再测试自然语言自动选择工具。最后在同一账户的手机端验证。模型不一定每次都自动选择正确插件，可以使用 @ 或明确说“用微博研究工具”。

电脑必须开机、联网、保持可工作状态，隧道进程也必须运行。官方隧道不承担你的服务托管；关机或睡眠时查询可能不可用。各操作系统的自动启动方式需要分别设置，当前公开包没有安装后台服务或修改账号权限的脚本。

## 使用边界

示例仅是部署配置，不包含任何人的账户绑定。多个客户需要各自的账号授权和资料库隔离；不得把个人服务作为无认证公共多用户服务分享。本项目还没有多租户 SaaS、用户注册、收费额度或高可用部署。不要为安装工具索取客户的 ChatGPT 密码或个人微博 Cookie。
