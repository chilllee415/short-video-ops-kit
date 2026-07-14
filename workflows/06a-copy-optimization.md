# 06a Copy Optimization Reference Match

文案优化不能直接凭感觉改。先分析原稿，再从用户数据里的参考库中找到最适合借鉴的案例和策略。

这个流程发生在正式脚本生成之前，也可以单独用于用户给出一段口播稿时的快速优化。

## 目标

把“我觉得文案差点意思”拆成三件事：

1. 原稿哪里弱：开头、证明、节奏、概念顺序、CTA。
2. 用户数据里哪几条内容最适合借鉴。
3. 每条参考具体借什么，以及哪些内容不能抄。

## 输入

- 用户原始文案。
- `config/profile/account.profile.json`
- `config/strategy/strategy-brief.json`
- `data/benchmarks/current/reference-bank.json`

## 输出

- `runs/<run-id>/outputs/copy-reference-match.json`
- `runs/<run-id>/outputs/copy-reference-match.md`

## 运行方式

```bash
python3 system/scripts/optimize_copy_with_reference_bank.py \
  /path/to/client-workspace \
  --current-draft "<用户原始文案>" \
  --run-id <date>-copy-reference-match \
  --top-k 5
```

也可以从文件读取：

```bash
python3 system/scripts/optimize_copy_with_reference_bank.py \
  /path/to/client-workspace \
  --draft-file /path/to/draft.txt \
  --run-id <date>-copy-reference-match \
  --top-k 5
```

## 文案优化顺序

1. 先判断原稿的内容类型和用户核心意图。
2. 判断开头 3 秒是否明确：结果、痛点、Codex 主角和可见证明。
3. 判断方法论出现顺序：不要一上来讲“提示词/垂域数据”，先给结果或反差。
4. 从 `reference-bank` 选 3-5 条参考。
5. 输出借鉴映射：
   - 借开头方式。
   - 借证明方式。
   - 借结构节奏。
   - 借 CTA 逻辑。
   - 明确不能抄的点。
6. 再进入正式文案改写。

## 当前账号优先规则

如果原稿是 Codex/AI 工作流内容，优先匹配：

- 用户自己已经跑出数据的内部爆款。
- 已入库的 AI 头部博主拆解。
- 和“结果展示、工作流包装、垂域数据、用户痛点、爆款拆解”有关的参考。

泛工具教程、未经验证收益承诺、纯 AI 技巧合集只作为低优先级结构参考。
