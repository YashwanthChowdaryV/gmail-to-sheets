# === OAuth Scopes ===
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',   # For marking emails as read
    'https://www.googleapis.com/auth/spreadsheets'
]

# === Gmail Settings ===
GMAIL_QUERY = 'in:inbox is:unread'
MAX_EMAILS = 5

# === Google Sheets Settings ===
SPREADSHEET_ID = '1pnY5TnVU6PKm7Gn5hvhm6lZTxMrU8UUKiV1J2j6MN48'  # Replace with your actual ID
SHEET_NAME = 'Sheet1'
SHEET_RANGE = 'A:D'

# === State Management ===
STATE_FILE = 'state.json'

# 1. Subject Filtering
FILTER_ENABLED = False
FILTER_KEYWORDS = ['invoice', 'order', 'payment', 'quote']

# 2. Logging
LOG_ENABLED = True
LOG_FILE = 'email_processor.log'
LOG_LEVEL = 'INFO'  # Options: DEBUG, INFO, WARNING, ERROR

# 3. Retry Logic
RETRY_ENABLED = True
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds 