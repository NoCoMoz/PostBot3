from sheets_helper import SheetsHelper
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_connection():
    try:
        helper = SheetsHelper()
        print("Successfully connected to Google Sheets")
        
        # Try to setup the sheet
        helper.setup_sheet()
        print("Successfully setup sheet")
        
    except Exception as e:
        print(f"Error testing Google Sheets connection: {str(e)}")
        raise

if __name__ == '__main__':
    test_connection()
