import os
import logging
import json
import csv
from datetime import datetime
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    Updater, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler,
    Filters,
    CallbackContext
)
from dotenv import load_dotenv
from sheets_helper import SheetsHelper
from utils.backup_manager import BackupManager
from logging.handlers import RotatingFileHandler
import sys

# Load environment variables
load_dotenv()

# Get bot token from environment variables
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Configure logging with rotation and enhanced formatting
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

# File handler with rotation (10MB per file, keep 5 backup files)
file_handler = RotatingFileHandler('logs/bot.log', maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.DEBUG)  # Changed from INFO to DEBUG

# Configure root logger
logging.root.setLevel(logging.DEBUG)  # Changed from INFO to DEBUG
logging.root.addHandler(file_handler)
logging.root.addHandler(console_handler)

# Set Telegram API logger to WARNING to avoid exposing token
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('telegram.bot').setLevel(logging.WARNING)
logging.getLogger('telegram.ext.updater').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Initialize backup manager
backup_manager = BackupManager()

class FormBot:
    def __init__(self):
        self.questions = self.load_questions()
        self.state_links = self.load_state_links()
        self.leadership_links = {
            'general': 'https://t.me/c/2399831251/13132',
            'veterans_educators_nurses': 'https://t.me/c/2399831251/289114',
            'marginalized_underrepresented': 'https://t.me/c/2399831251/231957'
        }
        self.social_media_links = {
            "BlueSky": "https://bsky.app/profile/voicesignited.bsky.social",
            "TikTok": "https://www.tiktok.com/@voices_united",
            "Substack": "https://voicesignited.substack.com/",
            "YouTube": "https://www.youtube.com/@VoicesIgnited",
            "Instagram": "https://www.instagram.com/voicesignited",
            "Linktree": "https://linktr.ee/voices_ignited",
            "Keybase": "keybase://team-page/quiz_team"
        }
        self.sheets_helper = SheetsHelper()
        
    def load_questions(self):
        """Load and validate questions from JSON file."""
        try:
            questions_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'questions.json')
            
            # Create backup before loading
            backup_manager.backup_file(questions_path)
            
            with open(questions_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Validate question format
                if not isinstance(data, dict) or 'quiz' not in data or not isinstance(data['quiz'], list):
                    logger.error("Invalid questions.json format: must have a 'quiz' list")
                    raise ValueError("Invalid questions.json format")
                
                for q in data['quiz']:
                    if not isinstance(q, dict):
                        logger.error(f"Invalid question format - not a dict: {q}")
                        raise ValueError("Invalid question format")
                    
                    required_fields = ['id', 'question', 'type']
                    for field in required_fields:
                        if field not in q:
                            logger.error(f"Question missing required field '{field}': {q}")
                            raise ValueError(f"Question missing required field '{field}'")
                    
                    if q['type'] in ['multiple_choice', 'multiple_select'] and ('options' not in q or not q['options']):
                        logger.error(f"Multiple choice/select question missing options: {q}")
                        raise ValueError("Multiple choice/select question missing options")
                
                logger.info(f"Successfully loaded {len(data['quiz'])} questions")
                return data['quiz']
        except Exception as e:
            logger.error(f"Error loading questions: {str(e)}", exc_info=True)
            raise  # Re-raise the error to stop bot initialization
            
    def load_state_links(self):
        """Load state links from CSV file."""
        state_links = {}
        try:
            csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'forum_topics_with_links.csv')
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert state name to match the format in questions.json
                    state_name = row['title'].strip().title()
                    if state_name in [
                        "Alabama", "Alaska", "Arizona", "Arkansas", "California",
                        "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
                        "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
                        "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
                        "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
                        "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
                        "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
                        "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
                        "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
                        "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
                    ]:
                        state_links[state_name] = row['link']
        except Exception as e:
            logger.error(f"Error loading state links: {str(e)}")
        return state_links

    def get_user_data(self, context: CallbackContext):
        """Initialize or get user data with proper structure."""
        try:
            if 'form_data' not in context.user_data:
                context.user_data['form_data'] = {
                    'current_question': 0,
                    'answers': {},
                    'start_time': datetime.now().isoformat()
                }
            return context.user_data['form_data']
        except Exception as e:
            logger.error(f"Error in get_user_data: {str(e)}", exc_info=True)
            raise

    def start(self, update: Update, context: CallbackContext):
        """Start the conversation and send first question."""
        try:
            if not self.questions:
                logger.error("No questions loaded")
                update.message.reply_text("Sorry, there was an error loading the questions. Please try again later.")
                return

            # Get user info
            user = update.effective_user
            username = user.username or "Unknown"
            first_name = user.first_name or "Unknown"
            last_name = user.last_name or "Unknown"
            user_id = str(user.id)

            # Reset user data
            context.user_data['form_data'] = {
                'current_question': 0,
                'answers': {
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'user_id': user_id
                },
                'start_time': datetime.now().isoformat()
            }

            # Send welcome message and first question
            welcome_text = (
                "Hello and welcome to Voices Ignited! \n\n"
                "We are a movement fighting for a government that truly serves its people, not corporations.\n"
                "This short quiz will help us understand your values and how you'd like to contribute.\n"
                "Let's stand together for justice, equality, and real change—let's get started!\n "
                "Please answer all questions to complete your profile."
            )
            update.message.reply_text(welcome_text)
            self.send_question(update, context)
        except Exception as e:
            logger.error(f"Error in start: {str(e)}", exc_info=True)
            update.message.reply_text("Sorry, something went wrong. Please try again later.")

    def send_question(self, update: Update, context: CallbackContext):
        """Send the current question to the user."""
        try:
            user_data = self.get_user_data(context)
            current_idx = user_data['current_question']
            
            # Check if we've reached the end of questions
            if current_idx >= len(self.questions):
                # Finish the form
                self.finish_form(update, context)
                return

            question = self.questions[current_idx]
            question_text = f"{current_idx + 1}. {question['question']}"
            
            # Add description if present
            if 'description' in question:
                question_text += f"\n\n{question['description']}"

            if question.get('type') in ['multiple_choice', 'multiple_select']:
                # Get the current options
                options = question.get('options', [])
                
                # For state question, check if we need to use region-specific options
                if question['id'] == 'state' and question.get('dynamic'):
                    selected_region = user_data['answers'].get('region')
                    if selected_region and 'region_states' in question:
                        options = question['region_states'].get(selected_region, ["Other State"])
                        logger.info(f"Using region-specific states for {selected_region}: {options}")
                
                # Create keyboard with available options
                keyboard = []
                for option in options:
                    keyboard.append([InlineKeyboardButton(option, callback_data=option)])
                    
                # For multiple select, add a "Done" button
                if question.get('type') == 'multiple_select':
                    # Initialize selected options in user data if not present
                    if 'selected_options' not in user_data:
                        user_data['selected_options'] = []
                    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="DONE_SELECTING")])
                    # Add note about multiple selection
                    question_text += "\n\n(You can select multiple options. Click '✅ Done' when finished.)"
                
                # Add back button if not on the first question
                bottom_row = []
                if current_idx > 0:
                    bottom_row.append(InlineKeyboardButton("⬅️ Back", callback_data="GO_BACK"))
                
                # Add the bottom row if it has any buttons
                if bottom_row:
                    keyboard.append(bottom_row)
                    
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if update.callback_query:
                    update.callback_query.message.edit_text(
                        text=question_text,
                        reply_markup=reply_markup
                    )
                elif update.message:
                    update.message.reply_text(
                        text=question_text,
                        reply_markup=reply_markup
                    )
                else:
                    logger.error("No valid message object found in update")
                    raise ValueError("No valid message object found in update")
            else:
                # For text input questions
                # Create keyboard with just the back button if not on first question
                keyboard = []
                if current_idx > 0:
                    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="GO_BACK")])
                
                # Only create reply markup if we have buttons
                reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                
                if update.callback_query:
                    update.callback_query.message.edit_text(
                        text=question_text,
                        reply_markup=reply_markup
                    )
                elif update.message:
                    update.message.reply_text(
                        text=question_text,
                        reply_markup=reply_markup
                    )
                else:
                    logger.error("No valid message object found in update")
                    raise ValueError("No valid message object found in update")
                    
        except Exception as e:
            logger.error(f"Error in send_question: {str(e)}", exc_info=True)
            try:
                if update.callback_query:
                    update.callback_query.message.reply_text("Sorry, something went wrong. Please try /start again.")
                elif update.message:
                    update.message.reply_text("Sorry, something went wrong. Please try /start again.")
            except Exception as nested_e:
                logger.error(f"Error in error handler: {str(nested_e)}")

    def handle_response(self, update: Update, context: CallbackContext):
        """Handle text responses."""
        user_data = self.get_user_data(context)
        current_idx = user_data['current_question']
        current_question = self.questions[current_idx]
        
        if current_idx >= len(self.questions):
            update.message.reply_text("You've already completed the form!")
            return

        # Handle number type questions
        if current_question['type'] == 'number':
            try:
                number = int(update.message.text)
                if current_question['id'] == 'age':
                    if number < 13 or number > 120:
                        update.message.reply_text("Please enter a valid age between 13 and 120.")
                        return
                    if number < 18:
                        update.message.reply_text(
                            "We apologize, but you must be 18 or older to participate in Voices Ignited. "
                            "Thank you for your interest!"
                        )
                        return
            except ValueError:
                update.message.reply_text("Please enter a valid number.")
                return

        # Save the answer and move to next question
        user_data['answers'][current_question['id']] = update.message.text
        user_data['current_question'] += 1
        self.send_question(update, context)

    def handle_callback(self, update: Update, context: CallbackContext):
        """Handle button callbacks."""
        try:
            query = update.callback_query
            user_data = self.get_user_data(context)
            current_idx = user_data['current_question']
            current_question = self.questions[current_idx]
            
            # Always acknowledge the callback query first
            query.answer()
            
            # Handle multiple select questions
            if current_question.get('type') == 'multiple_select':
                if 'selected_options' not in user_data:
                    user_data['selected_options'] = []
                    
                if query.data == "DONE_SELECTING":
                    if user_data['selected_options']:  # Only proceed if they selected at least one option
                        # Join the selected options with commas and save
                        user_data['answers'][current_question['id']] = ", ".join(user_data['selected_options'])
                        # Clear the selected options
                        user_data['selected_options'] = []
                        # Move to next question
                        user_data['current_question'] += 1
                        self.send_question(update, context)
                    else:
                        # If no options selected, inform the user
                        query.message.reply_text("Please select at least one option before clicking Done.")
                else:
                    # Toggle the selected option
                    if query.data in user_data['selected_options']:
                        user_data['selected_options'].remove(query.data)
                    else:
                        user_data['selected_options'].append(query.data)
                    # Update the message to show what's selected
                    current_selections = "\n\nSelected: " + ", ".join(user_data['selected_options']) if user_data['selected_options'] else ""
                    query.message.edit_text(
                        text=f"{current_idx + 1}. {current_question['question']}\n\n(You can select multiple options. Click '✅ Done' when finished.){current_selections}",
                        reply_markup=query.message.reply_markup
                    )
            elif query.data == "GO_BACK":
                # Move back to previous question
                user_data['current_question'] -= 1
                self.send_question(update, context)
            else:
                # For multiple choice questions, process immediately
                user_data['answers'][current_question['id']] = query.data
                user_data['current_question'] += 1
                self.send_question(update, context)
                
        except Exception as e:
            logger.error(f"Error in handle_callback: {str(e)}", exc_info=True)
            try:
                query.answer()  # Make sure to acknowledge the query even on error
                update.callback_query.message.reply_text("Sorry, something went wrong. Please try /start again.")
            except Exception as inner_e:
                logger.error(f"Error sending error message: {str(inner_e)}", exc_info=True)

    def process_answer(self, update: Update, context: CallbackContext, answer: str):
        """Process the user's answer and move to next question."""
        try:
            user_data = self.get_user_data(context)
            current_idx = user_data['current_question']
            current_question = self.questions[current_idx]
            
            # Save the answer
            user_data['answers'][current_question['id']] = answer
            
            # Check for disqualifying answers
            if current_question['id'] in ['enforcement_affiliation', 'reporting_role'] and answer == "Yes":
                # Finish the form
                self.finish_form(update, context)
                update.effective_message.reply_text(
                    "We apologize, but based on your responses, we cannot proceed with your application. "
                    "Thank you for your interest in Voices Ignited."
                )
                context.user_data.clear()
                return
                
            if current_question['id'] == 'confidentiality' and answer == "No":
                # Finish the form
                self.finish_form(update, context)
                update.effective_message.reply_text(
                    "We apologize, but based on your responses, we cannot proceed with your application. "
                    "Thank you for your interest in Voices Ignited."
                )
                context.user_data.clear()
                return

            if current_question['id'] == 'mission_alignment' and answer == "Do not agree":
                # Finish the form
                self.finish_form(update, context)
                update.effective_message.reply_text(
                    "We apologize, but based on your responses, we cannot proceed with your application. "
                    "Thank you for your interest in Voices Ignited."
                )
                context.user_data.clear()
                return
            
            # If this was the region question, update the next question's state options
            if current_question['id'] == 'region':
                next_idx = current_idx + 1
                if next_idx < len(self.questions):
                    next_question = self.questions[next_idx]
                    if next_question['id'] == 'state' and next_question.get('dynamic'):
                        logger.info(f"Updating state options for region: {answer}")
                        if 'region_states' in next_question:
                            next_question['options'] = next_question['region_states'].get(answer, ["Other State"])
                            logger.info(f"New state options: {next_question['options']}")
                        else:
                            logger.error("region_states not found in state question")
            
            # Move to next question
            user_data['current_question'] += 1
            
            # Check if we're done with all questions
            if user_data['current_question'] >= len(self.questions):
                self.finish_form(update, context)
                return
                
            # Send next question
            self.send_question(update, context)
            
        except Exception as e:
            logger.error(f"Error in process_answer: {str(e)}", exc_info=True)
            if update.callback_query:
                update.callback_query.message.reply_text("Sorry, something went wrong. Please try /start again.")
            elif update.message:
                update.message.reply_text("Sorry, something went wrong. Please try /start again.")

    def save_to_local_csv(self, row_data):
        """Save response data to local CSV file."""
        try:
            # Ensure backup directories exist
            csv_dir = os.path.join(os.path.dirname(__file__), 'local_backups')
            if not os.path.exists(csv_dir):
                os.makedirs(csv_dir)

            # Current timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Paths for CSV files
            latest_csv = os.path.join(csv_dir, 'latest_responses.csv')
            timestamped_csv = os.path.join(csv_dir, f'responses_{timestamp}.csv')
            
            # Get headers from questions.json
            with open('questions.json', 'r', encoding='utf-8') as f:
                questions = json.load(f)['quiz']
            headers = ['Username', 'First Name', 'Last Name', 'User ID', 'Timestamp'] + [q['question'] for q in questions]
            
            # Create new CSV file if it doesn't exist
            if not os.path.exists(latest_csv):
                with open(latest_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
            
            # Append to latest responses
            with open(latest_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
            
            # Also save timestamped copy
            with open(timestamped_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                # Read all existing responses and write them
                with open(latest_csv, 'r', newline='', encoding='utf-8') as latest:
                    reader = csv.reader(latest)
                    next(reader)  # Skip header
                    for row in reader:
                        writer.writerow(row)
            
            logger.info(f"Response saved to local CSV files: {latest_csv} and {timestamped_csv}")
            
        except Exception as e:
            logger.error(f"Error saving to local CSV: {str(e)}", exc_info=True)

    def save_to_text_log(self, row_data):
        """Save response data to a simple text log file."""
        try:
            # Ensure log directory exists
            log_dir = os.path.join(os.path.dirname(__file__), 'response_logs')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Path for log file (one file per day)
            today = datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(log_dir, f'responses_{today}.log')
            
            # Format the data in an easy-to-read way
            log_entry = f"\n=== Response at {row_data[4]} ===\n"  # Timestamp is at index 4
            log_entry += f"Username: {row_data[0]}\n"
            log_entry += f"Name: {row_data[1]} {row_data[2]}\n"
            log_entry += f"User ID: {row_data[3]}\n"
            
            # Add all question responses
            with open('questions.json', 'r', encoding='utf-8') as f:
                questions = json.load(f)['quiz']
            
            for i, q in enumerate(questions):
                log_entry += f"{q['question']}: {row_data[i + 5]}\n"  # +5 because first 5 are user info and timestamp
            
            log_entry += "=" * 50 + "\n"
            
            # Append to log file
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            logger.info(f"Response saved to text log: {log_file}")
            
        except Exception as e:
            logger.error(f"Error saving to text log: {str(e)}", exc_info=True)

    def finish_form(self, update: Update, context: CallbackContext) -> None:
        """Save form data and finish."""
        try:
            # Get user data from form_data
            form_data = context.user_data.get('form_data', {})
            user_data = form_data.get('answers', {})
            chat_id = update.effective_chat.id
            
            # Get current time
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Start row data with user info and timestamp
            row_data = [
                user_data.get('username', 'Unknown'),
                user_data.get('first_name', 'Unknown'),
                user_data.get('last_name', 'Unknown'),
                user_data.get('user_id', 'Unknown'),
                timestamp
            ]
            
            # Load questions to ensure correct order
            with open('questions.json', 'r', encoding='utf-8') as f:
                questions = json.load(f)['quiz']
            
            # Add responses in the same order as questions
            for q in questions:
                response = user_data.get(q['id'], '')
                if isinstance(response, list):
                    response = ', '.join(response)
                row_data.append(response)
            
            # Save to Google Sheet
            try:
                self.sheets_helper.append_row(row_data)
            except Exception as e:
                logger.error(f"Error saving to Google Sheets: {str(e)}", exc_info=True)
            
            # Save to local CSV
            self.save_to_local_csv(row_data)
            
            # Save to text log
            self.save_to_text_log(row_data)
            
            # Get user preferences for personalized recommendations
            user_state = None
            state_keys = ['state', 'location_state', 'region']
            for key in state_keys:
                if key in user_data and user_data[key]:
                    user_state = user_data[key]
                    logger.info(f"Found state using key: {key} = {user_state}")
                    break
                    
            beliefs = user_data.get('beliefs', [])
            if isinstance(beliefs, str) and beliefs:
                beliefs = [beliefs]
            skills = user_data.get('skills', [])
            if isinstance(skills, str) and skills:
                skills = [skills]
            activism_type = user_data.get('activism_type', [])
            if isinstance(activism_type, str) and activism_type:
                activism_type = [activism_type]
            leadership_interest = user_data.get('leadership', '')
            social_media_platforms = user_data.get('social_media', [])
            if isinstance(social_media_platforms, str) and social_media_platforms:
                social_media_platforms = [social_media_platforms]
                
            # Debug logging to see what data we have
            logger.info(f"User data keys: {list(user_data.keys())}")
            logger.info(f"User state: {user_state}")
            logger.info(f"Beliefs: {beliefs}")
            logger.info(f"Skills: {skills}")
            logger.info(f"Activism type: {activism_type}")
            logger.info(f"Leadership interest: {leadership_interest}")
            
            # Prepare completion message with personalized recommendations
            completion_text = (
                "Thank you for completing the Voices Ignited questionnaire! \n\n"
                "Welcome to the group! Here are some links to get you started:\n"
            )
            
            # Add state-specific link if available
            if user_state and user_state in self.state_links:
                completion_text += f"\n• Your local state group: {self.state_links[user_state]}"
            else:
                # If state not found, check if it's a region and provide general info
                region = user_data.get('region', '')
                if region:
                    completion_text += f"\n• Your region ({region}) resources: https://t.me/c/2399831251/regional_resources"
                else:
                    # Fallback to general state resources
                    completion_text += f"\n• State & regional resources: https://t.me/c/2399831251/state_resources"
            
            # Add general channels that everyone should join
            general_channels = [
                ("Mental Health Check In", "https://t.me/c/2399831251/227321"),
                ("Public Announcements", "https://t.me/c/2399831251/465"),
                ("Official Media & Information", "https://t.me/c/2399831251/202409"),
                ("Open Discussion", "https://t.me/c/2399831251/8684")
            ]
            
            completion_text += "\n\nImportant general channels:"
            for channel_name, channel_link in general_channels:
                completion_text += f"\n• {channel_name}: {channel_link}"
            
            # Add topic-specific channels based on user interests
            topic_channels = []
            
            # Add channels based on beliefs
            if "Healthcare Rights" in beliefs:
                topic_channels.append(("Healthcare Advocacy", "https://t.me/c/2399831251/123456"))
            if "Environmental Issues" in beliefs:
                topic_channels.append(("Environmental Action", "https://t.me/c/2399831251/234567"))
            if "Government Reform" in beliefs:
                topic_channels.append(("Government Reform", "https://t.me/c/2399831251/345678"))
            if "Economic Justice" in beliefs:
                topic_channels.append(("Economic Justice", "https://t.me/c/2399831251/456789"))
            
            # Add channels based on activism type
            if "Online Advocacy" in activism_type:
                topic_channels.append(("Digital Activism", "https://t.me/c/2399831251/567890"))
            if "Direct Action/Protest" in activism_type:
                topic_channels.append(("Direct Action Planning", "https://t.me/c/2399831251/678901"))
            if "Policy/Legislative" in activism_type:
                topic_channels.append(("Policy Working Group", "https://t.me/c/2399831251/789012"))
            
            # Add channels based on skills
            if "Social Media" in skills or "Writing/Content" in skills:
                topic_channels.append(("Content Creation", "https://t.me/c/2399831251/890123"))
            if "Tech/IT" in skills:
                topic_channels.append(("Tech Team", "https://t.me/c/2399831251/901234"))
            if "Event Planning" in skills:
                topic_channels.append(("Event Coordination", "https://t.me/c/2399831251/012345"))
            
            # Add topic channels if any were selected
            if topic_channels:
                completion_text += "\n\nBased on your interests, we recommend these topic channels:"
                for channel_name, channel_link in topic_channels:
                    completion_text += f"\n• {channel_name}: {channel_link}"
            
            # Add leadership application links if user expressed interest
            if leadership_interest in ["Yes, I'm ready to lead", "Maybe, I'd like to learn first"]:
                completion_text += "\n\nLeadership application channels:"
                completion_text += f"\n• General Leadership: {self.leadership_links['general']}"
                completion_text += f"\n• Veterans, Educators & Nurses: {self.leadership_links['veterans_educators_nurses']}"
                completion_text += f"\n• Marginalized/Underrepresented Communities: {self.leadership_links['marginalized_underrepresented']}"
            
            # Add social media follow links
            completion_text += "\n\nFollow us on social media:"
            for platform, link in self.social_media_links.items():
                if platform != "Linktree" and platform != "Keybase":
                    completion_text += f"\n• {platform}: {link}"
            
            completion_text += f"\n\nAll our social links: {self.social_media_links['Linktree']}"
            
            if "encrypted_communication" in user_data and user_data["encrypted_communication"] == "Yes":
                completion_text += f"\n\nSecure communication: {self.social_media_links['Keybase']}"
            
            # Clear user data
            context.user_data.clear()
            
            # Send completion message
            if update.callback_query:
                update.callback_query.message.reply_text(
                    completion_text
                )
            else:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=completion_text
                )
            
        except Exception as e:
            logger.error(f"Error in finish_form: {str(e)}")
            context.bot.send_message(
                chat_id=chat_id,
                text="Sorry, there was an error saving your responses. Please try again later or contact support."
            )

def main():
    """Run the bot."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get bot token from environment
        token = BOT_TOKEN
        if not token:
            raise ValueError("No bot token found in environment variables")
            
        # Enable more verbose logging
        logging.getLogger('telegram').setLevel(logging.DEBUG)
        logging.getLogger('telegram.ext').setLevel(logging.DEBUG)
        
        bot = FormBot()
        updater = Updater(token, use_context=True)
        bot.updater = updater
        
        # Get the dispatcher to register handlers
        dp = updater.dispatcher

        # Add handlers
        dp.add_handler(CommandHandler('start', bot.start))
        dp.add_handler(CommandHandler('quiz', bot.start))  # Use the same handler for both commands
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, bot.handle_response))
        dp.add_handler(CallbackQueryHandler(bot.handle_callback))

        # Add error handler
        def error_handler(update: Update, context: CallbackContext):
            error = context.error
            logger.error(f"Error occurred: {error}", exc_info=True)
            try:
                if update and update.effective_message:
                    update.effective_message.reply_text("Sorry, something went wrong. Please try again later.")
                elif update and update.callback_query:
                    update.callback_query.message.reply_text("Sorry, something went wrong. Please try /start again.")
            except Exception as e:
                logger.error(f"Error in error handler: {e}", exc_info=True)
        
        dp.add_error_handler(error_handler)
        
        # Start the bot
        logger.info("Starting bot with token ending in ...%s", token[-4:])
        updater.start_polling(
            timeout=30,
            read_latency=5,
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        updater.idle()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
