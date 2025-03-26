import json
import os

def load_questions():
    """Load questions from JSON file."""
    try:
        questions_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'questions.json')
        
        with open(questions_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'quiz' in data and isinstance(data['quiz'], list):
                return data['quiz']
            else:
                print("Error: Invalid questions.json format")
                return []
    except Exception as e:
        print(f"Error loading questions: {str(e)}")
        return []

def main():
    questions = load_questions()
    print(f"Loaded {len(questions)} questions\n")
    
    for i, q in enumerate(questions, 1):
        print(f"Question {i}: {q.get('id', 'No ID')}")
        print(f"Type: {q.get('type', 'No type')}")
        print(f"Question: {q.get('question', 'No question text')}")
        
        if 'options' in q and q['options']:
            print("Options:")
            for j, option in enumerate(q['options'], 1):
                print(f"  {j}. {option}")
        
        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    main()
