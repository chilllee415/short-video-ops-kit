# 04c 参考正文策略拆解工作流

## 目的

把已经抓到的原始正文/逐字稿，进一步拆成可复用的短视频策略：开头钩子、证明方式、流程包装、概念植入、CTA 承接和当前文案改写建议。

这个工作流不负责重新抓视频，也不重新下载正文。它只读取 `04b-reference-transcript-download` 的输出，保证采集和策略拆解分层。

## 输入

- `runs/<source-run-id>/outputs/reference-transcript-collection.json`
- 兼容旧产物：`runs/<source-run-id>/outputs/teaching-video-script-analysis.json`
- 可选：当前待优化文案

## 执行命令

```bash
python3 system/scripts/decompose_reference_strategy.py \
  /path/to/client-workspace \
  --source-run-id <source-run-id> \
  --run-id <source-run-id>-strategy-deconstruction \
  --current-draft "当前文案"
```

## 输出

```text
runs/<run-id>/outputs/reference-strategy-deconstruction.json
runs/<run-id>/outputs/reference-strategy-deconstruction.md
runs/<run-id>/run.manifest.json
```

## 拆解维度

| 维度 | 作用 |
| --- | --- |
| 场景适配 | 判断参考内容属于教学、复盘、结果展示、知识付费承接还是工作流展示 |
| 开头钩子 | 判断它用成果前置、反坑、新手友好、数字框架还是主题承诺 |
| 证明方式 | 提取数据、画面、工作台、系统、案例、录屏等证据 |
| 工作流节点 | 把正文里的流程、步骤、工具模块、自动化节点拆出来 |
| 概念桥 | 判断概念是如何接在流程之后，而不是开头空讲 |
| CTA | 判断评论、关注、资料、课程、社群、星球等承接方式 |
| 迁移策略 | 输出当前账号可借鉴的结构，不复用原句 |

## 对当前文案的用法

对于“最近几条视频数据不错，我用 Codex 从定位、选题、文案到视频生成”的文案，优先输出：

- 这条更像“AI 内容生产工作流复盘”，不是单纯 AI 基础教学。
- 开头应先给数据/结果，再说自己不懂运营。
- 七个工作流必须命名，不能只说“包括 xxxxxx”。
- “AI 不是标准答案，是概率结果”应该放在数据积累之后。
- 知识星球 CTA 应承接“完整流程拆解/模板/案例复盘”，不要变成泛 AI 课。

## 边界

- 不复制原视频口播句子。
- 不使用原画面、原音频、原案例作为发布素材。
- 本地 Whisper tiny 生成的正文错字较多，适合结构拆解；正式引用前必须人工校对。
