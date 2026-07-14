# Skill Assets

This directory is for reusable, commercial-safe skills that belong to the public system.

Do not put raw personal skills here.

## Included Public Skills

- [`short-video-ops`](short-video-ops/SKILL.md)：编排完整的每日运营闭环。
- [`short-video-ops-semantic-layer`](short-video-ops-semantic-layer/SKILL.md)：约束数据层级、证据角色、读写边界与血缘。
- [`short-video-topic-discovery`](short-video-topic-discovery/SKILL.md)：评估方向并生成 6:4 双候选池，再选出 2+1 日更组合。
- [`short-video-benchmark-mining`](short-video-benchmark-mining/SKILL.md)：围绕已选题寻找并拆解可迁移的高价值参考结构。
- [`short-video-copywriting`](short-video-copywriting/SKILL.md)：把选题、参考结构和真实证明转成可直接拍摄的口播稿。

“看账号、做计划、更新页面”主要是稳定、可校验的工作流节点，定义在 `manifests/`；找选题、找爆款和写文案包含较多可复用判断策略，因此同时提供 Skill。Skill 负责判断方法，manifest 仍负责输入、输出和写入边界。

## Migration Classes

| Class | Location | Commit | Use |
| --- | --- | --- | --- |
| System skill | `skills/` | Yes | Commercial-safe reusable capability |
| Workspace skill | `<workspace>/archive/legacy-skills/` | No | Project-specific capability asset |
| Raw legacy skill | `<workspace>/archive/legacy-skills/raw-legacy/` | No | Original imported skill, not enabled by default |
| Commercial candidate | `<workspace>/archive/legacy-skills/commercial-candidates/` | No | Candidate waiting for identity cleanup and abstraction |
| Distilled skill | `<workspace>/archive/legacy-skills/distilled/` | No by default | Clean project-specific version derived from raw legacy material |

## Promotion Rule

A legacy skill can be promoted into this directory only after it passes:

1. No operator personal name, handle, avatar, private path, or private account data.
2. No customer raw data, private screenshots, DMs, or unpublished performance data.
3. No hard-coded personal strategy that should instead live in `config/strategy/strategy-brief.json`.
4. Inputs and outputs are declared through workflow manifests or workspace indexes.
5. The skill can run against a new commercial workspace with only public templates and that workspace's data source.

## Current Stance

The system repo stores the reusable framework. Personal experience, voice preferences, competitor observations, and historical feedback stay in the external workspace data source.
