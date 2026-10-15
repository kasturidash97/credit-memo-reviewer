import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 1. find the latest memo version
versions = []
for f in glob.glob("memo_v[0-9]*.json"):
    versions.append(int(re.findall(r"\d+", f)[0]))
current = max(versions)
old_file = "memo_v%d.json" % current
new_file = "memo_v%d.json" % (current + 1)
memo = json.load(open(old_file))
facts_text = pd.read_csv("facts.csv").to_csv(index=False)

# 2. ask the human which section and what the comment is
titles = list(memo.keys())
print("Reviewing", old_file)
for i, t in enumerate(titles, 1):
    print(i, "-", t)
choice = int(input("Which section number? "))
title = titles[choice - 1]
comment = input("Your reviewer comment: ")
old_text = memo[title]

# 3. ask Gemini to rewrite ONLY that section
prompt = """You are helping a credit analyst revise ONE section of a draft credit memo for J. Kumar Infraprojects Limited.
Amounts are in Rs lakh. Use ONLY the facts table below.

RULES
1. Rewrite only the section given. Apply the reviewer comment.
2. Use only numbers from the facts table. Never invent a number.
3. After every number, keep a source tag in square brackets, like [PDF page 155] or [calculated].
4. If the comment asks for something the table cannot answer, say "Not in the data provided." Do not guess.
5. The Revenue growth row is FY2024-25 over FY2023-24 only.
6. Plain, simple English. Return only the new text of the section.

SECTION TITLE: """ + title + """

CURRENT TEXT:
""" + old_text + """

REVIEWER COMMENT:
""" + comment + """

FACTS TABLE:
""" + facts_text

new_text = None
for m in ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]:
    try:
        reply = client.models.generate_content(
            model=m, contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2))
        new_text = reply.text.strip()
        print("Revised by", m)
        break
    except Exception as e:
        print("FAILED:", m, "->", str(e)[:120])
if new_text is None:
    sys.exit("No model worked. Wait a minute and run again.")

# 4. save the new version, change only that one section
new_memo = dict(memo)
new_memo[title] = new_text
json.dump(new_memo, open(new_file, "w"), indent=2)

# 5. prove the other sections did not change
for t in titles:
    if t != title and new_memo[t] != memo[t]:
        sys.exit("Something else changed. Stop and tell me.")
print("Other sections unchanged: yes")

# 6. history log
history = []
if os.path.exists("history.json"):
    history = json.load(open("history.json"))
history.append({
    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "from": old_file, "to": new_file,
    "section": title, "comment": comment,
    "old": old_text, "new": new_text,
})
json.dump(history, open("history.json", "w"), indent=2)

# 7. show old vs new
print()
print("=== OLD:", title)
print(old_text)
print()
print("=== NEW:", title)
print(new_text)
print()

# 8. run the number check on the new version
subprocess.run([sys.executable, "check_memo.py", new_file])
