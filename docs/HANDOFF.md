# TRAE 云端迁移交接记录

## 已完成

- 阅读并核对 `AGENTS.md`、`README.md`、`skills/README.md`、`workflows/README.md`、初始化脚本、校验脚本和大盘更新脚本。
- 当前 TRAE 云端没有可用的 GitHub CLI 登录态，也没有本会话可调用的平台级发布分支/创建 PR 工具；但已通过只读 `git ls-remote` 验证远程分支已经存在并指向提交 `613b7ad851a436c42d5d2594aa9506bcc8fa967e`。
- 保留原有工作流、Schema、manifest、模板和脚本；未做架构重写。
- 检查到仓库原先仅提供 Codex 风格的 Skill 安装说明（`~/.codex/skills`）。当前 TRAE 会话的可发现 Skill 列表不包含仓库内五个 `short-video-*` Skill，直接按 Skill 名称调用返回 `Skill not found`，因此不能宣称这些 Skill 已被 TRAE 加载。
- 增加 `.trae-html-share-packages/` 和 `.trae-workspaces/` 到 `.gitignore`，避免云端预览包和本阶段工作区进入公开仓库。
- 使用原有 `scripts/create_workspace.py` 创建商业模式独立工作区：
  `/workspace/.trae-workspaces/female-fashion-store`
- 已运行校验并生成首次配置大盘。工作区仍保留模板的未确认占位配置；没有写入女装店的客群、定位、价格、账号策略、成交路径，也没有生成正式选题或文案。

## 真实验证结果

环境：Python 3.14.7，pip 26.2.1。

依赖：`python3 -m pip install -r requirements-dev.txt` 成功，安装 `jsonschema==4.26.0` 及其依赖。

已通过：

```bash
python3 scripts/audit_public_release.py
# 4 passed, 0 failed；包含 16 个 workflow manifest、公开/私有边界、P2 dashboard contract、9 条离线 smoke checks

python3 -m compileall -q scripts skills
# 通过

python3 scripts/validate_workspace.py /workspace/.trae-workspaces/female-fashion-store
# ok

python3 scripts/update_ops_dashboard.py /workspace/.trae-workspaces/female-fashion-store
# built dashboard data；rendered dashboard

python3 scripts/verify_ops_dashboard_html.py /workspace/.trae-workspaces/female-fashion-store
# dashboard HTML semantic verification passed
```

当前首次工作区的策略状态为 `draft` 且 `confirmed_by_user=false`，候选池为 `blocked`，符合“先问卷、未确认前不做正式运营”的门禁。页面中展示的日期来自模板数据，不代表真实经营数据。

## Skills 验证结果

- 五个仓库 Skill 的 `SKILL.md`、`agents/openai.yaml` 均存在。
- `short-video-ops-semantic-layer` 的三个 `references/*.md` 均存在。
- `short-video-topic-discovery/scripts/discover_context.py` 存在。
- 仓库内相对路径引用检查未发现越界绝对路径；其中 topic discovery 仍要求从仓库根目录运行 `python3 scripts/discover_context.py <workspace>`，不是从 Skill 子目录运行。
- 当前 TRAE 原生 Skill 发现列表不包含这些仓库 Skill；直接加载 `short-video-ops` 实际返回 `Skill not found`。因此目前只能确认文件资产完整，不能确认原生 Skill 已安装/启用，也不能把直接读取 `SKILL.md` 称为原生加载成功。
- TRAE 当前没有暴露可从本会话直接安装用户 Skill 的入口。若需要原生加载，应在 TRAE 的 Skills/Extensions 管理入口安装仓库 Skill，并在新会话中按名称触发验证。

## 大盘入口

本地文件入口：

```text
/workspace/.trae-workspaces/female-fashion-store/presentation/internal-pages/运营大盘.html
```

已启动仅服务 `presentation/` 目录的静态服务，未暴露整个 `/workspace`。可点击预览：`http://localhost:8765/internal-pages/%E8%BF%90%E8%90%A5%E5%A4%A7%E7%9B%98.html`。通过 `curl` 实际返回 HTML 文档并通过 TRAE 预览打开验证。该工作区没有纳入 Git，不能依靠 Git 在设备间同步。

## 数据保存与跨设备边界

- 会随 Git 提交保留：仓库中的通用脚本、模板、Schema、manifest、workflow、公开 Skill 资产、`.gitignore` 和本交接文档。
- 不应提交：工作区内的账号资料、平台导出、评论/私信、客户资料、真实经营数据、截图、运行结果、Cookie、API Key、`.env`。
- 本阶段工作区位于 TRAE 云端 `/workspace/.trae-workspaces/...`，属于被忽略的运行目录；本次已检查可用目录和环境变量，未发现可验证的 TRAE 平台级持久项目存储或工作区恢复 API；云端环境销毁、重置或更换后不保证存在。
- 首次配置问卷由 HTML 页面写入浏览器本地存储时，只存在于当前浏览器配置文件；不会自动上传，也不会自动写入正式 JSON。
- 要在 Mac 继续开发，应把工作区放在 Mac 上的独立目录，并通过受保护的同步/备份方式迁移需要保留的业务数据；不要把真实工作区复制进公开仓库。

## API 与采集

本阶段没有运行真实平台采集。抖音参考内容研究脚本依赖可选的 `TIKHUB_API_KEY`；当前未提供密钥，因此跳过真实采集，没有编造采集结果。抖音主平台、小红书和视频号的账号数据也尚未提供。

## Mac 接续步骤

1. 克隆本仓库的新分支，并安装 Python 3.10+ 与 `requirements-dev.txt`。
2. 在 Mac 的私有目录运行：

   ```bash
   python3 scripts/create_workspace.py ~/short-video-ops-data/female-fashion-store --mode commercial
   export SHORT_VIDEO_OPS_WORKSPACE=~/short-video-ops-data/female-fashion-store
   python3 scripts/validate_workspace.py "$SHORT_VIDEO_OPS_WORKSPACE"
   python3 scripts/update_ops_dashboard.py "$SHORT_VIDEO_OPS_WORKSPACE"
   ```

3. 打开生成的 `presentation/internal-pages/运营大盘.html`，填写首次问卷；把结构化结果交给 TRAE 复核。
4. 在写入 `config/profile/` 和 `config/strategy/strategy-brief.json` 前，确认女装店的定位和阶段策略；确认前不要生成正式选题、脚本或 ready 计划。
5. 业务确认后，再导入抖音/小红书/视频号导出数据和实体店真实素材，保留来源日期；缺失数据继续标记为缺失。
6. 如需研究抖音参考内容，把密钥放在仓库外的私有 `.env` 文件中，仅通过 `--env-file` 使用。

## 最小持久化方案与需要操作的一步

当前没有可验证的平台级工作区持久化/恢复机制。跨设备前最小安全方案是：只在本地私有目录保存工作区，通过加密云盘或私有 Git 仓库同步；不要将真实工作区提交到当前公开 Fork。需要用户操作的一步：在 Mac 创建私有目录并运行仓库命令重新初始化工作区；若要恢复已填写问卷或真实数据，再由用户通过受保护方式单独复制工作区内容。

初始化工作区可随时重建：

```bash
python3 scripts/create_workspace.py ~/short-video-ops-data/female-fashion-store --mode commercial
```

## 待办

- 确认实体女装店的客群、问题/场景、商品范围与价格带、账号角色和内容方向。
- 确认主平台抖音与辅平台小红书/视频号的分发差异。
- 确认成交路径（到店、私信、团购、小程序、微信或其他）和阶段目标。
- 提供可使用的账号基线、作品表现、客户真实问题、商品/门店证明素材。
- 决定 TRAE 中采用仓库内 Skill 的何种安装/调用机制；当前已验证仓库 Skill 未出现在本会话可发现列表，需由 TRAE 环境提供安装入口后再做端到端触发验证。
