import json
import re
import sys
import pandas as pd

filename = sys.argv[1] if len(sys.argv) > 1 else "memo_v1.json"
facts = pd.read_csv("facts.csv")
memo = json.load(open(filename))

allowed = []
for col in ["FY2024-25", "FY2023-24"]:
    allowed += [float(x) for x in pd.to_numeric(facts[col], errors="coerce").dropna()]

def close(x):
    for a in allowed:
        if abs(abs(x) - abs(a)) <= 0.011 + abs(a) / 2000:
            return True
    return False

NUMBER = r"\d[\d,]{0,}\.?\d{0,}"
bad = 0
print("Checking", filename)
for title, text in memo.items():
    clean = re.sub(r"\[[^\]]{0,}\]", " ", text)
    clean = re.sub(r"FY\s?\d{4}(-\d{2,4})?", " ", clean)
    clean = re.sub(r"\b(19|20)\d{2}\b", " ", clean)
    cleaned = []
    for n in re.findall(NUMBER, clean):
        n = n.strip(",.")
        if n:
            cleaned.append(n)
    for n in cleaned:
        x = float(n.replace(",", ""))
        if not close(x):
            bad += 1
            print("FLAG |", title, "| number not in facts table:", n)
    if cleaned and "[" not in text:
        bad += 1
        print("FLAG |", title, "| has numbers but no source tag")

if bad == 0:
    print("PASS: every number is in the facts table, and numbers have source tags.")
else:
    print(bad, "flag(s). A human must look at these before using the memo.")
