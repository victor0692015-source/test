#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

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
  notes TEXT
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def add_scan(db_path: Path, json_path: Path, html_path: Path, notes: str = "") -> None:
    payload = json.loads(json_path.read_text(encoding="utf-8")) if json_path.exists() else {}
    hosts = payload.get("hosts", [])
    findings_total = sum(len(h.get("findings", [])) for h in hosts)
    max_risk = max((int(h.get("risk_score", 0)) for h in hosts), default=0)

    conn = connect(db_path)
    conn.execute(
        """
        INSERT INTO scans(created_at,cidr,json_path,html_path,hosts_total,findings_total,max_risk,notes)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            payload.get("target_network"),
            str(json_path.resolve()),
            str(html_path.resolve()),
            len(hosts),
            findings_total,
            max_risk,
            notes,
        ),
    )
    conn.commit()
    conn.close()


def list_rows(db_path: Path) -> list[tuple]:
    if not db_path.exists():
        return []
    conn = connect(db_path)
    rows = conn.execute(
        "SELECT id,created_at,cidr,json_path,html_path,hosts_total,findings_total,max_risk,notes FROM scans ORDER BY id DESC LIMIT 300"
    ).fetchall()
    conn.close()
    return rows


def render_index(rows: list[tuple], reports_dir: Path) -> str:
    cards = []
    for row in rows:
        sid, created_at, cidr, json_path, html_path, hosts, findings, max_risk, notes = row
        cards.append(
            "<div class='card'>"
            f"<h3>Scan #{sid}</h3>"
            f"<p><b>Time:</b> {html.escape(created_at)}</p>"
            f"<p><b>Target:</b> {html.escape(cidr or '-')}</p>"
            f"<p><b>Hosts:</b> {hosts} | <b>Findings:</b> {findings} | <b>Max risk:</b> {max_risk}</p>"
            f"<p><b>Notes:</b> {html.escape(notes or '-')}</p>"
            f"<p><a href='/reports/{html.escape(Path(html_path).name)}'>Open HTML report</a> | "
            f"<a href='/reports/{html.escape(Path(json_path).name)}'>Open JSON</a></p>"
            "</div>"
        )

    if not cards:
        cards.append("<div class='card'><h3>No scans yet</h3><p>Run one scan to populate library.</p></div>")

    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Auditor Scan Library</title>
<style>
body{{margin:0;font-family:Arial;background:#f4f7fb;color:#18314f}}
.top{{background:#fff;border-bottom:1px solid #d9e4ef;padding:14px 20px;display:flex;justify-content:space-between}}
.logo{{font-size:30px;font-weight:700;color:#1857a4}} .pill{{background:#f1d93b;padding:4px 10px;border-radius:16px}}
.wrap{{max-width:1200px;margin:0 auto;padding:16px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:12px}}
.card{{background:#fff;border:1px solid #e7edf4;border-radius:12px;padding:12px;box-shadow:0 2px 8px rgba(10,37,64,.08)}}
a{{color:#1857a4}}
</style></head><body>
<div class='top'><div class='logo'>comoda</div><div class='pill'>Scan Library</div></div>
<div class='wrap'><h1>Windows Auditor - Scan Library</h1><p>Reports: <code>{html.escape(str(reports_dir))}</code></p><div class='grid'>{''.join(cards)}</div></div>
</body></html>"""


def serve(reports_dir: Path, db_path: Path, port: int) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connect(db_path).close()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path in {"/", "/index.html"}:
                body = render_index(list_rows(db_path), reports_dir).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path.startswith("/reports/"):
                f = reports_dir / parsed.path.replace("/reports/", "", 1)
                if f.exists() and f.is_file():
                    data = f.read_bytes()
                    ctype = "application/json" if f.suffix == ".json" else "text/html; charset=utf-8"
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format: str, *args):
            return

    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"[+] Dashboard: http://127.0.0.1:{port}")
    httpd.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description="Windows scan library")
    parser.add_argument("--db", default=str(Path.home() / "AuditorData" / "auditor.db"))
    parser.add_argument("--reports", default=str(Path.home() / "AuditorData" / "reports"))
    parser.add_argument("--port", type=int, default=8088)

    sub = parser.add_subparsers(dest="cmd", required=True)
    p_add = sub.add_parser("add")
    p_add.add_argument("--json", required=True)
    p_add.add_argument("--html", required=True)
    p_add.add_argument("--notes", default="")

    sub.add_parser("serve")

    args = parser.parse_args()
    db_path = Path(args.db)
    reports_dir = Path(args.reports)

    if args.cmd == "add":
        add_scan(db_path, Path(args.json), Path(args.html), args.notes)
        print("[+] Scan added to SQLite")
        return 0

    serve(reports_dir, db_path, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
