# Douyin Comment Insight

将抖音账号的公开一级评论整理为可审计的需求洞察与静态 HTML 报告。项目既可作为 Codex Skill 使用，也可直接运行 Python 脚本。

[![Tests](https://github.com/whwhw/douyin-comment-insight/actions/workflows/test.yml/badge.svg)](https://github.com/whwhw/douyin-comment-insight/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-72e6d0.svg)](LICENSE)

> 本项目不是抖音或 TikHub 官方产品。使用者需要自行确认数据来源、账号权限、平台条款及当地法律要求。

## 能做什么

- 通过 TikHub 采集账号资料、最近作品和一级评论
- 标注高价值提问、明确需求和风险反馈
- 要求每条观点与机会绑定真实评论 ID
- 生成可搜索的静态报告库
- 使用固定 HTML 模板渲染报告，分析数据不会改变页面结构和样式
- 将远程头像保存为本地资源，避免抖音 CDN 防盗链导致头像失效
- 重跑同一账号时覆盖旧报告，避免重复卡片
- 使用脱敏 Demo 离线验证完整的分析与发布链路

## 环境要求

- Python 3.10+
- 在线采集需要 TikHub API Key

## 快速开始

### 1. 注册 TikHub 并获取 API Key

在线采集依赖 TikHub。首次使用请完成以下操作：

1. 打开 [TikHub 注册页面](https://user.tikhub.io/register) 创建账号。
2. 打开注册邮箱中的验证邮件，完成邮箱验证。
3. 登录后进入 [API Key 控制台](https://user.tikhub.io/dashboard/api)。
4. 点击创建 API Key，并立即复制到安全位置。TikHub 创建后的完整 Key 只显示一次，请勿提交到 GitHub、截图或发送给他人。
5. 如果免费额度不足，在 TikHub 控制台查看接口价格并按需充值。

TikHub 官方说明：[Getting Started](https://tikhub.io/getting-started) · [API 文档](https://docs.tikhub.io/)

### 2. 下载并安装项目

```bash
git clone https://github.com/whwhw/douyin-comment-insight.git
cd douyin-comment-insight
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

### 3. 配置 API Key

打开项目根目录中的 `.env`，填写刚才复制的 Key：

```dotenv
TIKHUB_API_KEY=your_api_key
TIKHUB_BASE_URL=https://api.tikhub.dev
```

- 中国大陆：使用 `https://api.tikhub.dev`，通常无需代理。
- 其他地区：建议改为 `https://api.tikhub.io`。
- `.env` 已加入 `.gitignore`，请勿将真实 Key 写进 `.env.example`。

检查配置文件是否就绪：

```bash
test -f .env && echo ".env 已创建"
```

程序不会显示 Key 内容；首次采集若提示 `TIKHUB_API_KEY 未配置`，请重新检查 `.env` 中的变量名和值。

### 4. 采集账号并生成分析输入

采集一个账号：

```bash
python3 scripts/workflow.py inspect --account <抖音号>
python3 scripts/workflow.py prepare --account <抖音号> --works 20 --comments 100
```

`prepare` 会输出 `analysisInput`、`findings` 和 `finalAnalysis` 路径。按照 [分析格式](references/analysis-schema.md) 填写 `findings.json` 后执行：

```bash
python3 scripts/finalize_analysis.py \
  --input <analysisInput> \
  --findings <findings> \
  --output <finalAnalysis>
python3 scripts/publish_report.py --account <抖音号> --data <finalAnalysis>
python3 scripts/validate_package.py --account <抖音号>
```

## 离线体验

离线 Demo 使用虚构账号和评论，不访问网络：

```bash
python3 scripts/demo.py
```

报告会生成到 `workspace/site/`。用浏览器打开 `workspace/site/comment-insight-index.html`。

报告详情页固定包含账号信息、核心结论、评论类型分层、高赞评论排行、用户需求画像、机会建议和评论证据。模板位于 `assets/templates/`，发布器只注入分析参数。

## 安装为 Codex Skill（原运行方式）

```bash
python3 install.py
```

然后编辑 `~/.codex/skills/douyin-comment-insight/.env`。更新已有安装时使用 `python3 install.py --upgrade`。

## 安装为 TRAE Skill

在 TRAE 的 Skills 管理入口导入 `skills/douyin-comment-insight/`，或直接导入本目录。启用后由 TRAE 调用机制加载 `SKILL.md`；将 `TIKHUB_API_KEY` 和 `TIKHUB_BASE_URL` 配置在 TRAE 敏感变量或项目外私密配置中，禁止写入仓库。

## 数据与隐私

- `.env`、`workspace/`、运行原文和生成报告默认不会进入 Git。
- 原始响应可能包含公开用户标识及评论内容，请按敏感数据管理。
- 发布 HTML 前应确认你有权展示其中内容；公开部署时建议自行增加匿名化步骤。
- API Key 只从环境变量或本地 `.env` 读取。

## 开发

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
```

欢迎提交 Issue 和 Pull Request。安全问题请参考 [SECURITY.md](SECURITY.md)。

## License

[MIT](LICENSE)
