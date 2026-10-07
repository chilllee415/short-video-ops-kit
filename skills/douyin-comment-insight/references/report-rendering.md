# 报告发布约定

最终分析 JSON 通过 `scripts/publish_report.py` 发布。

- 详情页模板：`assets/templates/report.html`
- 首页模板：`assets/templates/index.html`
- 默认输出：`workspace/site/`
- 详情页：`{accountId}.html`
- 索引源数据：`comment-insight-index.json`
- 浏览器数据包：`comment-insight-index-data.js`

详情页模板必须且只能包含一组 `INSIGHT_DATA_START` / `INSIGHT_DATA_END` 标记。发布器替换标记中的 `pageData`，不会把 API Key 写入页面。

同一 `accountId` 再次发布时覆盖详情页并替换索引中的旧记录；不得追加重复账号。只有 `commentCount > 0` 时状态才是 `completed`。

