import google.generativeai as genai
import PyPDF2
import os

# Initialize Google API with your key
google_api_key = 'AIzaSyDRE_FFGQ-4Tz6G3r64l1G__hCopinmvg8'
genai.configure(api_key=google_api_key)

# Read PDF
def read_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text

# Divide text into smaller chunks
def divide_text(text, section_size):
    return [text[i:i+section_size] for i in range(0, len(text), section_size)]

# Create Anki cards
def create_anki_cards(pdf_text):
    SECTION_SIZE = 1000
    divided_sections = divide_text(pdf_text, SECTION_SIZE)
    generated_flashcards = ''
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    for i, text in enumerate(divided_sections):
        prompt = ("Create a comprehensive set of Anki flashcards using the following text. "
                  "Strictly create questions only about the core concepts of the text."
                  "Ensure detailed questions and in-depth answers. Use the format: "
                  "question;answer next line question;answer etc. "
                  "Each question should cover key concepts thoroughly, and the answer should provide "
                  "a well-explained response. Include more questions to cover the material extensively. /n/n" + text)
        
        response = model.generate_content(prompt)
        generated_flashcards += response.text if response.text else ""
        
        if i == 0:
            break  # Process only the first chunk to limit API usage

    # Save the flashcards to a text file
    with open("flashcards.txt", "w") as f:
        f.write(generated_flashcards)

# Main script execution
if __name__ == "__main__":
    pdf_text = read_pdf('C:/Users/ICANIO10090/Documents/PhiData/test/MACHINE LEARNING(R17A0534).pdf')
    create_anki_cards(pdf_text)