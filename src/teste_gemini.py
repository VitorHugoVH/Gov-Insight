from google import genai
from dotenv import load_dotenv
import os

load_dotenv("../.env")

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Responda apenas OK"
)

print(response.text)
