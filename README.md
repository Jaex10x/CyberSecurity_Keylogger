# 🛡️ CyberSentinel - Ethical Keystroke Monitoring Suite

> **⚠️ IMPORTANT DISCLAIMER**: This tool is designed **exclusively** for authorized cybersecurity research, penetration testing, and educational purposes. Unauthorized use of this software to monitor individuals without their explicit consent is **illegal** and **unethical**. Always obtain proper authorization before deploying this tool.

---

## 📋 Overview

CyberSentinel is a professional-grade keystroke monitoring suite built for cybersecurity professionals and students. It features encrypted logging, real-time dashboard monitoring, system profiling, and comprehensive reporting capabilities.

## 🏗️ Project Structure

```
cybersentinel/
├── config/               # Configuration & settings
│   ├── __init__.py
│   └── settings.py       # Centralized configuration
├── core/                 # Core monitoring engines
│   ├── __init__.py
│   ├── keylogger.py      # Keystroke capture engine
│   ├── clipboard.py      # Clipboard monitoring
│   └── screenshot.py     # Screenshot capture
├── storage/              # Data persistence layer
│   ├── __init__.py
│   ├── file_handler.py   # Encrypted file storage
│   └── email_report.py   # Email-based reporting
├── ui/                   # User interface layer
│   ├── __init__.py
│   └── dashboard.py      # Rich terminal dashboard
├── utils/                # Utility modules
│   ├── __init__.py
│   ├── encryption.py     # Fernet encryption manager
│   ├── system_info.py    # System profiling
│   └── consent.py        # Ethical consent framework
├── tests/                # Unit tests
│   ├── __init__.py
│   └── test_core.py
├── logs/                 # Encrypted log output
├── main.py               # Application entry point
├── requirements.txt      # Dependencies
└── setup.py              # Package installer
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python main.py
```

### 3. Available Commands
| Command | Description |
|---------|------------|
| `python main.py --mode monitor` | Start real-time monitoring dashboard |
| `python main.py --mode stealth` | Start background monitoring |
| `python main.py --mode review` | Review encrypted logs |
| `python main.py --mode sysinfo` | Display system profile |
| `python main.py --mode decrypt` | Decrypt and export logs |

## 🔐 Security Features

- **AES-256 Encryption** via Fernet for all stored logs
- **Consent Verification** before any monitoring begins
- **Session-based Keys** with automatic rotation
- **Secure Deletion** of temporary files

## ⚖️ Ethical Use Policy

1. **Always obtain written consent** from the system owner
2. **Document your authorization** before deploying
3. **Limit data collection** to what is necessary
4. **Secure all collected data** and delete after analysis
5. **Report findings responsibly** through proper channels

## 📄 License

This project is licensed for **educational and authorized security testing only**.
