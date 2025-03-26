from sheets_helper import SheetsHelper
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_write():
    try:
        # Initialize sheets helper
        sheets = SheetsHelper()
        
        # Test data
        test_data = [
            "test_user",  # Username
            "2025-02-14 15:34:40",  # Timestamp
            "25",  # Age
            "Texas",  # State
            "Social Media",  # Source
            "Yes",  # Gov priority
            "Healthcare is a basic human right",  # Beliefs
            "Testing the form responses",  # Join reason
            "Low wages",  # Worker issues
            "Yes, and I would participate",  # Strike support
            "No, government should be separate from religion",  # Religion policy
            "The wealth gap is too large and must be addressed",  # Wealth inequality
            "1. Social media & content creation",  # Skills
            "Yes, I'm ready to lead",  # Leadership
            "Several hours/week",  # Time commitment
            "Yes, absolutely",  # Direct action
            "Yes, I can help with logistics and planning",  # Protest organize
            "Yes, and I can provide a link for verification",  # Social media
            "https://twitter.com/test",  # Social media link
            "1. Twitter/X",  # Social media platforms
            "Yes",  # Activist org
            "Yes",  # Encrypted communication
            "Yes, fully agree"  # Mission alignment
        ]
        
        # Write test data
        sheets.append_row(test_data)
        logger.info("Successfully wrote test data to sheet")
        
    except Exception as e:
        logger.error(f"Error writing test data: {str(e)}")
        raise

if __name__ == "__main__":
    test_write()
