# Windows setup (no separate OS)

## 1) Open project in PyCharm (optional)
You can use PyCharm only as editor. Running is done from terminal/PowerShell.

## 2) Install Python 3.11+
Install from python.org and ensure `python` works in PowerShell.

## 3) Run scanner directly

```powershell
python windows_app/auditor_win.py scan 192.168.1.0/24
```

Reports and DB will be stored in:
- `%USERPROFILE%\AuditorData\reports`
- `%USERPROFILE%\AuditorData\auditor.db`

## 4) Open Scan Library dashboard

```powershell
python windows_app/auditor_win.py dashboard --port 8088
```

Open browser:
- http://127.0.0.1:8088

## 5) Build EXE files (optional)

```powershell
powershell -ExecutionPolicy Bypass -File windows_app/build_windows.ps1
```

EXE output:
- `dist\audit_tool.exe`
- `dist\auditor_win.exe`
- `dist\scan_library.exe`

## Notes
- This is a Windows application workflow; no ISO and no separate OS are required.
- Use only with written authorization.
