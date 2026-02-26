$ErrorActionPreference = 'Stop'

# Build Windows executable bundle with PyInstaller
# Run in PowerShell from repository root.

python -m pip install --upgrade pip
python -m pip install pyinstaller

# Build scanner exe
pyinstaller --clean --onefile --name audit_tool audit_tool.py

# Build launcher exe
pyinstaller --clean --onefile --name auditor_win windows_app/auditor_win.py

# Build dashboard/library exe
pyinstaller --clean --onefile --name scan_library windows_app/scan_library.py

Write-Host "Done. EXE files are in .\dist"
