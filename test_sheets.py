from sheets_helper import SheetsHelper
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_sheets_connection():
    try:
        # Initialize sheets helper
        logger.info("Initializing sheets helper...")
        sheets = SheetsHelper()
        
        # Test setup
        logger.info("Testing sheet setup...")
        if sheets.setup_sheet():
            logger.info("✓ Sheet setup successful")
        else:
            logger.error("✗ Sheet setup failed")
            
        # Test row append
        logger.info("Testing row append...")
        test_row = ["Test Timestamp", "Test Username", "Test User ID", "Test Answer 1"]
        if sheets.append_row(test_row):
            logger.info("✓ Row append successful")
        else:
            logger.error("✗ Row append failed")
            
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    test_sheets_connection()
