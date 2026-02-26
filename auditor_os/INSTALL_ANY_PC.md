# Install AuditorOS on any PC (like Windows/Ubuntu)

## 1) Build ISO

```bash
cd auditor_os
./build_iso.sh
```

ISO output:
- `auditor_os/live-build/auditor-os-amd64.hybrid.iso`

## 2) Create bootable USB

Linux example:

```bash
sudo dd if=auditor_os/live-build/auditor-os-amd64.hybrid.iso of=/dev/sdX bs=4M status=progress oflag=sync
```

Or use Rufus/BalenaEtcher from Windows.

## 3) Install on target PC

1. Boot target PC from USB.
2. In boot menu choose **Installer** (Debian Live installer).
3. Follow installation wizard (disk, user, locale, network).
4. Reboot into installed AuditorOS.

## 4) First start

```bash
sudo systemctl enable --now auditor-dashboard.service
auditorctl db-init
auditorctl scan 192.168.1.0/24
```

Dashboard:
- `http://<pc-ip>:8088`

## Notes

- Works on common x86_64 hardware (BIOS/UEFI) if boot from USB is supported.
- Use only with written authorization for audited infrastructure.
