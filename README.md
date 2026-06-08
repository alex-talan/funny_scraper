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

# Environment variables

| Name | Secret | Description | Default |
|------|--------|-------------|---------|
|NEWS_LIMIT| |Number of news to scrap from the site|3|
|MAX_ATTEMPTS| |Maximum number of funny generation attempts|3| 
|OPENROUTER_API_KEY|X|OpenRouter API key ^^| |
|MODEL_NAME| |Model name|google/gemma-4-31b-it|
|LANGSMITH_KEY|X|LangSmith platform API key| |
|SMTP_HOST| |SMTP Server name|smtp.gmail.com|
|SMTP_PORT| |SMTP Server port|=587|
|SMTP_USERNAME| |Sender username (usually the same as email)| |
|SMTP_PASSWORD|X|Sender email application password| |
|EMAIL_FROM| |Sender email| |
|EMAIL_TO| |Recipient email| |

# Run
```sh
python main.py
```