# 04b 参考爆款正文下载工作流

## 目的

按账号阶段策略和参考内容研究计划，去 YouTube / B站 / 抖音批量寻找对标爆款，并拿到可用正文/逐字稿。

这个工作流只负责“找视频、下载视频、抽音频、转文字、保存原始文件”。它不做策略拆解，不生成选题池，也不改写当前文案。策略拆解交给 `04c-reference-strategy-deconstruction`。

## 输入

- `config/strategy/strategy-brief.json`
- `data/topic-research/current/pain-bank.json`
- `data/benchmarks/current/reference-bank.json`
- 研究计划里的平台、关键词、采集配比和入选标准
- 可选：TikHub 抖音榜单 API Key
- 可选：ASR provider key 或本机 `whisper`

## 适用场景

优先采：

- AI 内容生产工作流复盘
- AI 自动化教学
- AI 知识付费承接
- Codex / Claude Code / AI agent 实战演示
- 自媒体选题、文案、录制、剪辑的 AI 工作流

谨慎采：

- 月入、暴利、副业承诺类视频。可以借标题冲突，不借收益承诺。
- 超长大课。只保留开头承诺、结构和转化方式，不照搬课程结构。
- 只有标题和描述、没有口播正文的样本。默认不进入下载结果。

## 执行命令

```bash
cd /path/to/short-video-ops
python3 system/scripts/download_reference_transcripts.py \
  /path/to/client-workspace \
  --run-id <date>-reference-transcript-download \
  --plan-run-id <date>-reference-research-plan \
  --env-file /path/to/private/.env \
  --douyin-strategy high_like \
  --douyin-strategy high_completion \
  --download-douyin-video \
  --transcribe-missing \
  --asr-provider local-whisper \
  --local-whisper-model tiny \
  --min-transcript-chars 120
```

抖音正文链路必须是：

```text
TikHub 榜单/详情 -> 取 video.download_addr/play_addr -> 下载 mp4 -> ffmpeg 抽 mp3 -> ASR 转写 -> clean.txt
```

`--asr-provider` 可选 `auto`、`groq`、`openai`、`local-whisper`。没有 Groq/OpenAI key 时，可以用本机 `whisper` 命令兜底；`tiny` 速度快但错字较多，适合结构拆解，正式引用前需要人工校对。

## 输出

```text
data/benchmarks/raw/references/transcript-downloads/<run-id>/
runs/<run-id>/outputs/reference-transcript-collection.json
runs/<run-id>/outputs/reference-transcript-collection.md
runs/<run-id>/run.manifest.json
```

每条下载结果至少包含：

```text
来源平台 / 作者 / 标题 / 链接 / 热度指标
正文状态 / 正文来源 / 正文字数
clean.txt 文件路径
视频文件路径
音频文件路径
```

## 正文门槛

默认规则：没有可用正文的样本不能进入 `items`。

- YouTube：优先下载公开字幕或自动字幕。
- B站：优先读取公开视频字幕；没有字幕则进入 `excluded_no_transcript`。
- 抖音：TikHub 只作为视频发现和下载地址来源；默认不把 `desc/description/caption` 当正文。开启 `--download-douyin-video --transcribe-missing` 后，脚本会下载视频、用 `ffmpeg` 抽音频，再用 ASR 生成正文。

如果只是想临时研究平台描述文案，可以加 `--allow-description-body`，但这类样本不能替代口播逐字稿。

## 下游交接

下载完成后，把 `<run-id>` 传给 04c：

```bash
python3 system/scripts/decompose_reference_strategy.py \
  /path/to/client-workspace \
  --source-run-id <date>-reference-transcript-download \
  --run-id <date>-reference-strategy-deconstruction \
  --current-draft "当前文案"
```

04c 会读取 `reference-transcript-collection.json`，只做策略拆解，不再抓取或下载视频。
