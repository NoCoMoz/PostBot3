import logging
import sys
from telegram import Bot
from telegram.error import TelegramError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Bot token from config.py
from config import BOT_TOKEN

def test_connection():
    try:
        print(f"Using token ending with: ...{BOT_TOKEN[-4:]}")
        bot = Bot(token=BOT_TOKEN)
        me = bot.get_me()
        print(f"Successfully connected to Telegram API!")
        print(f"Bot information: {me.first_name} (@{me.username})")
        return True
    except TelegramError as e:
        print(f"Telegram Error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_connection()
