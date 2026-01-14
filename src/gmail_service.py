"""
Gmail Service - Handles Gmail API authentication and operations with bonus features
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


class GmailService:
    """Service for Gmail API operations with retry logic and logging"""
    
    def __init__(self):
        """Initialize with authentication"""
        logger.info("Initializing Gmail Service...")
        self.service = self._authenticate()
        self.processed_ids = set()
        logger.info("Gmail Service ready")
    
    @retry_on_failure(max_retries=3, delay=2)
    def _authenticate(self):
        """Authenticate with Gmail API using OAuth 2.0 with retry"""
        creds = None
        token_path = 'credentials/token.pickle'
        
        # Load existing token
        if os.path.exists(token_path):
            try:
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
                logger.info("Loaded existing credentials from token.pickle")
            except Exception as e:
                logger.warning(f"Token file corrupted: {e}, creating new...")
                try:
                    os.remove(token_path)
                except:
                    pass
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials...")
                try:
                    creds.refresh(Request())
                    logger.info("Credentials refreshed successfully")
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None
        
        if not creds:
            logger.info("Starting OAuth authentication flow...")
            
            # Check credentials file
            if not os.path.exists('credentials/credentials.json'):
                error_msg = "credentials.json not found in credentials/ folder"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            # Import config for scopes
            import config
            logger.info("=" * 60)
            logger.info("REQUESTING THESE PERMISSIONS:")
            for scope in config.SCOPES:
                if 'gmail.modify' in scope:
                    logger.info(f"  • {scope} ← CRITICAL for marking emails as read")
                else:
                    logger.info(f"  • {scope}")
            logger.info("=" * 60)
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials/credentials.json',
                    config.SCOPES
                )
                logger.info("Opening browser for OAuth consent...")
                logger.info("Look for 'Manage your mail' permission in browser")
                creds = flow.run_local_server(port=0)
                
                # Verify we got modify scope
                if hasattr(creds, 'scopes'):
                    if 'https://www.googleapis.com/auth/gmail.modify' in creds.scopes:
                        logger.info("✅ Successfully obtained 'gmail.modify' permission")
                    else:
                        logger.warning("⚠️ 'gmail.modify' scope not in token. Emails won't be marked as read!")
                
                # Save credentials
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("Credentials saved to token.pickle")
                
            except Exception as e:
                logger.error(f"OAuth authentication failed: {e}")
                raise
        
        return build('gmail', 'v1', credentials=creds)
    
    @retry_on_failure(max_retries=2, delay=1)
    def fetch_unread_emails(self, max_results=50):
        """Fetch unread emails from Gmail inbox with retry logic"""
        try:
            import config
            
            logger.info(f"Fetching up to {max_results} unread emails...")
            
            # List messages
            start_time = time.time()
            results = self.service.users().messages().list(
                userId='me',
                q=config.GMAIL_QUERY,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            elapsed = time.time() - start_time
            
            if not messages:
                logger.info("No unread emails found.")
                return []
            
            logger.info(f"Found {len(messages)} unread email(s) in {elapsed:.2f}s")
            
            # Get full details
            email_details = []
            fetch_start = time.time()
            
            for i, msg in enumerate(messages, 1):
                message_id = msg['id']
                
                # Skip if already processed
                if message_id in self.processed_ids:
                    logger.debug(f"Skipping already processed email: {message_id[:10]}...")
                    continue
                
                try:
                    # Fetch individual email with retry
                    message = self._fetch_single_email(message_id)
                    if message:
                        email_details.append(message)
                        self.processed_ids.add(message_id)
                    
                    # Log progress every 10 emails
                    if i % 10 == 0:
                        logger.debug(f"Fetched {i}/{len(messages)} emails...")
                        
                except Exception as e:
                    logger.error(f"Error fetching email {message_id[:10]}...: {e}")
            
            fetch_elapsed = time.time() - fetch_start
            logger.info(f"Fetched details for {len(email_details)} emails in {fetch_elapsed:.2f}s")
            
            return email_details
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return []
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    @retry_on_failure(max_retries=2, delay=1)
    def _fetch_single_email(self, message_id):
        """Fetch single email with retry logic"""
        return self.service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
    
    @retry_on_failure(max_retries=3, delay=1)
    def mark_as_read(self, message_id):
        """Mark an email as read with retry logic - ARCHIVE VERSION"""
        try:
            # Remove UNREAD label AND INBOX label (archive it)
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD', 'INBOX']}  # Archive from inbox
            ).execute()
            
            # VERIFICATION: Check if email is actually marked as read and archived
            try:
                email = self.service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='metadata',
                    metadataHeaders=['LabelIds']
                ).execute()
                
                label_ids = email.get('labelIds', [])
                
                if 'UNREAD' not in label_ids and 'INBOX' not in label_ids:
                    logger.info(f"✅ VERIFIED: Email {message_id[:10]}... marked as read and archived")
                    return True
                elif 'UNREAD' not in label_ids:
                    logger.info(f"✅ Email {message_id[:10]}... marked as read (still in inbox)")
                    return True
                else:
                    logger.warning(f"⚠️ Email {message_id[:10]}... still has UNREAD label")
                    return False
                    
            except Exception as verify_error:
                logger.info(f"Marked email {message_id[:10]}... as read and archived")
                return True
                
        except HttpError as e:
            error_msg = str(e)
            logger.error(f"HTTP error marking email as read: {error_msg}")
            
            if "insufficient authentication scopes" in error_msg.lower():
                logger.error("❌ CRITICAL: Missing 'gmail.modify' scope!")
                logger.error("   Solution: Delete token.pickle and re-run for new permissions")
            
            return False
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return False
    
    def mark_multiple_as_read(self, message_ids):
        """Mark multiple emails as read with batch processing"""
        if not message_ids:
            return 0
        
        logger.info(f"Attempting to mark {len(message_ids)} emails as read...")
        success_count = 0
        failed_ids = []
        
        for i, msg_id in enumerate(message_ids, 1):
            if self.mark_as_read(msg_id):
                success_count += 1
            else:
                failed_ids.append(msg_id[:10])
            
            # Log progress
            if i % 10 == 0:
                logger.debug(f"Marked {i}/{len(message_ids)} emails as read...")
        
        if failed_ids:
            logger.warning(f"Failed to mark {len(failed_ids)} emails as read: {failed_ids[:5]}...")
        
        logger.info(f"Successfully marked {success_count}/{len(message_ids)} emails as read")
        return success_count
    
    @retry_on_failure(max_retries=2, delay=1)
    def get_email_count(self):
        """Get count of unread emails with retry logic"""
        try:
            import config
            results = self.service.users().messages().list(
                userId='me',
                q=config.GMAIL_QUERY,
                maxResults=1
            ).execute()
            
            count = results.get('resultSizeEstimate', 0)
            logger.info(f"Unread email count: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Error getting email count: {e}")
            return 0
    
    def check_modify_permission(self):
        """Check if we have permission to mark emails as read"""
        try:
            # Try a simple modify operation to check permissions
            test_result = self.service.users().messages().list(
                userId='me',
                q='in:inbox is:unread',
                maxResults=1
            ).execute()
            
            messages = test_result.get('messages', [])
            if messages:
                # Try to get label info (requires modify scope to see labels)
                msg = self.service.users().messages().get(
                    userId='me',
                    id=messages[0]['id'],
                    format='metadata',
                    metadataHeaders=['LabelIds']
                ).execute()
                
                logger.info("✅ Gmail modify permission confirmed")
                return True
        except HttpError as e:
            if "insufficient authentication scopes" in str(e).lower():
                logger.error("❌ Missing 'gmail.modify' permission")
                return False
        except Exception:
            pass
        
        return True
    
    def check_email_status(self, message_id):
        """Check current status of an email"""
        try:
            email = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='metadata',
                metadataHeaders=['LabelIds', 'From', 'Subject']
            ).execute()
            
            label_ids = email.get('labelIds', [])
            headers = email.get('payload', {}).get('headers', [])
            
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            
            return {
                'labels': label_ids,
                'from': from_header,
                'subject': subject,
                'is_unread': 'UNREAD' in label_ids,
                'in_inbox': 'INBOX' in label_ids,
                'categories': [l for l in label_ids if l.startswith('CATEGORY_')]
            }
        except Exception as e:
            logger.error(f"Error checking email status: {e}")
            return None