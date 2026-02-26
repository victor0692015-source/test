#!/usr/bin/env bash
set -euo pipefail

# Build script for AuditorOS (Debian Live ISO)
# Requires: live-build, debootstrap, xorriso
# Resulting ISO is hybrid (USB/DVD), installable on BIOS and UEFI PCs via installer boot entry.

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKDIR="$ROOT_DIR/live-build"
SCANNER_SRC="$ROOT_DIR/../audit_tool.py"
SCANNER_DST="$WORKDIR/includes.chroot/usr/local/bin/audit_tool.py"
ISO_NAME="auditor-os-amd64.hybrid.iso"

cd "$WORKDIR"

if ! command -v lb >/dev/null 2>&1; then
  echo "[!] live-build is not installed. Install dependencies first:"
  echo "    sudo apt-get update && sudo apt-get install -y live-build debootstrap xorriso"
  exit 1
fi

if [[ ! -f "$SCANNER_SRC" ]]; then
  echo "[!] Cannot find scanner source: $SCANNER_SRC"
  exit 1
fi

mkdir -p "$(dirname "$SCANNER_DST")"
cp "$SCANNER_SRC" "$SCANNER_DST"
chmod +x "$SCANNER_DST"

echo "[*] Cleaning previous build..."
lb clean --purge || true

echo "[*] Configuring live-build..."
lb config \
  --architectures amd64 \
  --distribution bookworm \
  --binary-images iso-hybrid \
  --debian-installer live \
  --archive-areas "main contrib non-free non-free-firmware" \
  --linux-flavours amd64

echo "[*] Building ISO (this may take a while)..."
lb build

echo "[+] Build completed. Output ISO: $WORKDIR/$ISO_NAME"
echo "[+] Install on target PC: boot ISO and choose Installer from boot menu."
