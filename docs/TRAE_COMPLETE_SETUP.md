# TRAE Complete Setup

## 部署范围

本仓库按上传的《运营助手.zip》部署了三套通用工具：

- 短视频运营助手 v2：保留原有工作流、Schema、manifest、workspace 模板、脚本、五个 Skills 和运营大盘。
- 抖音评论洞察：保留 Python 采集、分析、发布、模板、示例、测试、许可证和安全说明，并增加 TRAE 导入说明。
- 抖音运营日报：保留日报 Skill、HTML 模板、示例 JSON 和分享提示词；ZIP 未提供独立渲染器，仓库补充了最小字段替换渲染器。

示例数据只用于离线验证，不代表真实账号、评论或平台采集结果。

## 七个 Skills

1. `short-video-ops`：编排从账号数据与确认策略到诊断、选题、计划和反馈的主流程。
2. `short-video-ops-semantic-layer`：解释和审计工作区的策略、证据、数据契约和产物。
3. `short-video-topic-discovery`：在已确认方向内发现候选选题并保留证据链。
4. `short-video-benchmark-mining`：对已选主题进行参考内容结构和证明方式拆解。
5. `short-video-copywriting`：根据主题、证据和参考结构生成拍摄口播稿。
6. `douyin-comment-insight`：从真实抖音评论生成可审计的洞察与静态报告。
7. `douyin-daily-report`：从结构化数据和历史对比生成 Markdown/HTML 日报。

## 在 TRAE 中导入

在 TRAE 的 Skills 管理入口逐个导入以下独立目录：

```text
skills/short-video-ops/
skills/short-video-ops-semantic-layer/
skills/short-video-topic-discovery/
skills/short-video-benchmark-mining/
skills/short-video-copywriting/
skills/douyin-comment-insight/
skills/douyin-daily-report/
```

目录结构和 frontmatter 验证不等于 TRAE 原生加载成功；原生加载需要在 TRAE Skills 入口启用后由调用机制实际返回该 Skill。

## 创建任意类目的项目

```bash
python3 scripts/create_workspace.py /absolute/private/path/example-project \
  --mode personal \
  --project-id example-project \
  --display-name "Example Project" \
  --category generic
```

`commercial` 可用于商业交付项目。每个 workspace 独立保存配置、原始数据、当前数据、工作文件、展示页、反馈和审计信息。首次创建默认策略为 `draft`，需用户明确确认后才能进入正式选题和文案流程。

## 运行短视频运营助手

```bash
python3 scripts/validate_workspace.py /absolute/private/path/example-project
python3 scripts/update_ops_dashboard.py /absolute/private/path/example-project
python3 scripts/verify_ops_dashboard_html.py /absolute/private/path/example-project
```

打开 workspace 下的 `presentation/internal-pages/运营大盘.html`。不得把演示数据当作真实经营数据；缺失数据应保持缺失或阻塞状态。

## 评论洞察

离线验证：

```bash
python3 -m pip install -r skills/douyin-comment-insight/requirements.txt
python3 -m unittest discover -s skills/douyin-comment-insight/tests -v
python3 skills/douyin-comment-insight/scripts/validate_package.py
python3 skills/douyin-comment-insight/scripts/demo.py
```

真实采集前，将 `TIKHUB_API_KEY` 和可选的 `TIKHUB_BASE_URL` 配置在 TRAE 敏感变量或项目外私密配置中。禁止写入仓库、`.env`、日志、JSON、HTML 或 Git 远程地址。当前部署没有执行真实 TikHub 采集。

## 抖音运营日报

日报逻辑保持：采集数据 → 结构化 JSON → 历史对比 → Markdown 日报 → HTML 日报。

字段兼容性检查：

```bash
python3 scripts/validate_daily_report_template.py
python3 scripts/render_daily_report.py \
  --template integrations/douyin-daily-report/templates/daily-report-template.html \
  --data integrations/douyin-daily-report/examples/daily-report.sample.json \
  --output /tmp/daily-report/report.html
```

渲染器只进行安全字段替换，输出路径已存在时拒绝覆盖，因此历史日报不会被覆盖。平台未展示的指标必须写为“平台未显示”。

## 数据与跨设备使用

通用引擎在本仓库；具体账号、评论、平台导出、日报和运行产物应放入私有项目 workspace 或私有项目仓库。不要把 `.env`、API Key、Cookie、Token、客户资料、真实评论和真实报告提交到 Git。Windows 与 Mac 可分别克隆同一 GitHub 仓库获取通用工具；私有项目数据必须使用安全的私有存储或私有仓库同步，不能依赖云端临时目录或浏览器本地存储。

## 已验证与未验证

已验证：核心审计与编译、通用 demo workspace 校验、大盘生成和 HTML 语义、评论洞察单元测试/包校验/离线 demo、日报模板字段兼容性/HTML 渲染/拒绝覆盖、七个 Skill 文件结构和相对引用检查。

未验证：TRAE 原生加载结果、TikHub 在线采集、真实账号端到端运行，以及 TRAE 平台 PR 创建。原生加载和在线能力不因本地文件验证通过而自动成立。
