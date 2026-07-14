# 10 分钟跑出第一份运营大盘

这套工具不是替你“自动做爆款”。它会把账号数据、用户需求、参考内容和今天的动作整理到同一个页面，让你知道下一条内容该从哪里开始。

## 你需要准备什么

- Codex Desktop 或 Codex CLI。这是运行工作流、阅读资料和更新运营判断的主工具。
- Python 3.10 或更高版本。
- 一个本地文件夹，用来存放自己的账号数据。这个文件夹不要上传到 GitHub。
- 可选：TikHub 密钥。只有下载和研究抖音参考内容时才需要。

## 第一步：下载项目并安装校验依赖

```bash
git clone <your-github-repository-url> short-video-ops
cd short-video-ops
python3 -m pip install -r requirements-dev.txt
```

## 第二步：创建自己的工作区

工作区存你的账号资料和运行结果。它和项目代码分开，方便保护隐私。

```bash
python3 scripts/create_workspace.py ~/short-video-ops-data/my-account
```

创建脚本会同时生成首次配置页面。打开工作区中的 `presentation/internal-pages/运营大盘.html`，即可填写账号定位与运营策略问卷。

如果你在为客户交付，使用：

```bash
python3 scripts/create_workspace.py ~/short-video-ops-data/client-a --mode commercial
```

## 第三步：先确认账号定位和运营策略

打开新工作区的 `config/profile/`，先修改这三个文件：

- `account.profile.json`：你的账号做什么。
- `audience.profile.json`：你想服务谁。
- `offer.profile.json`：你希望通过内容承接什么服务、产品或咨询。

再打开 `config/strategy/strategy-brief.json`，确认当前阶段目标、主拍方向、选题原则、排除项和转化路径。账号定位回答“这个账号长期为谁解决什么问题”，运营策略回答“现阶段优先拍什么、为什么、哪些不做”；旧选题、热门视频和页面标题都不能替代这两项确认。

如果你不知道如何填写，先把下面这段话发给 Codex：

```text
请先检查我的账号定位和运营策略。如果缺失、仍是模板示例或尚未确认，请依次确认：账号阶段、主赛道、创作者身份、目标用户、核心需求、真实资源、阶段目标、商业承接、内容形式和未来规划。请基于事实生成多个内容方向方案，不要预设为 AI 或其他特定赛道。请先总结给我确认，再写入 config/profile/ 和 config/strategy/strategy-brief.json。确认前不要找选题、拆爆款或生成 ready 计划。
```

也可以先运行一次大盘生成命令并打开 HTML。首次配置页会先识别赛道，再动态展示对应需求选项，并根据账号身份、资源、商业目标和后续规划生成三套内容方向。用户选择后，页面才整理定位、阶段策略和 30／60／90 天规划，再生成结构化提示词交给 Codex 复核。页面不会直接把未确认草案写入正式配置。

随后把平台导出或截图放进 `data/operations/raw/`，把可确认的当前账号快照维护在 `data/operations/current/`。刚开始没有完整数据也可以，模板会保留空字段；但不要编造播放、涨粉或咨询数据。

## 第四步：交给 Codex 更新运营大盘

用 Codex 打开项目后，发送：

```text
请阅读 AGENTS.md，使用工作区 ~/short-video-ops-data/my-account 更新今天的运营大盘。
请先检查账号定位和运营策略是否完整且已经由我确认；如果没有，请先向我提问并等待确认。
确认后再检查账号数据、作品数据和选题信号；不要编造缺失的数据。
最后告诉我：最重要的一个信号、今天的内容动作和还缺什么数据。
```

Codex 会读取你提供的资料、更新工作区，并调用 Python 脚本生成页面。没有 Codex 时，你也可以手动维护各业务域的 `current/` JSON，再运行以下命令渲染页面：

```bash
python3 scripts/validate_workspace.py ~/short-video-ops-data/my-account
python3 scripts/update_ops_dashboard.py ~/short-video-ops-data/my-account
```

生成后的页面在：

```text
~/short-video-ops-data/my-account/presentation/internal-pages/运营大盘.html
```

双击即可在浏览器中打开。

可直接复制的版本见 [每日更新大盘提示词](../prompts/daily-dashboard.md)。

## 想研究一条抖音参考内容

把密钥放在项目外的私有文件，例如 `~/.config/short-video-ops/.env`：

```env
TIKHUB_API_KEY=你的密钥
TIKHUB_BASE_URL=https://api.tikhub.io
```

再运行：

```bash
python3 scripts/download_single_douyin_reference.py \
  ~/short-video-ops-data/my-account \
  "https://v.douyin.com/你的链接/" \
  --env-file ~/.config/short-video-ops/.env
```

它会下载公开参考内容、尝试获得字幕或转写，并把可用于研究的结构化结果写回工作区。请遵守平台条款，只学习内容结构，不复制别人的原文、画面或案例。
