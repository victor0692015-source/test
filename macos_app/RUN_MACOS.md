# macOS setup

## 1) Install Python
Install Python 3.11+ and verify:

```bash
python3 --version
```

## 2) Run scanner

```bash
python3 macos_app/auditor_mac.py scan 192.168.1.0/24
```

Data paths:
- `~/Library/Application Support/AuditorData/reports`
- `~/Library/Application Support/AuditorData/auditor.db`

## 3) Open dashboard

```bash
python3 macos_app/auditor_mac.py dashboard --port 8088
```

Open browser: `http://127.0.0.1:8088`

## 4) Build .app bundle

```bash
bash macos_app/build_macos.sh
```

Artifacts:
- `dist/NetworkAuditorMac.app`
- `dist/ScanLibraryMac.app`
- `dist/NetworkAuditorMac_bundle.zip`

## 5) Copy to USB flash drive

```bash
cp dist/NetworkAuditorMac_bundle.zip /Volumes/<USB_NAME>/
```

## Notes
- Build must be done on macOS.
- On first launch Gatekeeper may require right-click → Open.
