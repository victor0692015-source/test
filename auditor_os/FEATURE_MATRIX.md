# AuditorOS feature matrix (from requested scanner capabilities)

| Feature | Status in this repo | Planned backend/tools |
|---|---|---|
| Attack Surface Discovery | Planned | Amass/Subfinder + DNS/ASN enrichment |
| Host Discovery | Ready (current `audit_tool.py`) | TCP/ARP discovery |
| Ping-Only Discovery | Planned | ICMP/ARP lightweight scan mode |
| Basic Network Scan | Ready (baseline) | Multi-thread TCP + banners + risk score |
| Credential Validation | Planned | SSH/WinRM auth check module |
| Advanced Scan | Planned | Profile-based port + plugin groups |
| Advanced Dynamic Scan | Planned | Policy-driven plugin resolver |
| Malware Scan | **Ready (Variant B, endpoint access)** | SSH endpoint checks, AV/EDR services |
| Mobile Device Scan | Planned | MDM API connectors |
| Web Application Tests | Planned | Nikto/Wapiti/Nuclei wrappers |
| Credentialed Patch Audit | Planned | Authenticated package/update inventory |
| Active Directory Starter Scan | Planned | LDAP/Kerberos/SMB checks |
| Find AI / LLM exposure | Planned | Prompt/API endpoint surface checks |
| Remote Monitoring & Management | Planned | RMM agent/service signature checks |
| Cryptographic Inventory | Planned | TLS versions/ciphers/certs inventory |
| Audit Cloud Infrastructure | Planned | CIS checks for cloud providers |
| Internal PCI Network Scan | Planned | PCI scan profile and evidence export |
| MDM Config Audit | Planned | MDM policy API audits |
| Offline Config Audit | Planned | Device config file/policy parser |
| PCI Quarterly External Scan | Planned | External profile + report templates |
| Policy Compliance Auditing | Planned | Baseline policies + remediation map |
| SCAP and OVAL Auditing | Planned | openscap + OVAL content |
| Scan Library Dashboard | Ready | SQLite + local web dashboard |
| Installable ISO for PCs | Ready (scaffold) | Debian Live installer workflow |

> "Ready" means implemented now in this repository; "Planned" means architecture and package/tooling prepared in AuditorOS baseline.
