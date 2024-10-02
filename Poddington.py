import os
import sys
import PyPDF2
import requests
from gtts import gTTS
import re
from dotenv import load_dotenv
from groq import Groq
from pydub import AudioSegment

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def read_pdf(file_path):
    try:
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return None

def read_text_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading text file: {e}")
        return None

def fetch_article(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching article: {e}")
        return None

def process_text(text):
    # Remove extra whitespace and normalize text
    text = re.sub(r'\s+', ' ', text).strip()
    # Add more text processing logic here if needed
    return text

def summarize_text(text):
    prompt = f"Summarize the following text in about 100 words:\n\n{text}"
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=150,
    )
    return response.choices[0].message.content

def generate_dialogue(summary):
    prompt = f"""
    Create a conversational dialogue between two podcast hosts, Alex and Sam, discussing the following summary:

    {summary}

    Make the conversation engaging, informative, and natural. Include some back-and-forth discussion, questions, and insights from both hosts. The dialogue should be about 300-400 words long.

    Format the output as:
    Alex: [Alex's line]
    Sam: [Sam's line]
    ...and so on.
    """
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=600,
    )
    return response.choices[0].message.content

def generate_audio_segment(text, voice, output_file):
    tts = gTTS(text=text, lang='en', tld='com.au' if voice == 'Alex' else 'co.uk')
    tts.save(output_file)
    return AudioSegment.from_mp3(output_file)

def generate_podcast(dialogue, output_file):
    lines = dialogue.split('\n')
    audio_segments = []

    for line in lines:
        if line.startswith('Alex:') or line.startswith('Sam:'):
            voice, text = line.split(':', 1)
            temp_file = f"temp_{voice.lower()}.mp3"
            audio_segment = generate_audio_segment(text.strip(), voice, temp_file)
            audio_segments.append(audio_segment)
            os.remove(temp_file)

    combined = sum(audio_segments)
    combined.export(output_file, format="mp3")

def main():
    print("Welcome to Poddington - Your Conversational Podcast Generator!")
    
    while True:
        input_source = input("Enter the path to the input file or URL (or 'q' to quit): ")
        if input_source.lower() == 'q':
            print("Thank you for using Poddington. Goodbye!")
            sys.exit(0)

        output_file = input("Enter the name for the output audio file (e.g., podcast.mp3): ")

        # Determine the type of input and read accordingly
        if input_source.startswith('http'):
            content = fetch_article(input_source)
        elif input_source.endswith('.pdf'):
            content = read_pdf(input_source)
        else:
            content = read_text_file(input_source)

        if content is None:
            print("Failed to read the input. Please try again.")
            continue

        # Process the text
        processed_text = process_text(content)

        # Summarize the text
        summary = summarize_text(processed_text)
        print("Summary generated.")

        # Generate dialogue
        dialogue = generate_dialogue(summary)
        print("Dialogue generated.")

        # Generate the podcast
        generate_podcast(dialogue, output_file)
        print(f"Podcast generated and saved as {output_file}")

if __name__ == "__main__":
    main()
