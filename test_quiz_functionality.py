import json
import os
from datetime import datetime
from utils.backup_manager import BackupManager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize backup manager
backup_manager = BackupManager()

def load_questions():
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
        logger.error(f"Error loading questions: {str(e)}")
        raise

def simulate_quiz():
    """Simulate a user going through the quiz."""
    questions = load_questions()
    
    print("\n===== QUIZ SIMULATION =====\n")
    print("Welcome to Voices Ignited Quiz!\n")
    
    # Simulate user answers
    answers = {}
    
    for i, question in enumerate(questions, 1):
        print(f"Question {i}/{len(questions)}: {question['question']}")
        
        if question['type'] in ['multiple_choice', 'multiple_select'] and 'options' in question:
            print("Options:")
            for j, option in enumerate(question['options'], 1):
                print(f"  {j}. {option}")
        
        # Simulate an answer
        if question['type'] == 'multiple_choice':
            # Just pick the first option for simulation
            answer = question['options'][0] if 'options' in question and question['options'] else "Simulated answer"
        elif question['type'] == 'multiple_select':
            # Pick the first two options if available
            answer = question['options'][:2] if 'options' in question and len(question['options']) >= 2 else ["Simulated answer 1"]
        elif question['type'] == 'text':
            answer = "Simulated text response"
        else:
            answer = "Simulated default response"
        
        answers[question['id']] = answer
        print(f"Simulated answer: {answer}\n")
    
    print("\n===== QUIZ COMPLETED =====\n")
    print("Here are your answers:")
    for q_id, answer in answers.items():
        print(f"{q_id}: {answer}")
    
    print("\nIn a real scenario, these answers would be saved to Google Sheets.")

if __name__ == "__main__":
    try:
        simulate_quiz()
    except Exception as e:
        logger.error(f"Error in simulation: {e}")
        print(f"\nError: {e}")
