# **Gmail to Google Sheets Automation System**

**Vankayalapati Yashwanth Kumar**  

## **Project Overview**
Python system that automatically transfers unread Gmail emails to Google Sheets using OAuth 2.0. Extracts sender, subject, date, and content from emails, organizes them into spreadsheet rows, and prevents duplicates through state management.

## **Features**

### **Core Features:**
- **OAuth 2.0 Authentication** - Secure login for Gmail and Sheets APIs
- **Fetch Unread Emails** - Retrieves only unread inbox emails
- **Email Parsing** - Extracts sender, subject, date, and plain text body
- **Google Sheets Integration** - Appends data as organized rows
- **State Management** - Prevents duplicate processing using `state.json`
- **Mark as Read** - Automatically marks processed emails as read

##  Bonus Features Implemented

### 1. Subject-Based Filtering
- Configurable keywords in `config.py`
- Processes only relevant emails

### 2. HTML to Plain Text Conversion  
- Handles rich HTML emails
- Clean text extraction with signature removal

### 3. Comprehensive Logging System
- Timestamped logs (console + file)
- UTF-8 support for international content
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)

### 4. Retry Logic for API Failures
- Exponential backoff (2s, 4s, 8s)
- Smart error handling (no retry on auth errors)
- Production-ready resilience

## 📊 Architecture Diagram

┌─────────────────────────────────────────────────────────────────────────┐
│                          SYSTEM ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐     ┌───────────────────┐     ┌──────────────┐         │
│  │   GMAIL     │     │   PYTHON SYSTEM   │     │ GOOGLE SHEETS│         │
│  │   API       │────▶│                   │────▶│    API       │         │
│  │             │     │  ┌─────────────┐  │     │              │         │
│  │ • Fetch     │     │  │   MAIN      │  │     │ • Append     │         │
│  │   Unread    │     │  │ CONTROLLER  │  │     │   Rows       │         │
│  │   Emails    │     │  └──────┬──────┘  │     │ • Update     │         │
│  │ • Mark as   │     │         │         │     │   Sheet      │         │
│  │   Read      │     │  ┌──────▼──────┐  │     │              │         │ 
│  │             │     │  │  GMAIL      │  │     │              │         │
│  └─────────────┘     │  │  SERVICE    │  │     └──────────────┘         │
│         ▲            │  │             │  │              ▲               │
│         │            │  └──────┬──────┘  │              │               │
│         │            │         │         │              │               │
│  ┌──────┴──────┐     │  ┌──────▼──────┐  │     ┌──────────────┐         │
│  │   OAuth     │     │  │   SHEETS    │  │     │ GOOGLE SHEET │         │
│  │   2.0       │◀────┤  │  SERVICE    │◀─┼─────│  (Output)    │         │
│  │  Flow       │     │  │             │  │     │              │         │
│  │             │     │  └──────┬──────┘  │     │ • From       │         │
│  │ • Browser   │     │         │         │     │ • Subject    │         │
│  │   Consent   │     │  ┌──────▼──────┐  │     │ • Date       │         │
│  │ • Token     │     │  │  EMAIL      │  │     │ • Content    │         │
│  │   Storage   │     │  │  PARSER     │  │     └──────────────┘         │
│  └─────────────┘     │  │             │  │                              │
│                      │  └──────┬──────┘  │     ┌──────────────┐         │
│                      │         │         │     │   STATE      │         │
│                      │  ┌──────▼──────┐  │     │  MANAGER     │         │
│                      │  │  LOGGER &   │  │     │              │         │
│                      │  │  RETRY      │  │     │ • state.json │         │
│                      │  │  LOGIC      │  │     │ • Tracks     │         │
│                      │  │  (Bonus)    │  │     │   processed  │         │
│                      │  └─────────────┘  │     │   emails     │         │
│                      │                   │     │ • Prevents   │         │
│                      └───────────────────┘     │   duplicates │         │
│                                                └──────────────┘         │
│                                                                         │
│  DATA FLOW:                                                             │
│  1. OAuth Auth → 2. Fetch Emails → 3. Parse → 4. Filter → 5. Append     │ 
│  6. Mark Read → 7. Update State → 8. Repeat (skips processed emails)    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

Architecture Image is in gmail-to-sheets/proof/


## ⚙️ Setup Instructions

### **Step 1: Clone and Setup**

```bash
git clone <repository-url>
cd gmail-to-sheets
pip install -r requirements.txt
```

### **Step 2: Google Cloud Console Setup**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project: `Gmail-Sheets-Automation`
3. Enable APIs: **Gmail API** and **Google Sheets API**
4. Configure OAuth Consent Screen:
   - User Type: External
   - App Name: `Email Logger`
   - Add your email as Test User
5. Create OAuth 2.0 Credentials:
   - Application Type: Desktop application
   - Name: `Email Logger Desktop`
   - Download `credentials.json` to `credentials/` folder

### **Step 3: Google Sheet Preparation**
1. Create a new Google Sheet
2. Add headers in Row 1: `From`, `Subject`, `Date`, `Content`
3. Get Sheet ID from URL: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`
4. Update `config.py` with your Sheet ID

### **Step 4: Configuration**
Update `config.py` with your settings:
```python
SPREADSHEET_ID = 'your_sheet_id_here'
FILTER_KEYWORDS = ['invoice', 'order', 'payment']  # Customize as needed
```

### **Step 5: Run the Application**
```bash
python run.py
```

## 🔐 Security & Credentials Management

**Important Security Rules:**
- `credentials/` folder is in `.gitignore`
- Never commit `credentials.json` or `token.pickle`
- OAuth tokens are stored locally with encryption
- All sensitive data is excluded from version control

## 🔄 OAuth Flow Explanation

### **Authentication Process:**
1. **Initial Run**: Browser opens for OAuth consent
2. **User Authorization**: Grant permissions to access Gmail and Sheets
3. **Token Generation**: Access and refresh tokens created
4. **Token Storage**: Securely saved as `token.pickle`
5. **Subsequent Runs**: Auto-refresh using stored tokens

### **Why OAuth 2.0 (not Service Account):**
- Required by assignment specifications
- More secure for user data access
- User consent is explicitly obtained
- Suitable for accessing personal Gmail accounts

## 💾 State Persistence & Duplicate Prevention

### **How State is Stored:**
```json
{
  "processed_ids": ["msg_id_1", "msg_id_2", ...],
  "total_processed": 50,
  "last_updated": "2024-01-13T18:32:44",
  "last_run_stats": {...}
}
```
### **Duplicate Prevention Logic:**
1. **Before Processing**: Check if email ID exists in `state.json`
2. **During Processing**: Skip already processed emails
3. **After Processing**: Add new email IDs to state
4. **State Persistence**: Save updated state to `state.json`

### **Why This Approach Was Chosen:**
- **Simple**: JSON file is human-readable and easy to debug
- **Reliable**: File-based storage works without external dependencies

## ⚡ What Happens When Script Runs Twice

### First Run:
1. **Authentication**: Browser opens for OAuth consent
2. **Email Fetching**: Retrieves up to `MAX_EMAILS` unread emails
3. **Processing**: Parses and appends to Google Sheets
4. **State Creation**: Creates `state.json` with processed email IDs

### Second Run:
- **Scenario A (No new emails)**: All fetched emails are in `state.json` → 0 rows added
- **Scenario B (More emails)**: Processes emails not in `state.json` → New rows added

### Key Guarantee:
Each email processed exactly once via `state.json` tracking.
Zero duplicates in spreadsheet guaranteed.


## Scalability Validation

Tested with Real Email Volumes:

5 emails: Perfect execution, all requirements met
50 emails: Flawless performance, efficient state tracking
100+ emails: Excellent scalability, zero duplicates maintained

Key Finding: The system reliably handles varying email volumes while guaranteeing zero duplicates through robust state management.


## 🚧 Challenges Faced & Solutions

### **Challenge 1: OAuth Consent Screen Verification**
**Problem**: Google blocking access with "App not verified" warning  
**Solution**: 
- Added email as Test User in OAuth consent screen
- Used "Advanced → Go to app (unsafe)" during testing
- Implemented proper error handling for consent flow

### **Challenge 2: Marking Emails as Read**
**Problem**: Insufficient authentication scopes error  
**Solution**:
- Added `https://www.googleapis.com/auth/gmail.modify` scope
- Regenerated OAuth tokens with new permissions
- Implemented retry logic for permission errors

### **Challenge 3: State File Corruption**
**Problem**: `state.json` corruption after datetime serialization error  
**Solution**:
- Used ISO format for datetime serialization
- Added robust error recovery
- Created fresh state file if corruption detected

### **Current Limitations:**
1. **Rate Limiting**: Google API quotas may limit large email volumes 
2. **Single Account**: Designed for single Gmail account access
3. **Basic Filtering**: Keyword-based only, no advanced filters
4. **No Attachment Handling**: Email attachments are ignored
5. **No Real-time Processing**: Manual execution required
6. **Single Threaded**: Processes emails sequentially




## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python run.py 
```

## Proof of Execution
Video and Screenshots available in /proof/ folder:

## Submission Details

Vankayalapati Yashwanth Kumar

23eg105t62@anurag.edu.in

9951810271

Git Link : https://github.com/YashwanthChowdaryV/gmail-to-sheets

