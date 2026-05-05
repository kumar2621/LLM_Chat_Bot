from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os

api_key = os.getenv("MISTRAL_API_KEY")

if not api_key:
    raise ValueError("API key not found. Set MISTRAL_API_KEY")

client = MistralClient(api_key=api_key)

def chat_once(messages):
    response = client.chat(
        model="mistral-small",
        messages=messages,
        temperature = 0.5,
        top_p = 0.9
    )
    return response.choices[0].message.content