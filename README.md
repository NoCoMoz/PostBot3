# Quiz Bot with Google Sheets Integration

A Telegram bot that conducts quizzes and saves responses to Google Sheets.

## Features

- Interactive quiz via Telegram
- Multiple choice and text questions
- Automatic response saving to Google Sheets
- Real-time response tracking
- Timestamp for each submission

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with:
```
BOT_TOKEN=your_telegram_bot_token
SPREADSHEET_ID=your_google_sheets_id
```

3. Add your Google Sheets service account JSON file as `service_account.json`

4. Share your Google Sheet with the service account email

5. Run the bot:
```bash
python main.py
```

## Usage

1. Start the bot with `/start`
2. Begin the quiz with `/quiz`
3. Answer all questions
4. Responses will be saved to your Google Sheet automatically

## Files

- `main.py`: Main bot code
- `sheets_helper.py`: Google Sheets integration
- `questions.json`: Quiz questions and options
- `test_sheets.py`: Test script for sheets setup
