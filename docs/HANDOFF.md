# TRAE 通用基础项目交接记录

## 项目范围

本仓库是通用短视频内容运营助手，适用于不同类目。具体项目资料必须保存在独立工作区，不写入通用引擎、模板、Skills 或默认配置。

## 已完成

- 保留原有工作流、Schema、manifest、模板和脚本，未进行架构重写。
- 创建脚本已支持任意工作区路径、项目 ID、显示名称、类目和 personal/commercial 模式。
- 创建脚本会生成独立的 `project.registry.json`，只保存项目登记元数据。
- 通用模板配置已清除原有具体示例定位、受众和服务内容，初始状态保持未确认。
- 新增 `docs/TRAE_SETUP.md`，说明 TRAE 使用、任意类目工作区、数据隔离和跨设备接续。

## 验证边界

五个仓库 Skill 必须通过 TRAE 的 Skill 调用机制验证；直接读取仓库 `SKILL.md` 只能证明文件存在，不能替代原生加载验证。当前会话的原生加载结果应以实际调用返回为准。

工作区首次创建后应保持：

- `config/strategy/strategy-brief.json` 为 `draft`。
- `confirmed_by_user` 为 `false`。
- 正式候选题、计划和文案保持阻塞。
- 不包含客户资料、账号数据、凭据或平台 Token。

## 数据保存边界

- 通用引擎：`skills/`、`workflows/`、`schemas/`、`manifests/`、`scripts/`、`prompts/`、`templates/` 和通用文档，可提交到仓库。
- 项目数据：工作区中的 `config/`、`data/`、`work/`、`presentation/`、`runs/` 和归档内容，不应提交到公开仓库。
- 云端临时目录和浏览器本地问卷不能视为跨设备持久化。
- Mac 或 Windows 接续时，应在私有目录重建或恢复独立工作区，并使用受保护的同步方式保存真实项目数据。

## 验收命令

```bash
python3 scripts/audit_public_release.py
python3 -m compileall -q scripts skills
python3 scripts/create_workspace.py /absolute/private/path/example-project \
  --mode personal \
  --project-id example-project \
  --display-name "Example Project" \
  --category generic
python3 scripts/validate_workspace.py /absolute/private/path/example-project
python3 scripts/update_ops_dashboard.py /absolute/private/path/example-project
python3 scripts/verify_ops_dashboard_html.py /absolute/private/path/example-project
```

## 仍需人工配置

- 在 TRAE 的 Skill 管理入口安装并启用五个仓库 Skill。
- 新会话中逐个调用五个 Skill，记录原生加载结果。
- 为具体项目确认类目、账号定位、目标用户、业务资料、数据来源和阶段策略。
- 在策略确认前不要生成正式选题、文案或 ready 计划。
