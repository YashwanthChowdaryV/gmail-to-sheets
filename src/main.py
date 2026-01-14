"""
Main script - Orchestrates Gmail to Sheets automation with all bonus features
"""

import json
import os
import time
from datetime import datetime

# Import modules
from .gmail_service import GmailService
from .sheets_service import SheetsService
from .email_parser import EmailParser
from .logger import logger

class EmailToSheets:
    """Main orchestrator with all bonus features"""
    
    def __init__(self):
        logger.info("=" * 60)
        logger.info("Initializing Email to Sheets Processor")
        logger.info("=" * 60)
        
        self.gmail = None
        self.sheets = None
        self.parser = EmailParser()
        self.state = self._load_state()
        
        # Statistics
        self.stats = {
            'emails_processed': 0,
            'emails_filtered': 0,
            'rows_added': 0,
            'emails_marked_read': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _load_state(self):
        """Load processed email IDs from state file"""
        import config
        if os.path.exists(config.STATE_FILE):
            try:
                with open(config.STATE_FILE, 'r') as f:
                    data = json.load(f)
                
                processed_count = len(data.get('processed_ids', []))
                last_updated = data.get('last_updated', 'Never')
                
                logger.info(f"Loaded state file: {processed_count} processed emails")
                logger.info(f"Last updated: {last_updated}")
                
                return set(data.get('processed_ids', []))
                
            except Exception as e:
                logger.error(f"Error loading state file: {e}")
                logger.info("Creating new state file")
                return set()
        else:
            logger.info("No state file found, starting fresh")
            return set()
    
    def _save_state(self):
        """Save processed email IDs to state file"""
        import config
        state_data = {
            'processed_ids': list(self.state),
            'total_processed': len(self.state),
            'last_updated': datetime.now().isoformat(),  # ISO format is JSON serializable
            'last_run_stats': {
                'emails_processed': self.stats['emails_processed'],
                'emails_filtered': self.stats['emails_filtered'],
                'rows_added': self.stats['rows_added'],
                'emails_marked_read': self.stats['emails_marked_read'],
                'start_time': self.stats['start_time'].isoformat() if self.stats['start_time'] else None,
                'end_time': self.stats['end_time'].isoformat() if self.stats['end_time'] else None
            }
        }
        
        try:
            with open(config.STATE_FILE, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            logger.info(f"State saved: {len(self.state)} processed emails")
            
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    def _should_process_email(self, parsed_email):
        """Apply subject filtering - Bonus Feature"""
        import config
        
        if not config.FILTER_ENABLED or not config.FILTER_KEYWORDS:
            return True, []
        
        should_process = self.parser.filter_by_subject(parsed_email, config.FILTER_KEYWORDS)
        keywords_found = self.parser.extract_keywords(parsed_email, config.FILTER_KEYWORDS)
        
        if keywords_found:
            logger.debug(f"Email filtered IN - Keywords: {', '.join(keywords_found)}")
        elif config.FILTER_ENABLED:
            logger.debug(f"Email filtered OUT - No keywords found")
        
        return should_process, keywords_found
    
    def process_emails(self):
        """Main processing function with all bonus features"""
        self.stats['start_time'] = datetime.now()
        logger.info(f"Processing started at: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Initialize services
        logger.info("Initializing services...")
        self.gmail = GmailService()
        self.sheets = SheetsService()
        
        import config
        
        # Test Sheets connection
        if not self.sheets.test_connection():
            logger.error("Failed to connect to Google Sheets. Exiting.")
            return 0
        
        # Step 1: Fetch unread emails
        logger.info("Step 1: Fetching unread emails...")
        emails = self.gmail.fetch_unread_emails(config.MAX_EMAILS)
        
        if not emails:
            logger.info("No new unread emails found.")
            return 0
        
        logger.info(f"Found {len(emails)} unread email(s)")
        
        # Step 2: Parse and filter emails
        logger.info("Step 2: Parsing and filtering emails...")
        email_data = []
        emails_to_mark_read = []
        filtered_out_emails = []
        
        for i, email in enumerate(emails, 1):
            msg_id = email.get('id', 'unknown')
            
            # Skip already processed
            if msg_id in self.state:
                logger.debug(f"Skipping already processed: {msg_id[:10]}...")
                continue
            
            # Parse email
            parsed = self.parser.parse_email_message(email)
            if not parsed:
                logger.warning(f"Failed to parse email: {msg_id[:10]}...")
                continue
            
            # Apply filtering (Bonus Feature)
            should_process, keywords_found = self._should_process_email(parsed)
            
            if should_process:
                # Add keywords to data (Bonus Feature)
                if keywords_found:
                    parsed['keywords'] = ', '.join(keywords_found)
                    parsed['filtered'] = True
                
                email_data.append(parsed)
                emails_to_mark_read.append(msg_id)
                self.state.add(msg_id)
                
                # Log processing
                sender_short = parsed.get('sender', 'Unknown')[:20]
                subject_short = parsed.get('subject', 'No Subject')[:30]
                logger.info(f"✓ Processing email {i}: {sender_short} - {subject_short}...")
                
            else:
                filtered_out_emails.append(parsed)
                self.stats['emails_filtered'] += 1
                logger.debug(f"✗ Filtered out: {parsed.get('subject', 'No Subject')[:30]}...")
            
            # Limit processing
            if len(email_data) >= config.MAX_EMAILS:
                logger.info(f"Reached maximum processing limit ({config.MAX_EMAILS})")
                break
        
        self.stats['emails_processed'] = len(email_data)
        
        if filtered_out_emails:
            logger.info(f"Filtered out {len(filtered_out_emails)} email(s) based on keywords")
        
        if not email_data:
            logger.info("No new emails to process after filtering")
            return 0
        
        logger.info(f"Parsed {len(email_data)} new email(s) for processing")
        
        # Step 3: Format for Sheets
        logger.info("Step 3: Formatting for Google Sheets...")
        sheets_rows = []
        for data in email_data:
            row = self.parser.format_for_sheets(data)
            if row and len(row) >= 4:
                # Add keywords column if enabled (Bonus Feature)
                if config.FILTER_ENABLED and 'keywords' in data:
                    row.append(data['keywords'])  # Add as column E
                sheets_rows.append(row)
        
        if not sheets_rows:
            logger.warning("No valid data to send to Sheets")
            return 0
        
        # Step 4: Send to Google Sheets
        logger.info(f"Step 4: Sending {len(sheets_rows)} rows to Google Sheets...")
        rows_added = self.sheets.append_emails(sheets_rows)
        self.stats['rows_added'] = rows_added
        
        # Step 5: Mark emails as read
        if emails_to_mark_read and config.SCOPES and 'gmail.modify' in ' '.join(config.SCOPES):
            logger.info(f"Step 5: Marking {len(emails_to_mark_read)} emails as read...")
            marked_count = self.gmail.mark_multiple_as_read(emails_to_mark_read)
            self.stats['emails_marked_read'] = marked_count
            logger.info(f"Marked {marked_count} emails as read")
        else:
            logger.warning("Skipping mark-as-read: Insufficient permissions or no emails")
            self.stats['emails_marked_read'] = 0
        
        # Step 6: Save state
        logger.info("Step 6: Saving processing state...")
        self._save_state()
        
        # Final statistics
        self.stats['end_time'] = datetime.now()
        processing_time = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info("=" * 60)
        logger.info("✅ PROCESSING COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"📊 Execution Statistics:")
        logger.info(f"   • Processing time: {processing_time:.2f} seconds")
        logger.info(f"   • Emails fetched: {len(emails)}")
        logger.info(f"   • Emails processed: {self.stats['emails_processed']}")
        logger.info(f"   • Emails filtered out: {self.stats['emails_filtered']}")
        logger.info(f"   • Rows added to Sheet: {self.stats['rows_added']}")
        logger.info(f"   • Emails marked read: {self.stats['emails_marked_read']}")
        logger.info(f"   • Total processed (all time): {len(self.state)}")
        logger.info("=" * 60)
        
        # Summary for console
        print(f"\n🎉 Summary: Processed {self.stats['emails_processed']} emails, "
              f"added {self.stats['rows_added']} rows to Google Sheets")
        
        return self.stats['rows_added']


def main():
    """Main entry point with comprehensive error handling"""
    try:
        processor = EmailToSheets()
        result = processor.process_emails()
        return result
        
    except KeyboardInterrupt:
        logger.warning("⚠️ Process interrupted by user")
        print("\n⏹️ Process interrupted by user")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration error: {e}")
        print("Please check that credentials.json exists in credentials/ folder")
        return 0
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"\n❌ Import error: {e}")
        print("Make sure all required packages are installed:")
        print("  pip install -r requirements.txt")
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error in main process: {e}", exc_info=True)
        print(f"\n❌ Unexpected error: {e}")
        print("Check the log file for details: email_processor.log")
        return 0