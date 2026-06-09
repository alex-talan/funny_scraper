# Introduction
- Scraper: [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#api-documentation)
- Email Server: [aiosmtpd](https://realpython.com/python-send-email/)
- LangChain & LangGraph

# Setup for Google SMTP server
Go to https://myaccount.google.com/apppasswords and create an application password to configure SMTP_PASSWORD env variable.

# Setup
```sh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

# Environment variables

Configure your `.env` file as follows: 

| Name | Secret | Description | Default |
|------|--------|-------------|---------|
|NEWS_LIMIT| |Number of news to scrap from the site|3|
|MAX_ATTEMPTS| |Maximum number of funny generation attempts|3| 
|OPENROUTER_API_KEY|X|OpenRouter API key ^^| |
|DEFAULT_MODEL_NAME| |Generation model name|google/gemma-4-31b-it|
|JUDGE_MODEL_NAME| |Model use for the judgement process|openai/gpt-4.1-mini|
|LANGSMITH_KEY|X|LangSmith platform API key to load prompts| |
|SMTP_HOST| |SMTP Server name|smtp.gmail.com|
|SMTP_PORT| |SMTP Server port|587|
|SMTP_USERNAME| |Sender username (usually the same as email)| |
|SMTP_PASSWORD|X|Sender email application password| |
|EMAIL_FROM| |Sender email| |
|EMAIL_TO| |Recipient email| |

# Run
```sh
python main.py
```