from flask import Flask, render_template, request, redirect, url_for, session
import os
import google.generativeai as genai
import PyPDF2
import re
import json
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

# Configure Google API
genai.configure(api_key='AIzaSyDRE_FFGQ-4Tz6G3r64l1G__hCopinmvg8')

# Define upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Read PDF
def read_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

# Create flashcards from PDF
def create_flashcards(pdf_text, num_flashcards=10):
    # Divide text into chunks
    chunks = [pdf_text[i:i+1000] for i in range(0, len(pdf_text), 1000)]
    
    # Use Gemini to generate flashcards
    model = genai.GenerativeModel('gemini-1.5-flash')
    flashcards = []
    
    for chunk in chunks[:2]:  # Process only first 2 chunks to avoid rate limits
        prompt = f"""
        Create {num_flashcards} flashcards from this text that focus ONLY on core concepts and key ideas.
        DO NOT include metadata, publication details, or peripheral information.
        Each flashcard should have a question about a fundamental concept and a clear, concise answer.
        Format each flashcard as a JSON object with 'question' and 'answer' fields.
        Return an array of these objects.
        
        Text: {chunk}
        """
        
        try:
            response = model.generate_content(prompt)
            response_text = response.text
            
            # Try to extract JSON from the response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                try:
                    cards = json.loads(json_match.group(0))
                    if isinstance(cards, list):
                        flashcards.extend(cards)
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"Error generating flashcards: {str(e)}")
    
    # If no flashcards were generated, create some simple ones
    if not flashcards:
        sentences = re.split(r'(?<=[.!?])\s+', pdf_text)
        for i in range(0, min(len(sentences), int(num_flashcards)), 2):
            if i + 1 < len(sentences):
                flashcards.append({
                    "question": sentences[i],
                    "answer": sentences[i + 1]
                })
    
    return flashcards[:int(num_flashcards)]

# Generate coding problem
def generate_coding_problem(topic):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Generate a Python programming problem about {topic}.
    Include:
    1. A clear problem statement
    2. At least 2 input/output examples
    3. Constraints for the solution
    4. A correct solution in Python
    
    Format your response as a JSON object with the following structure:
    {{
      "problem": "The problem statement",
      "examples": [
        {{"input": "example input", "output": "example output", "explanation": "explanation of the example"}}
      ],
      "constraints": ["constraint 1", "constraint 2", ...],
      "solution": "The solution code"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                problem_data = json.loads(json_match.group(0))
                return problem_data
            except json.JSONDecodeError:
                pass
        
        # If JSON parsing fails, return a simple problem
        return {
            "problem": f"Write a Python function to solve a problem related to {topic}.",
            "examples": [
                {"input": "example input", "output": "example output", "explanation": "This is an example"}
            ],
            "constraints": ["Your solution should be efficient"],
            "solution": "def solution():\n    # Your solution here\n    pass"
        }
    except Exception as e:
        print(f"Error generating problem: {str(e)}")
        return {
            "problem": f"Write a Python function to solve a problem related to {topic}.",
            "examples": [
                {"input": "example input", "output": "example output", "explanation": "This is an example"}
            ],
            "constraints": ["Your solution should be efficient"],
            "solution": "def solution():\n    # Your solution here\n    pass"
        }

# Evaluate coding solution
def evaluate_solution(problem, examples, constraints, solution, student_solution):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Problem: {problem}
    
    Examples:
    {json.dumps(examples, indent=2)}
    
    Constraints:
    {json.dumps(constraints, indent=2)}
    
    Correct Solution:
    {solution}
    
    Student Solution:
    {student_solution}
    
    Evaluate the student's solution and provide feedback.
    Format your response as a JSON object with the following structure:
    {{
      "correct": true/false,
      "feedback": "Detailed feedback on the code",
      "errors": ["error 1", "error 2", ...],
      "suggestions": ["suggestion 1", "suggestion 2", ...]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                eval_data = json.loads(json_match.group(0))
                return eval_data
            except json.JSONDecodeError:
                # If JSON parsing fails, return a simple evaluation
                return {
                    "correct": False,
                    "feedback": "Unable to parse the evaluation response. Please try again.",
                    "errors": ["JSON parsing error"],
                    "suggestions": ["Try submitting your solution again"]
                }
        
        # If no JSON found in the response, return a simple evaluation
        return {
            "correct": False,
            "feedback": "The evaluation response did not contain valid JSON. Please try again.",
            "errors": ["Invalid response format"],
            "suggestions": ["Try submitting your solution again"]
        }
    except Exception as e:
        print(f"Error evaluating solution: {str(e)}")
        # Return a simple evaluation with the error message
        return {
            "correct": False,
            "feedback": f"Error during evaluation: {str(e)}",
            "errors": ["Evaluation error"],
            "suggestions": ["Try again with a different approach"]
        }

# Get knowledge response
def get_knowledge_response(question):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Answer the following question with detailed information:
    
    {question}
    
    Provide a comprehensive answer with examples and explanations.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error getting knowledge response: {str(e)}")
        return f"I'm sorry, I couldn't process your question. Error: {str(e)}"

# Get chatbot response
def get_chatbot_response(user_message):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Define the context about the application
    app_context = """
    This is a learning assistant application with four main features:
    1. Knowledge Assistant: Answers questions about various topics using AI.
    2. Coding Assistant: Generates Python programming problems and evaluates user solutions.
    3. Flashcard Generator: Creates flashcards from PDF documents to help with studying.
    4. Notes Assistant: Provides access to structured subject notes and study materials.
    
    The application has a lavender color scheme and is designed to be user-friendly.
    """
    
    prompt = f"""
    You are a helpful assistant for a learning application. 
    {app_context}
    
    User question: {user_message}
    
    Provide a helpful, concise response that assists the user in using the application.
    If the user is asking about a specific feature, focus on explaining that feature.
    If the user is having trouble with something, provide step-by-step guidance.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error getting chatbot response: {str(e)}")
        return f"I'm sorry, I couldn't process your question. Error: {str(e)}"

@app.route('/')
def index():
    features = {
        'knowledge': {
            'title': 'Knowledge Assistant',
            'description': 'Get answers to your questions about various topics',
            'icon': 'fas fa-brain',
            'route': 'knowledge'
        },
        'coding': {
            'title': 'Coding Assistant',
            'description': 'Practice Python programming with interactive problems',
            'icon': 'fas fa-code',
            'route': 'coding'
        },
        'flashcards': {
            'title': 'Flashcard Generator',
            'description': 'Create flashcards from your PDF documents',
            'icon': 'fas fa-clone',
            'route': 'flashcards'
        },
        'notes': {
            'title': 'Notes Assistant',
            'description': 'Access and study subject notes',
            'icon': 'fas fa-book-open',
            'route': 'notes'
        }
    }
    return render_template('index.html', features=features)

@app.route('/knowledge', methods=['GET', 'POST'])
def knowledge():
    if request.method == 'POST':
        try:
            question = request.form['question']
            
            # Get response
            response_text = get_knowledge_response(question)
            
            # Clean the response
            cleaned_lines = []
            for line in response_text.split('\n'):
                line = line.strip()
                if line:
                    cleaned_lines.append(line)
            
            formatted_response = "<br/>".join([f"<p>{line}</p>" for line in cleaned_lines if line])
            return render_template('knowledge.html', response=formatted_response)
            
        except Exception as e:
            print(f"Error in knowledge route: {str(e)}")
            return render_template('knowledge.html', response=None, error=str(e))
    
    return render_template('knowledge.html', response=None)

@app.route('/coding', methods=['GET', 'POST'])
def coding():
    # Initialize attempts to 0 if not in session
    if 'attempts' not in session:
        session['attempts'] = 0
    
    if request.method == 'POST':
        if 'topic' in request.form:
            # Generate a new problem
            topic = request.form['topic']
            problem_data = generate_coding_problem(topic)
            
            # Store the problem data in the session
            session['problem'] = problem_data['problem']
            session['examples'] = problem_data['examples']
            session['constraints'] = problem_data['constraints']
            session['solution'] = problem_data['solution']
            session['attempts'] = 0
            
            return render_template('coding.html', 
                                  problem=problem_data['problem'],
                                  examples=problem_data['examples'],
                                  constraints=problem_data['constraints'],
                                  show_solution_form=True,
                                  attempts=0)
                
        elif 'submit_solution' in request.form and 'file_input' in request.files:
            try:
                # Handle file upload
                file = request.files['file_input']
                if file.filename == '':
                    return render_template('coding.html', 
                                          problem=session.get('problem', ''),
                                          examples=session.get('examples', []),
                                          constraints=session.get('constraints', []),
                                          show_solution_form=True,
                                          attempts=session.get('attempts', 0),
                                          error="No file selected")
                
                if not file.filename.endswith('.py'):
                    return render_template('coding.html', 
                                          problem=session.get('problem', ''),
                                          examples=session.get('examples', []),
                                          constraints=session.get('constraints', []),
                                          show_solution_form=True,
                                          attempts=session.get('attempts', 0),
                                          error="Only Python files are supported")
                
                # Save the file temporarily
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                
                try:
                    # Read the solution from the file
                    with open(file_path, 'r') as f:
                        student_solution = f.read()
                    
                    # Clean up the uploaded file
                    os.remove(file_path)
                    
                    # Get problem data from session
                    problem = session.get('problem', '')
                    examples = session.get('examples', [])
                    constraints = session.get('constraints', [])
                    correct_solution = session.get('solution', '')
                    
                    # Increment attempts counter
                    session['attempts'] = session.get('attempts', 0) + 1
                    attempts = session['attempts']
                    
                    # Evaluate the solution
                    eval_data = evaluate_solution(
                        problem, 
                        examples, 
                        constraints, 
                        correct_solution, 
                        student_solution
                    )
                    
                    # Check if the solution is correct
                    is_correct = eval_data.get('correct', False)
                    
                    # If the solution is correct or max attempts reached, show the solution
                    show_solution = is_correct or attempts >= 2
                    
                    # Format output lines for display
                    output_lines = []
                    
                    # Add feedback
                    if eval_data.get('feedback'):
                        output_lines.append({"type": "info", "content": eval_data.get('feedback')})
                    
                    # Add errors if any
                    for error in eval_data.get('errors', []):
                        output_lines.append({"type": "error", "content": error})
                    
                    # Add suggestions if any
                    for suggestion in eval_data.get('suggestions', []):
                        output_lines.append({"type": "suggestion", "content": suggestion})
                    
                    return render_template('coding.html',
                                          problem=problem,
                                          examples=examples,
                                          constraints=constraints,
                                          solution=correct_solution,
                                          output_lines=output_lines,
                                          is_correct=is_correct,
                                          show_solution_form=True,
                                          show_solution=show_solution,
                                          attempts=attempts)
                    
                except Exception as e:
                    # Clean up the uploaded file in case of error
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    return render_template('coding.html', 
                                          problem=session.get('problem', ''),
                                          examples=session.get('examples', []),
                                          constraints=session.get('constraints', []),
                                          show_solution_form=True,
                                          attempts=session.get('attempts', 0),
                                          error=f"Error processing file: {str(e)}")
            except Exception as e:
                # Handle any unexpected errors
                return render_template('coding.html', 
                                      problem=session.get('problem', ''),
                                      examples=session.get('examples', []),
                                      constraints=session.get('constraints', []),
                                      show_solution_form=True,
                                      attempts=session.get('attempts', 0),
                                      error=f"An unexpected error occurred: {str(e)}")
    
    # Check if we need to reset the session
    if request.args.get('reset') == 'true':
        session.pop('problem', None)
        session.pop('examples', None)
        session.pop('constraints', None)
        session.pop('solution', None)
        session.pop('attempts', None)
        session['attempts'] = 0
    
    # If there's a problem in the session, show it
    if 'problem' in session:
        return render_template('coding.html',
                              problem=session['problem'],
                              examples=session['examples'],
                              constraints=session['constraints'],
                              show_solution_form=True,
                              attempts=session.get('attempts', 0))
    
    # Otherwise, show the topic selection form
    return render_template('coding.html', show_topic_form=True, attempts=0)

@app.route('/flashcards', methods=['GET', 'POST'])
def flashcards():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('flashcards.html', error="No file uploaded")
        
        file = request.files['file']
        if file.filename == '':
            return render_template('flashcards.html', error="No file selected")
        
        if not file.filename.endswith('.pdf'):
            return render_template('flashcards.html', error="Only PDF files are supported")
        
        # Get number of flashcards from request
        num_flashcards = request.form.get('num_cards', '10')
        
        # Save the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        try:
            # Read the PDF
            pdf_text = read_pdf(file_path)
            
            # Create flashcards
            flashcards = create_flashcards(pdf_text, num_flashcards)
            
            # Clean up the uploaded file
            os.remove(file_path)
            
            return render_template('flashcards.html', flashcards=flashcards)
        except Exception as e:
            # Clean up the uploaded file in case of error
            if os.path.exists(file_path):
                os.remove(file_path)
            return render_template('flashcards.html', error=str(e))
    
    return render_template('flashcards.html')

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if 'messages' not in session:
        session['messages'] = []

    if request.method == 'POST':
        try:
            user_message = request.form['user_message']
            
            # Add user message to session
            session['messages'].append({
                'type': 'user',
                'text': user_message
            })
            
            # Get response from chatbot
            response_text = get_chatbot_response(user_message)
            
            # Clean the response
            cleaned_lines = []
            for line in response_text.split('\n'):
                line = line.strip()
                if line:
                    cleaned_lines.append(line)
            
            formatted_response = "<p>" + "</p><p>".join(cleaned_lines) + "</p>"
            
            # Add bot response to session
            session['messages'].append({
                'type': 'bot',
                'text': formatted_response
            })
            
            # Keep only last 50 messages
            if len(session['messages']) > 50:
                session['messages'] = session['messages'][-50:]
            
            return render_template('chatbot.html', messages=session['messages'])
            
        except Exception as e:
            print(f"Error in chatbot route: {str(e)}")
            return render_template('chatbot.html', 
                                messages=session['messages'], 
                                error=str(e))
    
    return render_template('chatbot.html', messages=session.get('messages', []))

def get_subject_notes(subject_file):
    """Read and parse subject notes from a file."""
    try:
        with open(subject_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into lessons
        lessons = content.split('LESSON')
        parsed_notes = []
        
        for lesson in lessons[1:]:  # Skip first empty split
            lesson_content = lesson.strip()
            # Split into modules
            modules = lesson_content.split('Module')
            lesson_num = modules[0].strip().split()[0]  # Get lesson number
            
            module_list = []
            for module in modules[1:]:  # Skip the lesson number part
                module_content = module.strip()
                module_lines = module_content.split('\n')
                module_title = module_lines[0].strip()
                
                # Extract topics (bullet points)
                topics = []
                current_topic = []
                
                for line in module_lines[1:]:
                    line = line.strip()
                    if line.startswith('•'):
                        # If we were building a previous topic, save it
                        if current_topic:
                            topics.append(' '.join(current_topic))
                            current_topic = []
                        # Start new topic
                        current_topic.append(line[1:].strip())  # Remove bullet point
                    elif line and current_topic:  # Continue previous topic
                        current_topic.append(line)
                
                # Add the last topic if exists
                if current_topic:
                    topics.append(' '.join(current_topic))
                
                module_list.append({
                    'title': module_title,
                    'topics': topics
                })
            
            parsed_notes.append({
                'lesson_num': lesson_num,
                'modules': module_list
            })
        
        return parsed_notes
    except Exception as e:
        print(f"Error parsing notes: {str(e)}")
        return None

@app.route('/notes')
def notes():
    # Get list of available subjects
    subject_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'subject context')
    subjects = {
        'MDA': {
            'name': 'Multivariate Data Analysis',
            'file': 'mda.txt',
            'description': 'Learn about multivariate analysis techniques and their applications.',
            'icon': 'fas fa-chart-bar'
        },
        'ML': {
            'name': 'Machine Learning',
            'file': 'ml.txt',
            'description': 'Explore machine learning algorithms, concepts, and implementations.',
            'icon': 'fas fa-brain'
        },
        'DL': {
            'name': 'Deep Learning',
            'file': 'dl.txt',
            'description': 'Study deep neural networks, architectures, and advanced concepts.',
            'icon': 'fas fa-network-wired'
        },
        'BDA': {
            'name': 'Big Data Analytics',
            'file': 'bda.txt',
            'description': 'Understand big data processing, analytics, and frameworks.',
            'icon': 'fas fa-database'
        },
        'TSA': {
            'name': 'Text and Speech Analysis',
            'file': 'tsa.txt',
            'description': 'Explore natural language processing and speech technologies.',
            'icon': 'fas fa-comments'
        },
        'FDSA': {
            'name': 'Fundamentals of Data Science and Analytics',
            'file': 'fdsa.txt',
            'description': 'Master the core concepts of data science and statistical analysis.',
            'icon': 'fas fa-chart-line'
        }
    }
    
    # Get selected subject from query parameter
    selected_subject = request.args.get('subject')
    notes_content = None
    
    if selected_subject and selected_subject in subjects:
        file_path = os.path.join(subject_dir, subjects[selected_subject]['file'])
        if os.path.exists(file_path):
            notes_content = get_subject_notes(file_path)
    
    return render_template('notes.html', 
                         subjects=subjects,
                         selected_subject=selected_subject,
                         notes=notes_content)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

