import json
import os
import logging
from datetime import datetime
from utils.backup_manager import BackupManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize backup manager
backup_manager = BackupManager()

class SimpleQuizBot:
    def __init__(self):
        self.questions = self.load_questions()
        self.user_data = {}
        self.current_user = "user123"
        
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
                
                logger.info(f"Successfully loaded {len(data['quiz'])} questions")
                return data['quiz']
        except Exception as e:
            logger.error(f"Error loading questions: {str(e)}")
            raise
    
    def initialize_user(self):
        """Initialize user data."""
        self.user_data[self.current_user] = {
            'current_question': 0,
            'answers': {
                'username': 'test_user',
                'first_name': 'Test',
                'last_name': 'User',
                'user_id': self.current_user
            },
            'start_time': datetime.now().isoformat()
        }
    
    def get_current_question(self):
        """Get the current question for the user."""
        if self.current_user not in self.user_data:
            self.initialize_user()
            
        user_data = self.user_data[self.current_user]
        current_idx = user_data['current_question']
        
        if current_idx >= len(self.questions):
            return None
        
        return self.questions[current_idx]
    
    def answer_question(self, answer):
        """Process the user's answer to the current question."""
        if self.current_user not in self.user_data:
            self.initialize_user()
            
        user_data = self.user_data[self.current_user]
        current_idx = user_data['current_question']
        
        if current_idx >= len(self.questions):
            return "You have already completed the quiz!"
        
        question = self.questions[current_idx]
        
        # Save the answer
        user_data['answers'][question['id']] = answer
        
        # Move to the next question
        user_data['current_question'] += 1
        
        # Check if we've reached the end
        if user_data['current_question'] >= len(self.questions):
            return self.finish_quiz()
        
        # Return the next question
        return self.format_question(self.questions[user_data['current_question']])
    
    def format_question(self, question):
        """Format a question for display."""
        result = f"Question: {question['question']}\n"
        
        if question['type'] in ['multiple_choice', 'multiple_select'] and 'options' in question:
            result += "Options:\n"
            for i, option in enumerate(question['options'], 1):
                result += f"  {i}. {option}\n"
        
        return result
    
    def finish_quiz(self):
        """Finish the quiz and return a summary."""
        user_data = self.user_data[self.current_user]
        
        # Calculate completion time
        start_time = datetime.fromisoformat(user_data['start_time'])
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Prepare summary
        summary = "\n===== QUIZ COMPLETED =====\n\n"
        summary += f"Completion time: {duration.total_seconds():.2f} seconds\n\n"
        summary += "Your answers:\n"
        
        for q_id, answer in user_data['answers'].items():
            if q_id not in ['username', 'first_name', 'last_name', 'user_id']:
                # Find the question text
                question_text = next((q['question'] for q in self.questions if q['id'] == q_id), q_id)
                summary += f"{question_text}: {answer}\n"
        
        summary += "\nThank you for completing the quiz!"
        return summary
    
    def run_interactive(self):
        """Run the bot in interactive mode."""
        print("Welcome to the Simple Quiz Bot!\n")
        print("This is a simplified version of the Telegram quiz bot.")
        print("You can answer questions and see how the bot works.\n")
        
        self.initialize_user()
        
        while True:
            question = self.get_current_question()
            
            if question is None:
                print("\nYou have already completed the quiz!")
                break
            
            print("\n" + self.format_question(question))
            
            # Get user input
            if question['type'] == 'multiple_choice':
                print("Enter the number of your choice:")
                choice = input("> ")
                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(question['options']):
                        answer = question['options'][choice_idx]
                    else:
                        print("Invalid choice. Please try again.")
                        continue
                except ValueError:
                    print("Please enter a number.")
                    continue
            elif question['type'] == 'multiple_select':
                print("Enter the numbers of your choices (comma-separated):")
                choices = input("> ")
                try:
                    choice_indices = [int(c.strip()) - 1 for c in choices.split(',')]
                    answer = [question['options'][idx] for idx in choice_indices if 0 <= idx < len(question['options'])]
                except (ValueError, IndexError):
                    print("Invalid choices. Please try again.")
                    continue
            else:  # text input
                print("Enter your answer:")
                answer = input("> ")
            
            # Process the answer
            result = self.answer_question(answer)
            
            # Check if quiz is completed
            if "QUIZ COMPLETED" in result:
                print(result)
                break

if __name__ == "__main__":
    try:
        bot = SimpleQuizBot()
        bot.run_interactive()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        print(f"\nError: {e}")
