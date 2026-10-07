# TRAE 通用基础搭建

## 适用范围

`short-video-ops-kit` 是通用短视频内容运营助手，适用于女装、医美、本地生活、电商、知识类、个人 IP 及其他内容类目。仓库只保存通用工作流、Schema、Skills、脚本和展示模板；任何具体项目的账号资料、策略、平台数据、客户资料和凭据都应放在独立工作区。

系统主流程保持为：

```text
新建项目
→ 类目与账号资料录入
→ 账号历史数据导入
→ 内容诊断
→ 用户需求与痛点研究
→ 对标及跨行业参考挖掘
→ 选题候选
→ 人工确认选题
→ 文案与拍摄方案
→ 每日内容计划
→ 发布数据回流
→ 内容效果分析
→ 规则与文案能力反哺
```

## 1. 在 TRAE 云端打开项目

在 TRAE 中打开仓库根目录，并确认终端工作目录是仓库根目录：

```bash
cd /workspace
python3 --version
python3 -m pip install -r requirements-dev.txt
```

运行仓库级公开发布检查：

```bash
python3 scripts/audit_public_release.py
python3 -m compileall -q scripts skills
```

## 2. 安装并启用五个 Skills

仓库提供以下通用 Skills：

```text
short-video-ops
short-video-ops-semantic-layer
short-video-topic-discovery
short-video-benchmark-mining
short-video-copywriting
```

在 TRAE 的 Skills / Extensions / 用户 Skill 管理入口中，从仓库的 `skills/` 目录安装五个 Skill；如果界面要求重启或新会话，完成后再验证。验证必须通过 TRAE 的 Skill 调用机制逐个调用名称，并记录返回的 Skill Path、名称和描述。

“原生 Skill 加载成功”是指 TRAE 的 Skill 调用机制实际返回该 Skill；直接打开或读取仓库中的 `SKILL.md` 只能证明文件存在，不能替代原生加载验证。

当前仓库 Skill 的脚本和引用路径按仓库根目录解析。运行 topic discovery 的辅助脚本时使用：

```bash
python3 skills/short-video-topic-discovery/scripts/discover_context.py /absolute/path/to/workspace
```

## 3. 创建任意类目的工作区

创建命令接受任意路径、项目 ID、显示名称和尚未确认的类目：

```bash
python3 scripts/create_workspace.py \
  ~/short-video-ops-data/example-project \
  --mode personal \
  --project-id example-project \
  --display-name "Example Project" \
  --category generic
```

商用项目使用：

```bash
python3 scripts/create_workspace.py \
  ~/short-video-ops-data/client-project \
  --mode commercial \
  --project-id client-project \
  --display-name "Client Project" \
  --category generic
```

创建脚本会复制独立的配置、数据、工作、展示、反馈、归档和审计目录，并生成：

```text
project.manifest.json
project.registry.json
```

`project.registry.json` 只记录项目登记信息：`project_id`、`display_name`、`category`、`workspace_path`、`status`、`created_at`、`last_run_at`，不得写入客户隐私、API Key 或平台凭据。每个工作区必须使用独立路径，不得复用已有目录。

首次创建的模板保持未确认状态：策略为 `draft`，`confirmed_by_user` 为 `false`，正式选题池和可执行文案保持阻塞。

## 4. 导入账号资料和作品数据

先在工作区中填写并确认：

```text
config/profile/account.profile.json
config/profile/audience.profile.json
config/profile/offer.profile.json
config/strategy/strategy-brief.json
```

再将平台导出或人工整理的数据放入对应的 `data/operations/raw/`、`data/topic-research/raw/`、`data/benchmarks/raw/` 和 `data/feedback/raw/` 目录，并在 `current/` 中维护带来源日期的规范化数据。

不要把真实工作区复制到公开仓库；不要把 Cookie、密钥、私信、客户身份信息或未公开素材放进仓库。

## 5. 运行账号诊断

设置工作区变量并校验：

```bash
export SHORT_VIDEO_OPS_WORKSPACE=~/short-video-ops-data/example-project
python3 scripts/validate_workspace.py "$SHORT_VIDEO_OPS_WORKSPACE"
python3 scripts/update_ops_dashboard.py "$SHORT_VIDEO_OPS_WORKSPACE"
```

只有在账号定位和策略已由用户明确确认后，才进入正式选题、对标拆解和文案流程。缺少真实数据时必须报告缺失，不得生成虚构结论。

## 6. 进入选题与文案流程

按工作流顺序执行：

```text
账号诊断
→ 用户需求与痛点证据
→ 策略确认
→ 选题候选
→ 人工确认选题
→ 参考内容结构拆解
→ 文案与拍摄方案
```

选题候选必须保留策略、评估、搜索范围和证据链路。没有已确认策略或用户侧需求证据时，保持 `blocked`，不要用热门创作者内容替代需求证据。

## 7. 回填发布数据

发布后将平台记录和指标放入工作区的反馈域：

```text
data/feedback/raw/published-posts.json
data/feedback/raw/post-metrics.json
data/feedback/current/learning.json
data/feedback/current/strategy-delta.json
```

保留平台、作品 ID、观察日期、指标来源和数据范围；运行校验与大盘更新后，再由反馈工作流提出规则或文案能力调整建议。反馈不能自动覆盖用户确认的稳定定位和策略。

## 8. Windows 与 Mac 接续开发

在任一设备上都从同一仓库安装依赖，并把业务工作区保存在设备外部的私有目录。Mac 使用 `python3`；Windows PowerShell 使用 `py -3` 替代 `python3`：

```powershell
py -3 scripts\create_workspace.py $HOME\short-video-ops-data\example-project --mode personal --project-id example-project --category generic
py -3 scripts\validate_workspace.py $HOME\short-video-ops-data\example-project
```

不要把被忽略的云端临时目录当作跨设备持久化。需要恢复业务工作区时，通过私有加密云盘或私有 Git 仓库同步，不要提交到公开 Fork。

## 9. 通用引擎与具体项目数据

通用引擎包括：

- `skills/`、`workflows/`、`schemas/`、`manifests/`
- `scripts/`、`prompts/`、`templates/`
- `docs/` 中的通用使用说明

具体项目数据包括：

- `config/` 中的账号定位、目标用户、产品或服务、策略和确认记录
- `data/` 中的平台导出、评论、私信、客户素材、需求证据和发布指标
- `work/` 中的候选题、选题确认、脚本、发布计划和复盘结果
- `presentation/` 和 `runs/` 中的项目运行产物

具体项目数据必须放在独立工作区，不能写入通用引擎目录。

## 10. 防止项目数据混用

- 每个项目使用独立的绝对路径和唯一 `project_id`。
- 每次运行只读取目标工作区 manifest 声明的路径。
- 不从其他工作区补齐缺失数据。
- 不把演示模板、旧项目结果或热门内容当作新项目事实。
- 提交前运行 `python3 scripts/audit_public_release.py`、`git diff --check` 和 `git status --short --ignored`。
- 任何 API Key、`.env`、Cookie、客户资料和真实账号数据都不得提交。
