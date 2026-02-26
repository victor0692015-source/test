# AuditorOS (ISO image blueprint)

AuditorOS is a dedicated bootable/installable OS profile for running network and endpoint security audits with HTML/JSON reporting.

## What is implemented now

- ISO build scaffolding based on Debian Live (`live-build`).
- Automatic inclusion of `audit_tool.py` into the ISO rootfs during build.
- Preinstalled security/audit toolset list.
- `auditorctl` wrapper to run scans and store reports.
- SQLite scan registry (`/var/lib/auditor/auditor.db`).
- Local Scan Library dashboard (`auditor-dashboard.py`) on port `8088`.
- Service unit template for dashboard startup.

## Build ISO

```bash
cd auditor_os
./build_iso.sh
```

Output ISO is generated in `auditor_os/live-build/`.

## Install on any PC

See step-by-step guide:
- `auditor_os/INSTALL_ANY_PC.md`

## Runtime model

- Reports path: `/var/lib/auditor/reports`
- SQLite registry: `/var/lib/auditor/auditor.db`
- Scan launcher: `auditorctl scan <cidr> [flags]`
- Report list: `auditorctl report-list`
- Scan library: `auditorctl scan-library`
- Dashboard: `auditorctl dashboard`

## Security / legal

Use only with explicit written authorization from infrastructure owners.
