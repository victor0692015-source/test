#!/usr/bin/env bash
set -euo pipefail

# Build macOS app bundle + distributable zip
# Run on macOS host.

python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller

pyinstaller --clean --windowed --name NetworkAuditorMac macos_app/auditor_mac.py
pyinstaller --clean --windowed --name ScanLibraryMac macos_app/scan_library_mac.py

mkdir -p dist/macos_bundle
cp -R dist/NetworkAuditorMac.app dist/macos_bundle/
cp -R dist/ScanLibraryMac.app dist/macos_bundle/
cp audit_tool.py dist/macos_bundle/

( cd dist && zip -r NetworkAuditorMac_bundle.zip macos_bundle )

echo "[+] Done. Artifacts:"
echo "    dist/NetworkAuditorMac.app"
echo "    dist/ScanLibraryMac.app"
echo "    dist/NetworkAuditorMac_bundle.zip"
