"""
Google Sheets Service - Handles Google Sheets API operations with bonus features
"""

import os
import pickle
import time
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.retry_logic import retry_on_failure
from src.logger import logger


class SheetsService:
    """Service for Google Sheets operations with retry logic and logging"""
    
    def __init__(self):
        """Initialize with authentication"""
        logger.info("Initializing Sheets Service...")
        self.service = self._authenticate()
        import config
        self.spreadsheet_id = config.SPREADSHEET_ID
        logger.info(f"Sheets service ready for spreadsheet: {self.spreadsheet_id[:30]}...")
    
    @retry_on_failure(max_retries=3, delay=2)
    def _authenticate(self):
        """Authenticate with Sheets API with retry logic"""
        creds = None
        token_path = 'credentials/token.pickle'
        
        # Load existing token
        if os.path.exists(token_path):
            try:
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
                logger.debug("Loaded credentials for Sheets")
            except Exception as e:
                logger.warning(f"Error loading token: {e}")
        
        # Refresh or re-authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing Sheets credentials...")
                try:
                    creds.refresh(Request())
                    logger.info("Sheets credentials refreshed")
                except Exception as e:
                    logger.error(f"Failed to refresh Sheets credentials: {e}")
                    creds = None
            
            if not creds:
                logger.info("Authenticating for Sheets API...")
                import config
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials/credentials.json',
                    config.SCOPES
                )
                creds = flow.run_local_server(port=0)
                
                # Save token
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("Sheets authentication complete")
        
        return build('sheets', 'v4', credentials=creds)
    
    @retry_on_failure(max_retries=3, delay=1)
    def append_emails(self, email_rows):
        """
        Append email data to Google Sheet with retry logic
        
        Args:
            email_rows: List of lists [[From, Subject, Date, Content], ...]
            
        Returns:
            Number of rows added
        """
        if not email_rows:
            logger.info("No emails to add to sheet")
            return 0
        
        try:
            import config
            
            logger.info(f"Preparing to append {len(email_rows)} rows to Google Sheet...")
            start_time = time.time()
            
            # Prepare data
            body = {'values': email_rows}
            
            # Determine range based on number of columns
            num_columns = len(email_rows[0]) if email_rows else 4
            sheet_range = f"{config.SHEET_NAME}!A:{chr(64 + min(num_columns, 26))}"
            
            # Append to sheet
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_range,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            elapsed = time.time() - start_time
            updated = result.get('updates', {}).get('updatedRows', len(email_rows))
            
            logger.info(f"✅ Added {updated} rows to Google Sheet in {elapsed:.2f}s")
            
            # Log sample data
            if email_rows and len(email_rows) > 0:
                sample = email_rows[0]
                logger.debug(f"Sample row: From={sample[0][:20]}..., Subject={sample[1][:30]}...")
            
            return updated
            
        except HttpError as error:
            logger.error(f"Sheets API error: {error}")
            
            # Provide helpful error messages
            if "Unable to parse range" in str(error):
                logger.error("Check SHEET_NAME in config.py - sheet might not exist")
            elif "The caller does not have permission" in str(error):
                logger.error("No permission to access this spreadsheet. Check sharing settings.")
            
            return 0
        except Exception as e:
            logger.error(f"Error appending to Sheets: {e}")
            return 0
    
    @retry_on_failure(max_retries=2, delay=1)
    def get_last_row_number(self):
        """Get the last row number with data in sheet"""
        try:
            import config
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{config.SHEET_NAME}!A:A"
            ).execute()
            
            values = result.get('values', [])
            row_count = len(values)
            logger.debug(f"Sheet currently has {row_count} rows")
            return row_count
            
        except Exception as e:
            logger.warning(f"Could not get row count: {e}")
            return 0
    
    @retry_on_failure(max_retries=2, delay=1)
    def test_connection(self):
        """Test connection to Google Sheets"""
        try:
            import config
            
            logger.info("Testing Google Sheets connection...")
            result = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            title = result.get('properties', {}).get('title', 'Unknown')
            logger.info(f"Connected to spreadsheet: '{title}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            return False