# Introduction
Scraper: [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#api-documentation)
Email Server: [aiosmtpd](https://realpython.com/python-send-email/)

# Setup for Google SMTP server
Go to https://myaccount.google.com/apppasswords and create an application password to configure SMTP_PASSWORD env variable.

# Setup
```sh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

# Run

```sh
python main.py
```