from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SheetsHelper:
    def __init__(self):
        """Initialize the Google Sheets helper."""
        self.SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
        if not self.SPREADSHEET_ID:
            raise ValueError("SPREADSHEET_ID not found in environment variables")
            
        self.SHEET_NAME = 'Sheet1'  # Changed to Sheet1 since it's the default sheet
        
        try:
            # Load credentials
            logger.debug("Loading service account credentials...")
            creds = service_account.Credentials.from_service_account_file(
                'credentials/service_account.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            logger.info("Successfully loaded credentials")
            
            # Create service
            logger.debug("Initializing Google Sheets service...")
            self.service = build('sheets', 'v4', credentials=creds)
            self.sheet = self.service.spreadsheets()
            logger.info("Successfully initialized Google Sheets service")
            
        except Exception as e:
            logger.error(f"Failed to initialize sheets helper: {str(e)}")
            raise
            
    def setup_sheet(self, force_recreate=False):
        """Create Responses sheet if it doesn't exist and set up headers."""
        try:
            # Get spreadsheet info
            spreadsheet = self.sheet.get(spreadsheetId=self.SPREADSHEET_ID).execute()
            sheets = spreadsheet.get('sheets', [])
            sheet_names = [s['properties']['title'] for s in sheets]
            
            # Delete sheet if force recreate
            if force_recreate and self.SHEET_NAME in sheet_names:
                # Get sheet ID
                sheet_id = None
                for s in sheets:
                    if s['properties']['title'] == self.SHEET_NAME:
                        sheet_id = s['properties']['sheetId']
                        break
                        
                if sheet_id:
                    # Delete sheet
                    body = {
                        'requests': [{
                            'deleteSheet': {
                                'sheetId': sheet_id
                            }
                        }]
                    }
                    self.sheet.batchUpdate(
                        spreadsheetId=self.SPREADSHEET_ID,
                        body=body
                    ).execute()
                    sheet_names.remove(self.SHEET_NAME)
                    
            # Create sheet if it doesn't exist
            if self.SHEET_NAME not in sheet_names:
                body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': self.SHEET_NAME
                            }
                        }
                    }]
                }
                self.sheet.batchUpdate(
                    spreadsheetId=self.SPREADSHEET_ID,
                    body=body
                ).execute()
                
            # Load questions to get headers
            with open('questions.json', 'r', encoding='utf-8') as f:
                questions = json.load(f)['quiz']
                
            # Create headers
            headers = [
                'Timestamp',
                'Telegram Username',
                'Telegram User ID'
            ]
            
            # Add question headers
            for q in questions:
                headers.append(q['question'])
                
            # Update headers in sheet
            body = {
                'values': [headers]
            }
            self.sheet.values().update(
                spreadsheetId=self.SPREADSHEET_ID,
                range=f'{self.SHEET_NAME}!A1:ZZ1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info("Sheet setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup sheet: {str(e)}")
            return False
            
    def append_row(self, row_data):
        """Append a row of data to the sheet."""
        try:
            body = {
                'values': [row_data]
            }
            self.sheet.values().append(
                spreadsheetId=self.SPREADSHEET_ID,
                range=f'{self.SHEET_NAME}!A1',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            logger.info("Successfully appended row to sheet")
            return True
            
        except Exception as e:
            logger.error(f"Failed to append row: {str(e)}")
            return False
