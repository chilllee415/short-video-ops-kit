# GitHub 发布前检查

## 必做

- [ ] 运行 `python3 scripts/audit_public_release.py`，所有检查通过。
- [ ] 确认没有 `user-data/`、真实账号导出、评论、私信、客户资料、运行结果或 API 密钥。
- [ ] 确认 `.env` 没有被提交，只保留 `.env.example`。
- [ ] 按 [快速开始](quick-start.md) 在一个全新目录创建工作区并生成页面。
- [ ] 确认 `LICENSE` 和 `NOTICE` 随仓库一起发布；修改后再次分发时保留这两个文件并说明改动。

## 建议的 GitHub 首次发布内容

- 仓库简介：`把短视频账号数据、用户需求和内容参考整理成每日可执行的运营计划。`
- Topics：`douyin`、`content-operations`、`ai-workflow`、`codex`、`creator-tools`。
- Release 名称：`v0.1.0-beta`。
- 明确说明：平台数据源、模型与第三方 API 由使用者自行配置并遵守其服务条款。
