---
name: douyin-daily-report
description: Generate a traceable Douyin daily operations report from structured account data and historical comparisons, with Markdown output and fixed-template HTML rendering.
---

# Douyin Daily Report

用于通用抖音运营日报自动化，不绑定具体类目、账号或经营策略。

## 工作流

```text
采集数据 -> 写入结构化 JSON -> 对比历史数据 -> 生成 Markdown 日报 -> 渲染 HTML
```

原始日报模板、示例 JSON 和分享提示词位于本 Skill 的 `templates/`、`examples/` 和 `prompts/` 目录。ZIP 未提供独立渲染脚本；本 Skill 附带的通用渲染器为 `scripts/render_daily_report.py`（源仓库同时提供 `scripts/render_daily_report.py`），只做占位字段替换，不重构模板，并拒绝覆盖已有输出。

## 规则

- 优先读取当天结构化数据和昨天或近 7 天历史数据。
- 平台未展示的指标必须写“平台未显示”。
- 采集遇到登录、扫码或验证码时暂停并请求人工处理。
- 不覆盖仍有价值的历史日报；每次输出使用新的目标路径。
- 示例数据仅用于模板兼容性和离线渲染验证，不代表真实采集结果。
- 真实采集凭据不得写入 Skill、JSON、HTML、日志或 Git 远程地址。

## 推荐字段

至少包括日期、报告标题、账号身份、数据范围、KPI、最佳作品、变化信号、行动建议和观察清单；具体字段以 `examples/daily-report.sample.json` 与模板占位符为准。

## TRAE 使用

在 TRAE 的 Skills 管理入口导入本目录。采集、分析与发布由用户明确触发；本 Skill 不自动访问平台，不生成未提供的数据。
