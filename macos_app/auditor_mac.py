#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_scan(cidr: str, extra: list[str], data_dir: Path) -> int:
    reports = data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_out = reports / f"audit_{ts}.json"
    html_out = reports / f"audit_{ts}.html"

    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "audit_tool.py"),
        cidr,
        "--out",
        str(json_out),
        "--human-out",
        str(html_out),
        *extra,
    ]
    print("[*]", " ".join(cmd))
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        return rc

    db_cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent / "scan_library_mac.py"),
        "--db",
        str(data_dir / "auditor.db"),
        "--reports",
        str(reports),
        "add",
        "--json",
        str(json_out),
        "--html",
        str(html_out),
        "--notes",
        "macos-runner",
    ]
    return subprocess.run(db_cmd).returncode


def open_dashboard(data_dir: Path, port: int) -> int:
    reports = data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent / "scan_library_mac.py"),
        "--db",
        str(data_dir / "auditor.db"),
        "--reports",
        str(reports),
        "--port",
        str(port),
        "serve",
    ]
    print("[*]", " ".join(cmd))
    return subprocess.run(cmd).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="macOS launcher for auditor scanner")
    parser.add_argument("--data-dir", default=str(Path.home() / "Library" / "Application Support" / "AuditorData"))

    sub = parser.add_subparsers(dest="cmd", required=True)
    p_scan = sub.add_parser("scan")
    p_scan.add_argument("cidr")
    p_scan.add_argument("extra", nargs=argparse.REMAINDER)

    p_dash = sub.add_parser("dashboard")
    p_dash.add_argument("--port", type=int, default=8088)

    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    if args.cmd == "scan":
        return run_scan(args.cidr, args.extra, data_dir)
    return open_dashboard(data_dir, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
