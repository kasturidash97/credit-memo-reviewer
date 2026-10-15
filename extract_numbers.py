import re
import pdfplumber
import pandas as pd

BS_INDEX = 153
PL_INDEX = 154

def to_number(s):
    s = s.replace(",", "")
    if s.startswith("(") and s.endswith(")"):
        return -float(s[1:-1])
    return float(s)

def read_lines(pdf, index):
    return (pdf.pages[index].extract_text() or "").split("\n")

def find_values(lines, label, nth=1):
    hits = 0
    for line in lines:
        if label in line:
            hits += 1
            if hits == nth:
                nums = re.findall(r"\(?\d[\d,]*\.\d+\)?", line)
                return to_number(nums[-2]), to_number(nums[-1])
    return None, None

wanted = [
    ("Revenue from operations", "PL", "Revenue from operations", 1),
    ("Finance costs", "PL", "Finance costs", 1),
    ("Depreciation", "PL", "Depreciation expense", 1),
    ("Profit before tax", "PL", "Profit before tax", 1),
    ("Profit for the year", "PL", "Profit for the year", 1),
    ("Total assets", "BS", "TOTAL ASSETS", 1),
    ("Equity share capital", "BS", "Equity share capital", 1),
    ("Other equity", "BS", "Other equity", 1),
    ("Non-current borrowings", "BS", "(i) Borrowings", 1),
    ("Current borrowings", "BS", "(i) Borrowings", 2),
]

rows = []
with pdfplumber.open("data/jkumar_ar_2025.pdf") as pdf:
    pages = {"BS": (BS_INDEX, read_lines(pdf, BS_INDEX)),
             "PL": (PL_INDEX, read_lines(pdf, PL_INDEX))}
    for name, stmt, label, nth in wanted:
        idx, lines = pages[stmt]
        fy25, fy24 = find_values(lines, label, nth)
        rows.append({"item": name, "FY2024-25": fy25, "FY2023-24": fy24,
                     "pdf_page": idx + 1})

df = pd.DataFrame(rows)
print(df.to_string(index=False))
df.to_csv("numbers.csv", index=False)
print("Saved numbers.csv (all in Rs lakh)")
