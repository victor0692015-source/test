#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  cidr TEXT,
  json_path TEXT NOT NULL,
  html_path TEXT NOT NULL,
  hosts_total INTEGER DEFAULT 0,
  findings_total INTEGER DEFAULT 0,
  max_risk INTEGER DEFAULT 0,
  endpoint_mode INTEGER DEFAULT 0,
  notes TEXT
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def parse_json_stats(json_path: Path) -> dict[str, int | str | None]:
    if not json_path.exists():
        return {"cidr": None, "hosts_total": 0, "findings_total": 0, "max_risk": 0, "endpoint_mode": 0}
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    hosts = payload.get("hosts", [])
    findings_total = sum(len(h.get("findings", [])) for h in hosts)
    max_risk = max((int(h.get("risk_score", 0)) for h in hosts), default=0)
    endpoint_mode = int(bool(payload.get("endpoint_malware_scan", {}).get("enabled", False)))
    return {
        "cidr": payload.get("target_network"),
        "hosts_total": len(hosts),
        "findings_total": findings_total,
        "max_risk": max_risk,
        "endpoint_mode": endpoint_mode,
    }


def cmd_init(args: argparse.Namespace) -> int:
    with connect(Path(args.db)):
        pass
    print(f"[+] DB initialized: {args.db}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    db = Path(args.db)
    json_path = Path(args.json).resolve()
    html_path = Path(args.html).resolve()
    stats = parse_json_stats(json_path)

    conn = connect(db)
    conn.execute(
        """
        INSERT INTO scans(created_at,cidr,json_path,html_path,hosts_total,findings_total,max_risk,endpoint_mode,notes)
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            stats["cidr"],
            str(json_path),
            str(html_path),
            stats["hosts_total"],
            stats["findings_total"],
            stats["max_risk"],
            stats["endpoint_mode"],
            args.notes,
        ),
    )
    conn.commit()
    conn.close()
    print(f"[+] Scan registered in DB: {db}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AuditorOS SQLite registry")
    parser.add_argument("--db", default="/var/lib/auditor/auditor.db")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize DB")
    p_init.set_defaults(func=cmd_init)

    p_add = sub.add_parser("add", help="Register scan result")
    p_add.add_argument("--json", required=True)
    p_add.add_argument("--html", required=True)
    p_add.add_argument("--notes", default="")
    p_add.set_defaults(func=cmd_add)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
