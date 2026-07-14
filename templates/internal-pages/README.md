# Internal Page Templates

## 运营大盘 V2

Template:
`system/templates/internal-pages/ops-dashboard.template.html`

Daily data:
`<workspace>/presentation/ops-dashboard.json`

Rendered page:
`<workspace>/presentation/internal-pages/运营大盘.html`

Daily workflow contract:

1. Update the normalized/generated user data.
2. Build `presentation/ops-dashboard.json`.
3. Render the page.

One-command update:

```bash
cd /path/to/short-video-ops/system
python3 scripts/update_ops_dashboard.py "$SHORT_VIDEO_OPS_WORKSPACE"
```

When `SHORT_VIDEO_OPS_WORKSPACE` is already exported, this also works:

```bash
python3 scripts/update_ops_dashboard.py
```

For this workspace, the explicit command is:

```bash
python3 /path/to/short-video-ops/system/scripts/update_ops_dashboard.py /path/to/client-workspace
```

Advanced split commands:

```bash
python3 scripts/build_ops_dashboard_data.py "$SHORT_VIDEO_OPS_WORKSPACE"
python3 scripts/render_ops_dashboard.py "$SHORT_VIDEO_OPS_WORKSPACE"
```
