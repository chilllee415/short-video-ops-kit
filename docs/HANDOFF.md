# TRAE 云端迁移交接记录

## 已完成

- 阅读并核对 `AGENTS.md`、`README.md`、`skills/README.md`、`workflows/README.md`、初始化脚本、校验脚本和大盘更新脚本。
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

## 大盘入口

本地文件入口：

```text
/workspace/.trae-workspaces/female-fashion-store/presentation/internal-pages/运营大盘.html
```

这是云端临时工作区中的静态 HTML。若当前 TRAE 会话提供本地预览服务，可通过预览 URL 打开；否则直接在云端文件浏览器打开该 HTML。该工作区没有纳入 Git，不能依靠 Git 在设备间同步。

## 数据保存与跨设备边界

- 会随 Git 提交保留：仓库中的通用脚本、模板、Schema、manifest、workflow、公开 Skill 资产、`.gitignore` 和本交接文档。
- 不应提交：工作区内的账号资料、平台导出、评论/私信、客户资料、真实经营数据、截图、运行结果、Cookie、API Key、`.env`。
- 本阶段工作区位于 TRAE 云端 `/workspace/.trae-workspaces/...`，属于被忽略的运行目录；云端环境销毁、重置或更换后不保证存在。
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

## 待办

- 确认实体女装店的客群、问题/场景、商品范围与价格带、账号角色和内容方向。
- 确认主平台抖音与辅平台小红书/视频号的分发差异。
- 确认成交路径（到店、私信、团购、小程序、微信或其他）和阶段目标。
- 提供可使用的账号基线、作品表现、客户真实问题、商品/门店证明素材。
- 决定 TRAE 中采用仓库内 Skill 的何种安装/调用机制；当前已验证仓库 Skill 未出现在本会话可发现列表，需由 TRAE 环境提供安装入口后再做端到端触发验证。
