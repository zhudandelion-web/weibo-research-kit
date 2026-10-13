# Weibo Research Kit · 微博研究工具包

Guest-only Weibo MCP tools with a private, traceable research archive. **免费开源 · Alpha 0.1.0a1.**

[![tests](https://github.com/zhudandelion-web/weibo-research-kit/actions/workflows/tests.yml/badge.svg)](https://github.com/zhudandelion-web/weibo-research-kit/actions/workflows/tests.yml)

帮助研究者在 AI 对话中检索公开微博、保留原帖链接，并追溯材料是在何时、因什么查询被采集。适合记者取材、品牌讨论研究、公开账号资料整理。下载和本地使用免费；本项目没有注册收费、付费解锁或托管订阅。AI 客户端和自行部署所需的第三方账户由使用者自行选择。

[English guide](docs/QUICKSTART_EN.md) · [ChatGPT 网页及手机接入](docs/CHATGPT.md) · [研究模板](docs/WORKFLOWS.md) · [同类项目](docs/COMPARISON.md)

本项目在 [qinyuanpei/mcp-server-weibo](https://github.com/qinyuanpei/mcp-server-weibo) 的访客采集能力上增加研究记录、历史快照、本地检索与导出。底层作者保留原有署名。它是独立研究工具，与微博及 OpenAI 无官方关联。

## 适合什么任务

在 AI 对话里按关键词找公开微博、核对账号、读取动态样本和热搜，并在之后的对话中继续检索已经保存的材料。每次查询带采集时间、批次、状态及 HTTP 状态摘要。同一微博被重复采集时保留各批次快照，方便追溯正文和查询来源。

基础采集、MCP 和 SQLite 本身都有现有实现。本项目的重点是明确证据边界和可复现的研究记录，不声称采集能力领先。

## 安装

要求 Python 3.11+。可从 [Releases](https://github.com/zhudandelion-web/weibo-research-kit/releases) 下载源码和安装包，也可取得源码：

```sh
git clone https://github.com/zhudandelion-web/weibo-research-kit.git
cd weibo-research-kit
```

随后在项目目录运行：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/weibo-research doctor
```

Windows 用 `py -3 -m venv .venv`，其后把 `.venv/bin/python` 和 `.venv/bin/weibo-research` 换成 `.venv\Scripts\python.exe` 和 `.venv\Scripts\weibo-research.exe`。项目尚未发布到 PyPI，不能直接按包名安装；当前安装入口是源码目录或下载的 wheel。wheel 下载后可执行 `python -m pip install ./weibo_research_kit-0.1.0a1-py3-none-any.whl`；运行工具仍需安装其第三方依赖。

`doctor` 默认只检查本机依赖和资料库，会创建空资料库；`doctor --live` 另查询两条热搜，可能受微博访客访问限制。第三方依赖固定到已经测试的版本。

## MCP：让 AI 调用

把 `examples/mcp.json` 的程序位置替换成安装后的 **绝对路径**，在支持 stdio MCP 的客户端导入。程序启动命令为：

```sh
.venv/bin/weibo-research serve
```

7 个工具：`search_content`、`search_users`、`get_profile`、`get_feeds`、`get_trendings`、`get_comments`、`search_saved_weibo`。UID 和帖子 ID 用十进制字符串，避免长数字精度损失；网络样本最多 30 条，起始页最多 5。客户之间不能共用同一运行器和资料库。当前版本只提供 stdio，没有公共多用户 HTTP 服务。

## 本地采集、检索与导出

```sh
.venv/bin/weibo-research collect --keyword "人工智能" --limit 5
.venv/bin/weibo-research search-saved "人工智能"
.venv/bin/weibo-research search-saved "芯片" --uid 1749127163
.venv/bin/weibo-research stats
.venv/bin/weibo-research export evidence.jsonl
.venv/bin/weibo-research export evidence.csv --format csv
```

指定采集输出中的 `run_id` 可还原当时的帖子快照：

```sh
.venv/bin/weibo-research search-saved "人工智能" --run-id YOUR_RUN_ID
.venv/bin/weibo-research export run.jsonl --run-id YOUR_RUN_ID
```

导出不会覆盖同名文件。JSONL 保留原文及字符串 ID；CSV 为防止公式执行和长 ID 被电子表格改写，在相关单元格前添加单引号。CSV 的显示文本因此可能与原文不同，需要精确复用请用 JSONL。

## 保存与隐私

资料库默认位于操作系统的当前用户数据目录，可用 `WEIBO_RESEARCH_DATA_DIR` 或 `--data-dir` 自选根目录。`--profile brand-a` 建立独立资料库，profile 只是本地分类，不能替代用户认证或租户隔离。

```sh
.venv/bin/weibo-research --profile brand-a collect --keyword "咖啡" --limit 5
.venv/bin/weibo-research --no-archive collect --keyword "咖啡" --limit 5
```

默认保存查询词、采集批次、帖子快照和经过精简的 HTTP 状态。`--no-archive` 关闭新的网络结果及状态保存；本地查询仍可读取之前的材料。访客 Cookie 只在内存中，不读取或保存个人微博登录会话。状态摘要不包含 Cookie、请求头、查询字符串或服务器返回的任意消息。POSIX 新建 profile 目录为 700、数据库和导出为 600；Windows 权限继承当前用户目录的 ACL。对现有的宽权限目录请自行限制访问。

MCP 返回给 AI 的资料会进入该客户端及模型的数据处理路径。存储本身是本地的，不代表所有使用过程都离线。需要清理材料时，先停止客户端/运行器，再删除自己 profile 的资料库；默认不会自动清理历史。

## 结果边界

- `public_sample`：返回公开样本；不代表全部结果、最新排序或完整正文。
- `partial`：返回数据，但本次查询中也出现失败。
- `empty_unconfirmed`：未返回样本，不能证明不存在材料。
- `error`：出现错误，不能据此判断内容存在与否。
- `text_completeness=possibly_truncated`：观察到截断迹象；`unverified` 也不保证完整。
- 所有结果的完整历史和完整正文均未验证。不要据小样本推断全平台观点或总体情绪。

请求之间至少间隔 1.5 秒，单次查询总时限 60 秒；底层按其既有逻辑处理部分瞬时失败。微博可能限流、更改接口或要求登录。本项目会报告不确定性，不提供登录绕过、验证码破解或“永不封禁”保证。公开可见也不等于获得任意再分发内容的权利。

## 开发验证

```sh
.venv/bin/python -m unittest discover -s tests -v
```

自动测试不访问真实微博。实际网络检查需用户主动执行 `doctor --live`，不能用某次检查代替长期可用性承诺。已添加跨系统 CI 配置，发布前需查看真实 CI 结果。

## 许可

MIT；底层版权和完整许可证见 `licenses/mcp-server-weibo-MIT.txt` 和 `NOTICE`。项目不包含任何用户凭据、账号绑定、私人隧道配置或预采集数据库。

## 反馈和维护

遇到安装失败或结果异常，请到 [Issues](https://github.com/zhudandelion-web/weibo-research-kit/issues) 按模板提交操作系统、Python版本、操作步骤和经过脱敏的状态；不要上传密码、Cookie、运行密钥或你的资料库。欢迎补充真实研究场景，见 [贡献说明](CONTRIBUTING.md)。

项目提供自动测试、依赖更新提议和每周访客可用性检查。维护策略和已验证范围见 [维护说明](docs/MAINTENANCE.md)。测试版不承诺响应时限或持续可用性；遇到接口变更会先确认原因再调整。
