# Python-инструмент аудита локальной сети (аналог Nessus Expert)

> ⚠️ Используйте только при наличии официального разрешения на аудит.

## Что делает скрипт

- обнаруживает активные хосты в подсети;
- проверяет открытые TCP-порты и баннеры;
- считает risk score;
- оценивает вероятную ОС;
- показывает AV-видимость (network-only);
- поддерживает **Вариант B**: endpoint malware scan при наличии доступа;
- формирует JSON и фирменный HTML-отчёт.

## Запуск

```bash
python3 audit_tool.py 192.168.1.0/24
```

### Вариант B (endpoint malware scan)

```bash
python3 audit_tool.py 192.168.1.0/24 \
  --endpoint-mode \
  --endpoint-user audit
```

> Текущая реализация endpoint-режима автоматизирована для Linux по SSH (BatchMode/ключи).
> Для Windows нужен агентный путь (WinRM/WMI/EDR), это отражается в отчёте как limitation.

## Аргументы

- `cidr` — подсеть в формате CIDR (необязательный);
- `--ports` — список портов/диапазонов;
- `--timeout` — таймаут сокета;
- `--workers` — количество потоков;
- `--out` — путь к JSON отчёту;
- `--human-out` — путь к HTML отчёту;
- `--endpoint-mode` — включить endpoint malware scan;
- `--endpoint-user` — пользователь для SSH endpoint-проверки;
- `--endpoint-timeout` — таймаут endpoint-проверки.

## Ограничения

- это defensive network-аудит, не полная замена enterprise-сканерам;
- malware scan без endpoint-доступа не даёт достоверного результата;
- для Windows endpoint malware scan нужен WinRM/WMI/EDR.

## Зависимости

Дополнительные библиотеки не нужны (стандартная библиотека Python).


## AuditorOS ISO (отдельная ОС для аудитора)

В репозитории добавлен каталог `auditor_os/` с каркасом для сборки ISO-образа отдельной ОС аудитора:
- сборка ISO через `live-build`;
- преднастройка security toolchain;
- launcher `auditorctl`;
- локальная dashboard-страница отчётов.

- SQLite Scan Library (в AuditorOS) + dashboard со списком запусков;
- installable ISO workflow для установки на обычный ПК (как Windows/Ubuntu).

Смотрите: `auditor_os/README.md`, `auditor_os/FEATURE_MATRIX.md` и `auditor_os/INSTALL_ANY_PC.md`.
