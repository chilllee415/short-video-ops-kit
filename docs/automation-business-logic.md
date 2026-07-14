# 自动化业务逻辑

## 核心原则

自动化主要做三类事：

```text
稳定数据维护
持续素材积累
把最新证据串成当日建议并刷新运营大盘
```

涉及账号方向、正式选题、脚本定稿的事情，默认手动触发。原因是这些任务强依赖当下内容意图、产品承接和人工判断，不适合固定时间自动覆盖。

## 当前常驻自动化

| 任务 | 频率 | 业务目标 | 主要产物 |
| --- | --- | --- | --- |
| 每天更新运营大盘和作品表现 | 每天 15:00 | 维护账号数据、作品表现、日报和运营判断 | `account-snapshot.json`、`content-performance.json`、`post-metrics.json`、内部日报、大盘页面 |
| 每 2 天更新爆款素材库 | 每 2 天 09:00 | 持续积累可参考的爆款正文、结构和套路 | `reference-research-plan.json`、`reference-transcript-collection.json`、`reference-strategy-deconstruction.json`、`reference-bank.json` |
| 每周做用户需求调研 | 每周三 16:30 | 汇总用户需求/痛点，并输出对账号策略的影响建议 | `pain-bank.json`、`strategy-impact.md/json`、可选 `strategy-delta.json` |

每日任务按 `08-daily-ops-loop` 编排，顺序固定为：账号数据与反馈学习、策略约束、增量需求研究、按需爆款研究、当日内容计划、V2 页面。`work/plans/daily.json` 是“做计划”区域的唯一当日计划来源；只有它通过证据链门禁后才重建页面。

## 手动触发任务

| 任务 | 为什么手动 |
| --- | --- |
| 推荐下一批选题 | 需要结合当前要拍什么、素材库状态和你的选择，不自动覆盖正式选题池 |
| 生成可拍脚本 | 需要指定 topic、录制素材、CTA 和当期视频目标 |
| 复盘账号方向 | 需要你确认阶段目标，不应由自动化直接改变账号策略 |

## 已合并的子任务

以下任务保留为暂停状态，只在单独调试时启用：

```text
下载爆款视频正文
拆解爆款文案套路
把爆款套路存进素材库
每天复盘作品表现
```

它们分别被合并到：

```text
每 2 天更新爆款素材库
每天更新运营大盘和作品表现
```

## 爆款素材库流水线

`每 2 天更新爆款素材库` 是一个总工作流，内部顺序如下：

```text
04a 确定这轮要查哪些爆款
  -> 输出 reference-research-plan

04b 下载爆款视频正文
  -> 输出 reference-transcript-collection

04c 拆解爆款文案套路
  -> 输出 reference-strategy-deconstruction

04 Reference Mining 入库
  -> 更新 reference-bank / competitor-map
```

这个总工作流可以连续调度多个节点，但每个节点本身仍然保持职责单一。下游节点读取上游产物，不直接共享内部状态。

## 用户需求到账号策略

用户需求调研不直接改账号策略。正确关系是：

```text
用户需求/痛点变化
  -> 更新 pain-bank
  -> 输出 strategy-impact / strategy-delta
  -> 用户确认
  -> 手动更新 strategy-brief
```

`pain-bank.json` 是策略输入，不是策略本身。所有策略变化都必须标注“需要用户确认”，不能自动写回 `config/strategy/strategy-brief.json`。

## 运营数据到反馈学习

作品表现复盘已经合并进运营大盘：

```text
抖音后台数据
  -> content-performance / post-metrics
  -> account-snapshot
  -> feedback-learning / strategy-delta
  -> 内部日报和运营大盘
```

每日自动化可以写反馈学习和策略建议，但不能写正式账号策略，也不能自动生成正式选题。

## 选题和脚本

正式内容生产默认手动：

```text
手动推荐选题
  -> 读取 strategy-brief / pain-bank / reference-bank / 最新参考拆解
  -> 输出 topic candidates 或更新 topic-candidates

手动生成脚本
  -> 读取 selected-topics
  -> 输出 scripts / recording-plans
```

任何正式选题都必须保留：

```text
topic_id -> pain_id -> strategy_id -> reference_ids/evidence_ids
```

没有 pain lineage 的内容只能作为 idea，不进入正式推荐。

## 命名规则

已安排里的标题使用业务语言，不使用内部术语：

```text
每 2 天更新爆款素材库
每周做用户需求调研
每天更新运营大盘和作品表现
```

内部文档和 manifest 可以继续使用 `Pain Bank Builder`、`Reference Research Plan`、`Reference Transcript Download` 等工作流名，方便系统识别和排错。
