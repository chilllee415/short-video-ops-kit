# 分析输出约定

`findings.json` 只写 Codex 基于真实评论完成的语义归纳，至少包含：

```json
{
  "lane": "账号内容赛道",
  "summary": "一句话结论",
  "metrics": {
    "comments": 0,
    "highValueSignals": 0,
    "needClusters": 0,
    "highPotential": 0
  },
  "viewpoints": [],
  "opportunities": [],
  "run": {
    "status": "completed",
    "completedAt": "ISO-8601 时间"
  }
}
```

每个观点对象包含 `id`、`title`、`summary`、`evidenceCommentIds`。每个机会对象包含 `id`、`type`、`title`、`evidenceCommentIds`、`inference`、`validationAction`、`metric`、`confidence`。

规则：

- 证据 ID 必须存在于 `analysis-input.json` 的 `comments[].commentId`。
- 机会优先覆盖引流体验、付费交付、资源沉淀，但证据不足时减少数量，不得凑数。
- `title` 写具体交付物；`validationAction` 写清钩子、入口、交付物、承接方式和量化指标。
- 没有证据支持的判断写“待验证”，不得虚构付费意愿。
- 不改写原始评论文本，不在输出中保存 API Key。

`finalize_analysis.py` 会把观点和机会 ID 回填到评论，并拒绝不存在的证据 ID。

