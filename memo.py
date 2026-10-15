import json
import os
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

facts = pd.read_csv("facts.csv")
facts_text = facts.to_csv(index=False)

prompt = """You are helping a credit analyst draft a short credit memo for J. Kumar Infraprojects Limited,
based only on the facts table below. Amounts are in Rs lakh. The table has two years: FY2024-25 and FY2023-24.

RULES
1. Use ONLY numbers that appear in the facts table. Never invent or estimate any number.
2. After every number, add its source in square brackets, like [PDF page 155] or [calculated].
3. Write each number exactly as it appears in the table (same digits).
4. If the table cannot answer something, write "Not in the data provided." Do not guess.
5. Plain, simple English. Short sentences.
6. The Revenue growth row is one figure: FY2024-25 over FY2023-24. Never claim growth for FY2023-24 or any earlier trend from it.

Return JSON with exactly these 4 keys, each a short paragraph (3 to 5 sentences):
"Business and financial performance", "Leverage and debt service", "Points for the reviewer to verify", "Preliminary view"
For "Preliminary view": say it is a draft for human review, not an approval or rejection.

FACTS TABLE
""" + facts_text

models = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]
memo = None
for m in models:
    try:
        reply = client.models.generate_content(
            model=m,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2),
        )
        memo = json.loads(reply.text)
        print("Memo written by", m)
        break
    except Exception as e:
        print("FAILED:", m, "->", str(e)[:150])

if memo is None:
    raise SystemExit("No model worked. Wait a minute and run again.")

with open("memo_v1.json", "w") as f:
    json.dump(memo, f, indent=2)

for title, text in memo.items():
    print()
    print("##", title)
    print(text)
print()
print("Saved memo_v1.json")
