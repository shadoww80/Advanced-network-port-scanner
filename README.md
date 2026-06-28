# Advanced Network Port Scanner

A production-quality desktop TCP port scanner built with Python and CustomTkinter. Features a modern dark cybersecurity UI, multi-threaded scanning, service detection, banner grabbing, and CSV export.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Modern dark UI** — Cyber-security themed interface powered by CustomTkinter
- **TCP port scanning** — Concurrent scanning via `ThreadPoolExecutor` (100 workers)
- **IP & domain support** — Resolves hostnames automatically
- **Configurable port range** — Start and end port inputs (1–65535)
- **Live progress bar** — Real-time scan completion percentage
- **Results table** — Treeview with port, status, service, response time, and banner
- **Service detection** — Identifies 40+ common services by port number
- **Banner grabbing** — HTTP(S), SSH, FTP, SMTP, POP3, IMAP, and Telnet
- **Open port counter** — Live count of discovered open ports
- **Stop scan** — Gracefully cancel an in-progress scan
- **Export CSV** — Save results to a timestamped CSV file
- **Clear results** — Reset the table and counters
- **Thread-safe GUI** — All UI updates marshalled through `after()`

## Project Structure

```
Advanced-Network-Port-Scanner/
├── main.py                     # Application entry point
├── ui.py                       # Compatibility shim
├── scanner.py                  # Compatibility shim
├── banner.py                   # Compatibility shim
├── requirements.txt
├── README.md
└── portscanner/                # Application package
    ├── __init__.py
    ├── __main__.py             # python -m portscanner
    ├── constants.py            # Shared constants
    ├── types.py                # Callback type aliases
    ├── core/
    │   └── scanner.py          # PortScanner engine
    ├── network/
    │   ├── banner.py           # BannerGrabber
    │   ├── resolver.py         # Host resolution
    │   ├── services.py         # Well-known port mappings
    │   └── socket_utils.py     # Shared socket helpers
    └── ui/
        ├── app.py              # PortScannerApp window
        └── theme.py            # Color palette
```

## Requirements

- Python 3.9 or later
- Windows, macOS, or Linux

## Installation

1. Clone or download this repository.

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python main.py
```

Alternative entry points:

```bash
python -m portscanner
```

1. Enter a **target** — IP address (e.g. `192.168.1.1`) or domain (e.g. `scanme.nmap.org`)
2. Set **Start Port** and **End Port** (defaults: 1–1024)
3. Click **Start Scan**
4. Review open ports in the results table
5. Use **Export CSV** to save results, or **Clear** to reset

> **Note:** Only scan networks and hosts you own or have explicit permission to test. Unauthorized port scanning may violate laws or policies.

## Architecture

| Module | Responsibility |
|--------|----------------|
| `portscanner/ui/app.py` | Window layout, user actions, thread-safe UI updates |
| `portscanner/core/scanner.py` | Scan orchestration, worker pool, progress throttling |
| `portscanner/network/banner.py` | Protocol-aware banner grabbing on open sockets |
| `portscanner/network/resolver.py` | IPv4 validation and DNS resolution |
| `portscanner/network/services.py` | Well-known port-to-service mappings |

The scanner runs on a background thread. Worker threads publish results through callbacks that schedule GUI updates on the main thread via `tkinter.after()`.

## License

MIT License — use responsibly and only on authorized targets.
