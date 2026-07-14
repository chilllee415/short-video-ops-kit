# 04d Reference Bank Ingest

把 `04c` 产生的爆款拆解结果沉淀到长期参考库。

这个步骤只做“归档和规范化”，不重新下载视频，也不重新拆文案。它的价值是把临时研究结果变成后续选题、文案优化和脚本生成都能读取的用户数据。

## 什么时候运行

当一批爆款参考已经完成：

```text
04b Reference Transcript Download
-> 04c Reference Strategy Deconstruction
-> 04d Reference Bank Ingest
```

只有确认样本有长期复用价值时才写入 `data/benchmarks/current/reference-bank.json`。如果只是一次性研究，先 dry-run 看候选即可。

## 输入

- `runs/<deconstruction-run-id>/outputs/reference-strategy-deconstruction.json`
- `config/strategy/strategy-brief.json`
- `data/benchmarks/current/reference-bank.json`

## 输出

- `runs/<run-id>/outputs/reference-bank-additions.json`
- `runs/<run-id>/outputs/reference-bank-additions.md`
- 可选写入：`data/benchmarks/current/reference-bank.json`

## 运行方式

先 dry-run：

```bash
python3 system/scripts/promote_reference_deconstruction.py \
  /path/to/client-workspace \
  --deconstruction-run-id <deconstruction-run-id> \
  --run-id <date>-reference-bank-ingest
```

确认后写入长期参考库：

```bash
python3 system/scripts/promote_reference_deconstruction.py \
  /path/to/client-workspace \
  --deconstruction-run-id <deconstruction-run-id> \
  --run-id <date>-reference-bank-ingest \
  --write-bank
```

## 入库规则

每条参考必须包含：

- 来源平台、作者、标题、链接。
- 可观察指标，至少保留播放、点赞、评论、分享、收藏或时长中的可用项。
- `content_intents`：内容意图，如结果前置、教学拆步、个人复盘、工作流包装。
- `usable_for`：后续能借什么，如 hook、proof pattern、workflow explanation、CTA logic。
- `rewrite_notes`：可以迁移的策略。
- `do_not_copy`：不能复制的原句、素材、画面、作者故事和高风险承诺。

## 使用边界

参考库是“结构库”，不是“可抄素材库”。

可以借：

- 选题角度。
- 开头类型。
- 证明方式。
- 内容节奏。
- CTA 承接逻辑。

必须替换：

- 原文表达。
- 原视频画面和音频。
- 作者个人经历。
- 未验证数据。
- 收益、估值、结果承诺。
