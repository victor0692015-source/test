#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp -n .env.example .env || true

echo "Заполните .env и запустите:"
echo "source .venv/bin/activate && python bot/main.py"
