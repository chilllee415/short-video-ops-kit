# 04 参考拆解与选题复刻工作流

## 目的

选题不要凭空想。先按赛道、方向和策略去拆别人已经验证过的想法，再用自己的定位、概念和角度重新包装。

这里的“复刻”不是抄原文，而是拆解爆款背后的需求、结构和转化逻辑。

## 分层流程

```text
03 Strategy Confirmation
-> 04a Reference Research Plan：判断本轮要查什么
-> 04b Reference Transcript Download：下载爆款和正文/逐字稿
-> 04c Reference Strategy Deconstruction：拆钩子、结构、证明、CTA
-> 04d Reference Bank Ingest：确认长期可复用后写入参考库
-> 05 Weekly Topic Radar：生成自己的选题池
```

`04-reference-mining` 是总入口和长期参考库维护层。临时研究某一类爆款时，优先按 04a/04b/04c 的顺序跑；确认有长期价值的样本，再通过 04d 归档到 `data/benchmarks/current/reference-bank.json`。

## 输入

- `account-snapshot`：账号当前数据和瓶颈。
- `pain-bank`：目标用户的真实痛点和重复动作。
- `strategy-brief`：用户确认过的阶段策略。
- 对标账号或内容链接。
- 赛道关键词。
- 平台来源：抖音、小红书、B站、视频号、YouTube、X 等。

## 用户给抖音爆款链接时的硬规则

当用户给出抖音爆款链接或 aweme_id，并要求参考、拆解、复刻、学习口播策略时，不先走普通网页摘要，也不只看标题。必须先用 TikHub 拉取真实内容：

```bash
python3 system/scripts/download_single_douyin_reference.py \
  /path/to/client-workspace \
  "https://www.douyin.com/video/<aweme_id>" \
  --run-id <date>-douyin-<aweme_id>
```

这个单条链路会按顺序完成：

1. TikHub 获取视频详情和可用字幕/正文。
2. 下载原视频文件。
3. 用 ffmpeg 抽取音频。
4. 字幕缺失或不足时，用 ASR 转写口播。
5. 输出 `runs/<run-id>/outputs/single-douyin-reference.json` 和 `.md`，再基于真实转写拆解钩子、结构、证明方式和 CTA。

默认没有产出可用逐字稿时，脚本会保留诊断输出并以非 0 状态退出，避免把标题/元数据误当成内容拆解。只有明确需要保留 metadata-only 结果时才加 `--allow-metadata-only`。

如果当前环境没有 `TIKHUB_API_KEY`，需要先让用户提供临时 key，或通过 `--env-file` / `--tikhub-api-key-stdin` 传入。密钥不得写入输出文件。

## 拆解维度

| 维度 | 要记录什么 |
| --- | --- |
| 用户痛点 | 这条内容抓住了什么真实麻烦？ |
| 开头钩子 | 它用结果、反常识、恐惧、收益，还是身份代入开场？ |
| 内容结构 | 它是列表、案例、对比、诊断、教程，还是复盘？ |
| 证明方式 | 它靠数据、画面、流程、截图、故事，还是权威背书？ |
| 转化路径 | 它引导关注、评论、私信、领取资料，还是咨询成交？ |
| 可复刻点 | 哪个结构可以迁移到我们的账号？ |
| 必须改写点 | 哪些词、案例、承诺、表达必须换掉？ |

## 复刻公式

```text
对标内容 = 用户痛点 + 钩子结构 + 证明方式 + 转化路径

我们的选题 = 同类痛点 + 新概念包装 + 新场景证据 + 自己的承接方式
```

## 选题包装方法

1. 换角色：从泛用户换成目标客户。
2. 换场景：从工具使用换成业务流程。
3. 换概念：给旧问题一个新名字。
4. 换证据：用自己的数据、截图、案例或流程图。
5. 换 CTA：从“学教程”改成“诊断/模板/陪跑/服务筛选”。

## YouTube 热点挖掘

适合用 YouTube 找英文一手信息，尤其是 Codex、AI coding agent、AI automation、AI app builder 这类更新快、中文区滞后的主题。

如果账号阶段已经从教学转向结果呈现、场景诊断和企业赋能，检索词也必须同步变化。不要继续用 `tutorial`、`beginner guide`、`setup` 作为主入口，否则平台会把教程和大课推到前面。

### 采集顺序

不要只搜一个关键词。每轮信息源至少分三层：

1. **官方/一手来源**：确认产品能力和表述边界，避免二创跑偏。
2. **业务结果/流程案例**：优先看 AI 如何省时间、降成本、改造流程、辅助团队或小老板做决策。
3. **竞品账号/对标频道**：看同赛道创作者怎样包装结果、案例、对比和服务承接。
4. **教学/教程视频**：只作为功能边界和标题结构参考，不作为主选题来源。

输出时先给用户看候选源列表，再决定拆哪几条深拆。候选源进入 `reference-bank` 前，必须能映射到 `pain_id` 和 `strategy_id`。

### 搜索关键词

```text
AI agent business workflow case study
AI automation business results
AI agent automates business operations
AI workflow for small business
Codex real business workflow
AI coding agent real world workflow
AI automation agency client results
AI agents for business operations
AI workflow saves time business
Claude Code vs Codex business workflow
```

### 策略化查询模板

| 策略方向 | 查询模板 |
| --- | --- |
| 成果前置 | `AI automation business results`, `AI workflow saves time business`, `AI agent business case study` |
| 企业赋能 | `AI agents for business operations`, `AI agent automates business operations`, `AI workflow for small business` |
| 场景诊断 | `AI coding agent real world workflow`, `Codex real business workflow`, `AI agent workflow case study` |
| 对比决策 | `Claude Code vs Codex business workflow`, `AI coding agent honest results`, `AI tools for business operations` |
| 服务转化 | `AI automation agency client results`, `AI automation agency workflow`, `automate business with AI` |
| 功能边界 | `Codex product demo`, `OpenAI Codex app`, `Codex release demo` |

### 检索配比

```text
70% 业务结果/企业赋能/流程案例
20% 对比决策/真实测试/竞品结构
10% 官方演示/教程/功能边界
```

教学内容不是不能看，但它只能回答“这个工具能做什么”。真正进入选题池的内容，必须继续回答：

```text
谁会因此省时间、少花钱、少踩坑？
哪个业务动作被 AI 改造了？
我能不能用自己的录屏做出可见结果？
能不能自然引到诊断、模板、陪跑或服务筛选？
```

同样要注意另一种偏差：`AI automation agency`、`sign your first client`、`make money` 这类服务商卖课/签客户内容，适合参考商业包装，不适合作为主选题来源。账号如果面向“有业务、有流程的人”，就要优先拆终端用户的业务改造案例，而不是服务商获客教程。

### 竞品账号配置

每轮可以维护一个频道清单，字段包括：

```text
频道名：
频道链接：
为什么看它：
它的定位：
适合拆的结构：
不能直接抄的点：
```

频道不是越多越好。先选 5-10 个：

- 官方产品频道。
- AI 自动化频道。
- AI 编程工具频道。
- 对比评测频道。
- 面向新手的教程频道。

### 先看三类信号

| 信号 | 判断 |
| --- | --- |
| 播放/发布时间 | 新视频短时间高播放，代表当前需求热 |
| 策略适配分 | 优先业务结果、流程自动化、真实案例、角色场景和对比决策 |
| 标题结构 | vs、honest results、case study、workflow、what businesses want 优先于 full course/master |
| 用户场景 | 不只看工具名，要看它解决的是获客、运营、交付、管理、决策、提效还是业务自动化 |

### 汇总表字段

每条候选源最终汇总成：

```text
来源平台：
频道/作者：
视频标题：
链接：
播放/日期：
标题结构：
用户焦虑：
内容结构：
证明方式：
可复刻点：
不可直接抄：
中文场景重写：
自己录屏验证方式：
推荐选题：
推荐 CTA：
二创优先级：
```

这个汇总表先给用户看，用户确认后再进入选题池。

### 二创边界

可以拆：

- 选题方向。
- 标题结构。
- 痛点和承诺。
- 演示顺序。
- 用户决策问题。
- 观点和结论框架。

必须重做：

- 画面。
- 字幕。
- 配音。
- 示例项目。
- 中文解释。
- CTA 和承接方式。

不建议直接使用：

- 原视频片段。
- 原音频。
- 完整字幕。
- 作者原创素材。
- 未经许可的截图。

### Codex 二创改写方向

```text
英文参考：展示工具能力、真实测试或业务流程
中文二创：用普通用户/运营/小老板的具体结果重写
```

优先把功能翻译成业务动作：

- 写代码 -> 操作电脑完成任务。
- 修 bug -> 让 AI 帮你检查流程漏洞。
- 生成 app -> 把一个业务需求变成可测试原型。
- code review -> 帮团队减少重复检查。
- Codex vs Claude Code -> 帮用户判断该把任务交给谁。

## AI 教学视频正文研究

当用户明确要研究“AI 教学”“AI 知识付费”“AI 工作流教程”这类爆款呈现方式时，先跑 `04a-reference-research-plan` 判断场景和关键词，再跑 `04b-reference-transcript-download` 下载正文，最后跑 `04c-reference-strategy-deconstruction` 拆解。

下载脚本：

```bash
python3 system/scripts/download_reference_transcripts.py \
  /path/to/client-workspace \
  --run-id <date>-reference-transcript-download \
  --env-file /path/to/private/.env \
  --douyin-strategy high_like \
  --douyin-strategy high_completion \
  --download-douyin-video \
  --transcribe-missing \
  --min-transcript-chars 120
```

旧脚本 `collect_teaching_video_scripts.py` 保留为兼容工具；新流程中不再用它承担策略拆解。

这个脚本会下载公开字幕、TikHub 抖音详情和可用正文，输出文案结构分析。没有正文的候选只进入 `excluded_no_transcript`，不能作为教学文案样本。它不允许复用原视频画面、原字幕、原案例、原作者素材。

拆解完成后，如果这批样本后续还要反复用于选题或文案优化，运行 04d 入库：

```bash
python3 system/scripts/promote_reference_deconstruction.py \
  /path/to/client-workspace \
  --deconstruction-run-id <deconstruction-run-id> \
  --run-id <date>-reference-bank-ingest \
  --write-bank
```

入库后的 `reference-bank` 才能被 `06a-copy-optimization` 和 `06-script-planning` 稳定读取。

重点拆：

- 前 5 秒是结果、反坑、收益、身份代入，还是概念混乱？
- 教学概念是否绑定到具体流程？
- 证明方式是录屏、案例、步骤、前后对比，还是权威背书？
- CTA 是评论、资料、课程、社群、星球，还是咨询？

进入当前账号脚本时，必须改写成：

```text
Codex 已经跑出的结果 -> 工作流解释 -> 提示词/数据/技能概念 -> 知识星球承接
```

## 输出

```text
参考来源：
原始选题：
它为什么可能有效：
可复刻结构：
风险和不可抄点：
新概念包装：
改写后的选题：
推荐内容形式：
推荐 CTA：
```
