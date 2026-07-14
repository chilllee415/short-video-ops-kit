# 04a 参考内容研究计划工作流

## 目的

在下载爆款之前，先根据账号定位、阶段策略、当前选题意图和待优化文案，判断这一轮到底该查什么。

这个工作流只产出研究计划，不下载视频、不转写正文、不拆解策略。它的作用是把“我要做教学转化类内容”翻译成平台、关键词、样本类型、入选规则和排除规则。

## 输入

- `config/profile/account.profile.json`
- `data/operations/current/account-snapshot.json`
- `data/topic-research/current/pain-bank.json`
- `data/benchmarks/current/reference-bank.json`
- `config/strategy/strategy-brief.json`
- 可选：当前待优化文案
- 可选：上一轮 `reference-strategy-deconstruction.json`

## 输出

```text
runs/<run-id>/outputs/reference-research-plan.json
runs/<run-id>/outputs/reference-research-plan.md
runs/<run-id>/run.manifest.json
```

## 执行命令

```bash
python3 system/scripts/generate_reference_research_plan.py \
  /path/to/client-workspace \
  --run-id <date>-reference-research-plan \
  --current-draft "当前待优化文案" \
  --sample-youtube 1 \
  --sample-bilibili 1 \
  --sample-douyin 1
```

## 研究计划字段

```text
stage_direction：当前阶段方向
content_scene：本轮内容场景
research_questions：这轮要验证的问题
platform_mix：平台配比
query_groups：各平台关键词
sample_targets：目标样本数量
inclusion_rules：入选规则
exclusion_rules：排除规则
transcript_policy：正文获取要求
downstream_workflow：下一步交给哪个工作流
```

## 当前案例判断

用户文案：

```text
最近几条视频数据还不错，很多粉丝问有什么技巧策略。
我不太懂运营，但我比较懂 AI。
账号定位、选题、文案、视频生成，基本都是用 Codex 帮我做的。
```

这不是单纯“AI 基础教学”，更准确的场景是：

```text
AI 内容生产工作流复盘 + AI 教学转化 + 知识星球承接
```

因此本轮对标不应该只搜 `AI 教程`，而要分四类查：

| 类型 | 目的 | 关键词方向 |
| --- | --- | --- |
| 结果复盘类 | 学开头如何用数据建立可信度 | AI workflow results, AI 内容生产 数据, 账号复盘 |
| 工作流展示类 | 学如何把复杂系统讲成几个模块 | Codex workflow, AI agent workflow, AI 自动化工作流 |
| 教学转化类 | 学概念如何接到课程/社群/资料 | AI 教学 知识星球, AI 课程 引流, ChatGPT 教程 资料 |
| 竞品爆款类 | 学短视频钩子和节奏 | AI 自媒体 工作流, AI agent 帮我做视频, AI 选题 文案 |

## 入选规则

优先选择：

- 开头 3 秒有结果、反差、强承诺或可见画面。
- 正文能拿到逐字稿，且不少于 120 字。
- 内容里有流程、系统、工作台、模板、数据、案例或 CTA。
- 能映射到当前策略：Codex 提效、内容生产系统、知识星球承接。

排除：

- 只有标题和简介，没有口播正文。
- 主要卖暴富、副业、月入承诺。
- 纯工具安装教程，无法迁移到账号策略。
- 只讲概念，没有流程或证明。

## 下游交接

研究计划确认后交给 04b：

```bash
python3 system/scripts/download_reference_transcripts.py \
  /path/to/client-workspace \
  --run-id <date>-reference-transcript-download \
  --plan-run-id <date>-reference-research-plan \
  --download-douyin-video \
  --transcribe-missing
```

下载完成后交给 04c 策略拆解，再交给 05 生成自己的选题池。
