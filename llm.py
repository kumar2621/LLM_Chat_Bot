from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os
import pdfplumber

api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    raise ValueError("API key not found")

client = MistralClient(api_key=api_key)

def chat_once(messages):
    response = client.chat(
        model="mistral-small",
        messages=messages,
        temperature=0.5,
        top_p=0.9
    )
    return response.choices[0].message.content

def extract_pdf_text(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print("PDF error:", e)

    return text.strip()