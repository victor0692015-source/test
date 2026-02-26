#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


def load_rows(db_path: Path) -> list[tuple]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT id,created_at,cidr,json_path,html_path,hosts_total,findings_total,max_risk,endpoint_mode,notes "
        "FROM scans ORDER BY id DESC LIMIT 200"
    ).fetchall()
    conn.close()
    return rows


def render_index(rows: list[tuple], reports_dir: Path) -> str:
    cards = []
    for row in rows:
        sid, created_at, cidr, json_path, html_path, hosts, findings, max_risk, endpoint_mode, notes = row
        json_name = Path(json_path).name
        html_name = Path(html_path).name
        cards.append(
            "<div class='card'>"
            f"<h3>Scan #{sid}</h3>"
            f"<p><b>Time:</b> {html.escape(created_at)}</p>"
            f"<p><b>Target:</b> {html.escape(cidr or '-')}</p>"
            f"<p><b>Hosts:</b> {hosts} | <b>Findings:</b> {findings} | <b>Max risk:</b> {max_risk}</p>"
            f"<p><b>Endpoint mode:</b> {'ON' if endpoint_mode else 'OFF'}</p>"
            f"<p><b>Notes:</b> {html.escape(notes or '-')}</p>"
            f"<p><a href='/reports/{html.escape(html_name)}'>Open HTML report</a> | "
            f"<a href='/reports/{html.escape(json_name)}'>Open JSON</a></p>"
            "</div>"
        )

    if not cards:
        cards.append("<div class='card'><h3>No scans yet</h3><p>Run: <code>auditorctl scan 192.168.1.0/24</code></p></div>")

    return f"""<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>AuditorOS Scan Library</title>
<style>
:root{{--brand-blue:#0f3c7a;--brand-yellow:#f2d21b;}}
body{{margin:0;font-family:Arial;background:#f3f6fb;color:#172b4d;}}
.top{{display:flex;justify-content:space-between;align-items:center;padding:14px 20px;background:#fff;border-bottom:1px solid #d8e3f1;}}
.logo{{font-size:34px;font-weight:700;color:#1857a4;}} .pill{{background:#fff3b0;padding:4px 10px;border-radius:20px;}}
.wrap{{max-width:1200px;margin:0 auto;padding:16px;}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:12px;}}
.card{{background:#fff;border:1px solid #e7edf4;border-radius:12px;padding:12px;box-shadow:0 2px 8px rgba(10,37,64,.08);}}
a{{color:#1857a4;text-decoration:none;}}a:hover{{text-decoration:underline;}}
</style>
</head>
<body>
<div class='top'><div class='logo'>comoda</div><div class='pill'>Scan Library</div></div>
<div class='wrap'>
  <h1>AuditorOS - Scan Library</h1>
  <p>Reports directory: <code>{html.escape(str(reports_dir))}</code></p>
  <div class='grid'>{''.join(cards)}</div>
</div>
</body>
</html>"""


def make_handler(reports_dir: Path, db_path: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path in {"/", "/index.html"}:
                rows = load_rows(db_path)
                body = render_index(rows, reports_dir).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if parsed.path.startswith("/reports/"):
                local = reports_dir / parsed.path.replace("/reports/", "", 1)
                if local.exists() and local.is_file():
                    data = local.read_bytes()
                    ctype = "application/json" if local.suffix == ".json" else "text/html; charset=utf-8"
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

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="AuditorOS Scan Library dashboard")
    parser.add_argument("--reports", default="/var/lib/auditor/reports")
    parser.add_argument("--db", default="/var/lib/auditor/auditor.db")
    parser.add_argument("--port", type=int, default=8088)
    args = parser.parse_args()

    reports_dir = Path(args.reports)
    db_path = Path(args.db)
    reports_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    httpd = ThreadingHTTPServer(("0.0.0.0", args.port), make_handler(reports_dir, db_path))
    print(f"[+] AuditorOS dashboard: http://0.0.0.0:{args.port}")
    print(f"[+] Reports dir: {reports_dir}")
    print(f"[+] SQLite DB: {db_path}")
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
