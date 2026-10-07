---
name: douyin-comment-insight
description: Analyze real Douyin account comments, detect existing account history, decide whether to create or refresh a report, and publish a searchable static report library. Use when the user asks to analyze, update, rerun, inspect, or open a Douyin account comment report, including prompts such as “使用抖音评论分析技能，分析 xxxx 账号的数据并生成报告”.
---

# 抖音评论分析

始终使用真实采集数据。不得虚构昵称、头像、评论、观点、用户需求或商业机会。

原运行方式：安装包解压后可运行 `python3 install.py` 安装到 `~/.codex/skills/douyin-comment-insight`，然后编辑安装目录中的 `.env`。该方式保留用于兼容原环境，不是 TRAE 的安装路径。

TRAE 运行方式：将本目录作为独立用户 Skill 导入 TRAE 的 Skills 管理入口；API 配置从 TRAE 敏感变量或项目外私密配置读取，不要写入仓库。

## 执行流程

1. 在本 Skill 目录运行账号检查：

   `python3 scripts/workflow.py inspect --account <抖音号>`

2. 根据检查结果执行：

   - `new`：新增账号分析。
   - `update`：已有历史报告，重新采集并覆盖同账号报告。
   - 用户只要求“查看”时不要采集，直接返回检查结果中的详情页路径。

3. 采集并生成分析输入：

   `python3 scripts/workflow.py prepare --account <抖音号> --mode auto`

   可追加 `--works 20 --comments 100`。读取命令输出中的 `analysisInput`、`findings` 和 `finalAnalysis` 路径。

4. 完整读取 `analysisInput`。依据原始评论填写 `findings.json`，字段约定见 `references/analysis-schema.md`。所有观点和机会必须引用真实 `commentId`。

5. 合并并校验分析：

   `python3 scripts/finalize_analysis.py --input <analysisInput> --findings <findings> --output <finalAnalysis>`

6. 发布详情页并更新列表索引：

   `python3 scripts/publish_report.py --account <抖音号> --data <finalAnalysis>`

7. 运行验证：

   `python3 scripts/validate_package.py --account <抖音号>`

8. 向用户说明这是新增还是更新，报告评论数、执行时间、列表页和详情页路径。

## 默认规则

- 默认最近 20 条作品，每条作品最多 100 条一级评论。
- 已存在账号默认执行 `update`；输出文件名保持 `{accountId}.html`，不得创建重复卡片。
- 单账号采集失败不得破坏旧报告或索引。
- 没有评论时状态为 `pending`，不得标记完成。
- API Key 只从 `.env` 或环境变量读取，不写入日志、JSON 或 HTML。
- 用户明确要求复用历史数据时，使用 `prepare --mode reuse`，不得请求网络。

TikHub 接口见 `references/tikhub-api.md`；页面发布约定见 `references/report-rendering.md`。
