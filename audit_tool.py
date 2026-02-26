#!/usr/bin/env python3
"""Локальный инструмент аудита инфраструктуры (образовательный аналог Nessus Expert)."""

from __future__ import annotations

import argparse
import html
import ipaddress
import json
import shlex
import socket
import subprocess
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_PORTS = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 389, 443, 445, 465, 587, 993, 995, 1433, 1521, 2049, 3306, 3389, 5432, 5900, 6379, 8080, 8443]
WEAK_SERVICES = {
    21: "FTP открыт: проверьте анонимный доступ и TLS.",
    23: "Telnet открыт: небезопасный протокол, рекомендована миграция на SSH.",
    445: "SMB открыт: проверьте версию SMB и отключение SMBv1.",
    3389: "RDP открыт: проверьте MFA, NLA и ограничения по IP.",
    6379: "Redis открыт: проверьте bind, ACL и пароль.",
}
WINDOWS_PORT_HINTS = {135, 139, 445, 3389, 5985, 5986}
LINUX_PORT_HINTS = {22, 111, 2049}
MAC_PORT_HINTS = {548}


@dataclass
class PortFinding:
    port: int
    status: str
    service_hint: str
    banner: str | None
    severity: str
    recommendation: str | None


@dataclass
class EndpointScanConfig:
    enabled: bool
    user: str | None
    timeout: float


@dataclass
class HostReport:
    ip: str
    reachable: bool
    findings: list[PortFinding]
    risk_score: int
    probable_os: str
    os_confidence: str
    os_reason: str
    antivirus_status: str
    malware_scan_status: str
    malware_scan_summary: str


def parse_ports(raw: str | None) -> list[int]:
    if not raw:
        return DEFAULT_PORTS
    ports: set[int] = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, b = chunk.split("-", maxsplit=1)
            for p in range(int(a), int(b) + 1):
                if 1 <= p <= 65535:
                    ports.add(p)
        else:
            p = int(chunk)
            if 1 <= p <= 65535:
                ports.add(p)
    if not ports:
        raise ValueError("Список портов пуст или некорректен.")
    return sorted(ports)


def detect_local_cidr() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
    except OSError:
        local_ip = "127.0.0.1"
    finally:
        sock.close()
    return str(ipaddress.ip_network(f"{local_ip}/24", strict=False))


def network_hosts(cidr: str) -> list[str]:
    net = ipaddress.ip_network(cidr, strict=False)
    if net.num_addresses > 65536:
        raise ValueError("Сеть слишком большая. Укажите меньший диапазон (до /16).")
    return [str(ip) for ip in net.hosts()]


def tcp_probe(ip: str, port: int, timeout: float) -> tuple[bool, str | None]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        if sock.connect_ex((ip, port)) != 0:
            return False, None
        banner = None
        try:
            if port in {21, 22, 25, 80, 110, 143, 443, 587, 8080, 8443}:
                if port in {80, 8080, 8443}:
                    sock.sendall(b"HEAD / HTTP/1.0\r\nHost: audit.local\r\n\r\n")
                banner = sock.recv(256).decode("utf-8", errors="ignore").strip() or None
        except OSError:
            banner = None
        return True, banner
    finally:
        sock.close()


def discover_reachable(ip: str, seed_ports: Iterable[int], timeout: float) -> bool:
    return any(tcp_probe(ip, p, timeout)[0] for p in seed_ports)


def severity_for_port(port: int) -> tuple[str, str | None]:
    if port in WEAK_SERVICES:
        return "medium", WEAK_SERVICES[port]
    if port in {22, 443, 8443}:
        return "low", "Проверьте актуальность версии сервиса и политику доступа."
    return "info", None


def service_name(port: int) -> str:
    if port > 49151:
        return "unknown"
    try:
        return socket.getservbyport(port, "tcp")
    except OSError:
        return "unknown"


def detect_probable_os(findings: list[PortFinding]) -> tuple[str, str, str]:
    ports = {f.port for f in findings}
    banners = " ".join((f.banner or "").lower() for f in findings)
    win = len(ports & WINDOWS_PORT_HINTS) + (2 if ("microsoft" in banners or "windows" in banners) else 0)
    lin = len(ports & LINUX_PORT_HINTS) + (1 if "openssh" in banners else 0)
    mac = len(ports & MAC_PORT_HINTS) + (2 if ("apple" in banners or "darwin" in banners) else 0)
    if max(win, lin, mac) == 0:
        return "unknown", "low", "Недостаточно данных для уверенного определения ОС."
    if win >= lin and win >= mac:
        return "windows", ("high" if win >= 2 else "medium"), "Признаки Windows (SMB/RDP/WinRPC/баннер)."
    if lin >= win and lin >= mac:
        return "linux", ("medium" if lin >= 2 else "low"), "Признаки Linux/Unix (SSH/RPC/NFS/баннер)."
    return "macos", ("medium" if mac >= 2 else "low"), "Признаки macOS/Apple (AFP/баннер)."


def detect_antivirus_status(os_key: str) -> str:
    if os_key == "windows":
        return "network_only_unknown_windows"
    if os_key == "unknown":
        return "unknown_os"
    return "network_only_unknown_other"


def endpoint_malware_scan(ip: str, os_key: str, open_ports: set[int], cfg: EndpointScanConfig) -> tuple[str, str]:
    if not cfg.enabled:
        return "disabled", "Endpoint malware scan выключен."
    if not cfg.user:
        return "missing_credentials", "Нужен --endpoint-user и настроенный SSH ключ (BatchMode)."
    if os_key != "linux":
        return "unsupported_os", "Автопроверка реализована только для Linux по SSH; для Windows нужен WinRM/WMI агент."
    if 22 not in open_ports:
        return "unreachable", "SSH (22/tcp) недоступен, endpoint-скан не выполнен."

    remote_cmd = (
        "if command -v systemctl >/dev/null 2>&1; then "
        "for s in falcon-sensor wazuh-agent osqueryd clamav-daemon clamd; do "
        "systemctl is-active $s >/dev/null 2>&1 && echo ACTIVE:$s; done; "
        "fi"
    )
    ssh_cmd = [
        "ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={int(cfg.timeout)}",
        f"{cfg.user}@{ip}", remote_cmd,
    ]
    try:
        proc = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=max(5, cfg.timeout + 2))
    except (subprocess.TimeoutExpired, OSError) as exc:
        return "error", f"Ошибка endpoint-скана: {exc}"

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "SSH auth/connect error").strip()
        return "auth_failed", f"SSH не выполнен: {err[:180]}"

    active = [line.split(":", 1)[1] for line in proc.stdout.splitlines() if line.startswith("ACTIVE:")]
    if active:
        return "ok", "Найдены активные endpoint-защитники: " + ", ".join(active)
    return "ok", "Endpoint-доступ подтверждён, но активные AV/EDR сервисы не обнаружены по текущим сигнатурам."


def host_audit(ip: str, ports: list[int], timeout: float, endpoint_cfg: EndpointScanConfig) -> HostReport:
    findings: list[PortFinding] = []
    reachable = discover_reachable(ip, (22, 80, 443, 445, 3389), timeout)
    if not reachable:
        return HostReport(ip, False, findings, 0, "unknown", "low", "Хост не ответил на базовые TCP-проверки.", "not_applicable", "not_run", "Хост недоступен.")

    for p in ports:
        open_port, banner = tcp_probe(ip, p, timeout)
        if not open_port:
            continue
        sev, rec = severity_for_port(p)
        findings.append(PortFinding(p, "open", service_name(p), banner, sev, rec))

    risk = sum({"info": 1, "low": 2, "medium": 5, "high": 8}.get(f.severity, 1) for f in findings)
    os_key, conf, reason = detect_probable_os(findings)
    av = detect_antivirus_status(os_key)
    malware_status, malware_summary = endpoint_malware_scan(ip, os_key, {f.port for f in findings}, endpoint_cfg)
    return HostReport(ip, True, findings, risk, os_key, conf, reason, av, malware_status, malware_summary)


def scan_network(cidr: str, ports: list[int], timeout: float, workers: int, endpoint_cfg: EndpointScanConfig) -> list[HostReport]:
    reports: list[HostReport] = []
    lock = threading.Lock()

    def task(host_ip: str) -> None:
        report = host_audit(host_ip, ports, timeout, endpoint_cfg)
        if report.reachable:
            with lock:
                reports.append(report)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(task, ip) for ip in network_hosts(cidr)]
        for f in as_completed(futures):
            f.result()

    return sorted(reports, key=lambda x: x.risk_score, reverse=True)


def save_report(reports: list[HostReport], target: Path, cidr: str, ports: list[int], endpoint_cfg: EndpointScanConfig) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_network": cidr,
        "ports": ports,
        "endpoint_malware_scan": {"enabled": endpoint_cfg.enabled, "user": endpoint_cfg.user},
        "hosts": [{**asdict(h), "findings": [asdict(f) for f in h.findings]} for h in reports],
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _bar_rows(title: str, values: dict[str, int], color: str) -> str:
    if not values:
        return f"<h3>{html.escape(title)}</h3><p>—</p>"
    mx = max(values.values())
    out = [f"<h3>{html.escape(title)}</h3>"]
    for k, v in sorted(values.items(), key=lambda x: x[1], reverse=True):
        width = max(4, round((v / mx) * 100)) if mx else 4
        out.append(f"<div class='bar-row'><div class='bar-label'>{html.escape(k)} — {v}</div><div class='bar-track'><div class='bar-fill' style='width:{width}%; background:{color};'></div></div></div>")
    return "\n".join(out)


def save_human_report(reports: list[HostReport], target: Path, cidr: str, ports: list[int], endpoint_cfg: EndpointScanConfig) -> None:
    tr = {
        "ru": {"switch": "Язык:", "title": "Отчёт по аудиту сети", "rights": "Права на аудит", "rights_text": "Проверка выполняется только при письменном разрешении владельца инфраструктуры.", "endpoint": "Endpoint malware scan", "enabled": "включён", "disabled": "выключен", "malware": "Malware scan", "network": "Сеть", "date": "Дата", "checked": "Проверено портов", "top": "Узлы с наибольшим риском", "risk": "Риск", "os": "ОС", "av": "Антивирус", "actions": "Рекомендуемые действия", "no_critical": "Критичных рекомендаций не выявлено."},
        "en": {"switch": "Language:", "title": "Network Audit Report", "rights": "Audit Authorization", "rights_text": "Assessment is performed only with written permission from the infrastructure owner.", "endpoint": "Endpoint malware scan", "enabled": "enabled", "disabled": "disabled", "malware": "Malware scan", "network": "Network", "date": "Date", "checked": "Checked ports", "top": "Highest-risk hosts", "risk": "Risk", "os": "OS", "av": "Antivirus", "actions": "Recommended actions", "no_critical": "No critical recommendations."},
        "ro": {"switch": "Limbă:", "title": "Raport de audit de rețea", "rights": "Drept de audit", "rights_text": "Auditul se execută doar cu acord scris din partea proprietarului infrastructurii.", "endpoint": "Endpoint malware scan", "enabled": "activ", "disabled": "inactiv", "malware": "Malware scan", "network": "Rețea", "date": "Data", "checked": "Porturi verificate", "top": "Gazde cu risc ridicat", "risk": "Risc", "os": "OS", "av": "Antivirus", "actions": "Acțiuni recomandate", "no_critical": "Nu există recomandări critice."},
    }

    severity = Counter(f.severity for h in reports for f in h.findings)
    top_ports = Counter(f"{f.port}/tcp" for h in reports for f in h.findings)
    recs = sorted({f.recommendation for h in reports for f in h.findings if f.recommendation})

    def render(lang: str) -> str:
        cards = []
        for h in reports[:10]:
            cards.append(
                "<div class='card'>"
                f"<h4>{html.escape(h.ip)}</h4>"
                f"<p><b>{tr[lang]['risk']}:</b> {h.risk_score}</p>"
                f"<p><b>{tr[lang]['os']}:</b> {html.escape(h.probable_os)} ({html.escape(h.os_confidence)})</p>"
                f"<p><b>{tr[lang]['av']}:</b> {html.escape(h.antivirus_status)}</p>"
                f"<p><b>{tr[lang]['malware']}:</b> {html.escape(h.malware_scan_status)} — {html.escape(h.malware_scan_summary)}</p>"
                "</div>"
            )

        rec_html = "".join(f"<li>{html.escape(r)}</li>" for r in recs) if recs else f"<li>{tr[lang]['no_critical']}</li>"
        return f"""
<section class='lang-content' id='lang-{lang}' style='display:{'block' if lang == 'ru' else 'none'};'>
  <h1>{tr[lang]['title']}</h1>
  <p>{tr[lang]['network']}: <b>{html.escape(cidr)}</b> | {tr[lang]['checked']}: <b>{len(ports)}</b> | {tr[lang]['date']}: <b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</b></p>
  <div class='rights'><b>{tr[lang]['rights']}.</b> {tr[lang]['rights_text']}</div>
  <div class='rights'><b>{tr[lang]['endpoint']}:</b> {tr[lang]['enabled'] if endpoint_cfg.enabled else tr[lang]['disabled']} {f'({html.escape(endpoint_cfg.user)})' if endpoint_cfg.user else ''}</div>
  <div class='card'>{_bar_rows('Risk levels', dict(severity), '#0f3c7a')}</div>
  <div class='card'>{_bar_rows('Top ports', dict(top_ports.most_common(10)), '#f2d21b')}</div>
  <h2>{tr[lang]['top']}</h2><div class='grid'>{''.join(cards) if cards else '<div class="card">-</div>'}</div>
  <h2>{tr[lang]['actions']}</h2><div class='card'><ul>{rec_html}</ul></div>
</section>
"""

    html_doc = f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<style>
:root{{--brand-blue:#0f3c7a;--brand-yellow:#f2d21b;}} body{{font-family:Arial;margin:0;background:#f3f6fb;color:#123;}}
.top{{background:#fff;padding:14px 20px;border-bottom:1px solid #d8e3f1;display:flex;justify-content:space-between;align-items:center;}}
.logo{{font-size:36px;font-weight:700;color:#1857a4;}} .wrap{{max-width:1200px;margin:0 auto;padding:16px;}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;}}
.card{{background:#fff;border:1px solid #e7edf4;border-radius:12px;padding:12px;box-shadow:0 2px 8px rgba(10,37,64,.08);margin-top:10px;}}
.rights{{background:#fffbe7;border-left:4px solid var(--brand-yellow);padding:10px;border-radius:8px;margin:10px 0;}}
.bar-row{{margin:8px 0;}} .bar-track{{height:10px;background:#e9eff7;border-radius:6px;}} .bar-fill{{height:10px;border-radius:6px;}}
.lang-btn{{border:1px solid #c8d6e7;background:#fff;border-radius:8px;padding:6px 10px;cursor:pointer;}} .lang-btn.active{{background:#1857a4;color:#fff;}}
</style></head><body>
<div class='top'><div class='logo'>comoda</div><div><b id='lang-label'>{tr['ru']['switch']}</b> <button class='lang-btn active' data-lang='ru'>RU</button> <button class='lang-btn' data-lang='en'>EN</button> <button class='lang-btn' data-lang='ro'>RO</button></div></div>
<div class='wrap'>{render('ru')}{render('en')}{render('ro')}</div>
<script>
const labels={{ru:'{tr['ru']['switch']}',en:'{tr['en']['switch']}',ro:'{tr['ro']['switch']}'}};const bs=document.querySelectorAll('.lang-btn');const ss=document.querySelectorAll('.lang-content');const lb=document.getElementById('lang-label');
bs.forEach(b=>b.addEventListener('click',()=>{{const l=b.dataset.lang;ss.forEach(s=>s.style.display=s.id===('lang-'+l)?'block':'none');bs.forEach(x=>x.classList.toggle('active',x===b));lb.textContent=labels[l]||labels.ru;}}));
</script></body></html>"""
    target.write_text(html_doc, encoding="utf-8")


def print_console_summary(reports: list[HostReport]) -> None:
    if not reports:
        print("[i] Активные хосты с открытыми портами не найдены.")
        return
    print(f"[+] Найдено активных узлов: {len(reports)}")
    for h in reports:
        print(f"\nХост: {h.ip} | Risk: {h.risk_score} | OS: {h.probable_os}/{h.os_confidence}")
        print(f"    AV: {h.antivirus_status}")
        print(f"    Malware scan: {h.malware_scan_status} | {h.malware_scan_summary}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Локальный аудит сети (аналог Nessus Expert, без эксплуатации).")
    p.add_argument("cidr", nargs="?", help="CIDR подсеть, например 192.168.1.0/24 (если не указать, будет автоопределение /24)")
    p.add_argument("--ports", default=None, help="Порты: '22,80,443,3389' или диапазоны '1-1024,3306'")
    p.add_argument("--timeout", type=float, default=0.8, help="Таймаут сокета в секундах")
    p.add_argument("--workers", type=int, default=128, help="Количество потоков")
    p.add_argument("--out", default="audit_report.json", help="Путь для JSON отчёта")
    p.add_argument("--human-out", default="audit_report_human.html", help="Путь для визуального HTML-отчёта")
    p.add_argument("--endpoint-mode", action="store_true", help="Включить endpoint malware scan (вариант B, с доступом)")
    p.add_argument("--endpoint-user", default=None, help="Пользователь для SSH endpoint-проверки (Linux)")
    p.add_argument("--endpoint-timeout", type=float, default=5.0, help="Таймаут endpoint-проверки")
    return p


def main() -> int:
    p = build_parser()
    args = p.parse_args()
    try:
        ports = parse_ports(args.ports)
        cidr = args.cidr or detect_local_cidr()
    except ValueError as exc:
        p.error(str(exc))
        return 2

    endpoint_cfg = EndpointScanConfig(enabled=args.endpoint_mode, user=args.endpoint_user, timeout=args.endpoint_timeout)
    reports = scan_network(cidr, ports, timeout=args.timeout, workers=args.workers, endpoint_cfg=endpoint_cfg)

    if args.cidr is None:
        print(f"[i] Параметр cidr не указан, используется автоопределение: {cidr}")

    print_console_summary(reports)
    save_report(reports, Path(args.out), cidr, ports, endpoint_cfg)
    save_human_report(reports, Path(args.human_out), cidr, ports, endpoint_cfg)
    print(f"\n[+] JSON-отчёт: {Path(args.out).resolve()}")
    print(f"[+] HTML-отчёт: {Path(args.human_out).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
