import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

for model in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite"]:
    try:
        reply = client.models.generate_content(model=model, contents="Say hello in one short line.")
        print("WORKED with", model, "->", reply.text)
        break
    except Exception as e:
        print("failed", model, str(e)[:100])
