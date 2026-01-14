"""
Run script - Execute from project root folder with enhanced features
"""

import sys
import os
import time
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Print application banner"""
    print("=" * 70)
    print("🚀 GMAIL TO GOOGLE SHEETS AUTOMATION")
    print("=" * 70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    print("=" * 70)

def check_environment():
    """Check if environment is properly set up"""
    print("\n🔍 Checking environment...")
    
    # Check folder structure
    if not os.path.exists('src'):
        print("❌ ERROR: 'src' folder not found")
        return False
    if not os.path.exists('credentials'):
        print("❌ ERROR: 'credentials' folder not found")
        return False
    
    print("✅ Folder structure: OK")
    
    # Check credentials
    if not os.path.exists('credentials/credentials.json'):
        print("❌ ERROR: credentials.json not found in credentials/ folder")
        print("   Create it from Google Cloud Console")
        return False
    
    print("✅ Credentials file: OK")
    
    # Check config
    try:
        import config
        print("✅ Config module: OK")
        
        # Check Sheet ID
        if config.SPREADSHEET_ID == 'YOUR_ACTUAL_SHEET_ID_HERE':
            print("❌ ERROR: Update SPREADSHEET_ID in config.py!")
            print("   Get it from Google Sheets URL")
            return False
        
        print(f"✅ Sheet ID: {config.SPREADSHEET_ID[:30]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def print_features_status():
    """Print status of all bonus features"""
    try:
        import config
        
        print("\n🎁 BONUS FEATURES STATUS:")
        print("  ├─ Subject Filtering:", "✅ ENABLED" if config.FILTER_ENABLED else "❌ Disabled")
        if config.FILTER_ENABLED and config.FILTER_KEYWORDS:
            print(f"  ├─ Filter Keywords: {', '.join(config.FILTER_KEYWORDS[:3])}...")
        
        print("  ├─ HTML Conversion:", "✅ Built-in")
        print("  ├─ Logging:", f"✅ ENABLED ({config.LOG_LEVEL})" if config.LOG_ENABLED else "❌ Disabled")
        print("  ├─ Retry Logic:", f"✅ ENABLED ({config.MAX_RETRIES} retries)" if config.RETRY_ENABLED else "❌ Disabled")
        
        # Check permissions
        has_modify = any('gmail.modify' in scope for scope in config.SCOPES)
        print("  ├─ Mark as Read:", "✅ Available" if has_modify else "⚠️ Limited (read-only)")
        print("  └─ State Management:", "✅ Active (prevents duplicates)")
        
    except:
        print("  └─ Unable to load feature status")

def main():
    """Main execution function"""
    print_banner()
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix issues above.")
        return 1
    
    # Print features status
    print_features_status()
    
    # Initialize logger early
    try:
        from src.logger import logger
        logger.info("=" * 60)
        logger.info("Application started")
        logger.info(f"Working directory: {os.getcwd()}")
    except Exception as e:
        print(f"\n⚠️ Logger initialization failed: {e}")
        print("Continuing with basic logging...")
    
    print("\n" + "=" * 70)
    print("🚀 Starting email processing...")
    print("=" * 70 + "\n")
    
    # Run main program
    start_time = time.time()
    
    try:
        from src.main import main as process_emails
        result = process_emails()
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("\nPossible solutions:")
        print("1. Run from project root folder (contains src/ and credentials/)")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Check src/__init__.py exists (can be empty)")
        return 1
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Final summary
    end_time = time.time()
    elapsed = end_time - start_time
    
    print("\n" + "=" * 70)
    print(f"🏁 PROGRAM FINISHED")
    print("=" * 70)
    print(f"Total execution time: {elapsed:.2f} seconds")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        import config
        if config.LOG_ENABLED and config.LOG_FILE and os.path.exists(config.LOG_FILE):
            print(f"Log file: {config.LOG_FILE}")
            # Show last few log entries
            try:
                with open(config.LOG_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-5:]
                    if lines:
                        print("Recent log entries:")
                        for line in lines:
                            print(f"  {line.strip()}")
            except:
                pass
    except:
        pass
    
    print("=" * 70)
    
    return 0 if result > 0 else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️ Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)