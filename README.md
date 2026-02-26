# Network Auditor (Windows + macOS)

> ⚠️ Используйте только при наличии письменного разрешения на аудит.

## Что это

Это локальный аудитор сети с:
- сканером `audit_tool.py`;
- HTML + JSON отчётами;
- локальной Scan Library (SQLite + веб-страница);
- launcher-приложениями для Windows и macOS.

## Быстрый старт Windows

```powershell
python windows_app/auditor_win.py scan 192.168.1.0/24
python windows_app/auditor_win.py dashboard --port 8088
```

## Быстрый старт macOS

```bash
python3 macos_app/auditor_mac.py scan 192.168.1.0/24
python3 macos_app/auditor_mac.py dashboard --port 8088
```

## Где лежат данные

Windows:
- `%USERPROFILE%\AuditorData\reports`
- `%USERPROFILE%\AuditorData\auditor.db`

macOS:
- `~/Library/Application Support/AuditorData/reports`
- `~/Library/Application Support/AuditorData/auditor.db`

## Сборка приложений

Windows EXE:
```powershell
powershell -ExecutionPolicy Bypass -File windows_app/build_windows.ps1
```

macOS APP:
```bash
bash macos_app/build_macos.sh
```

## Документация

- `windows_app/RUN_WINDOWS.md`
- `macos_app/RUN_MACOS.md`

## Legacy

Каталог `auditor_os/` оставлен как legacy-скелет и не нужен для основного desktop workflow.
