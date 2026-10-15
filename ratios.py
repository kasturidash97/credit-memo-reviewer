import re
import pdfplumber
import pandas as pd

df = pd.read_csv("numbers.csv").set_index("item")

def get(item, year):
    return float(df.loc[item, year])

def to_number(s):
    s = s.replace(",", "")
    if s.startswith("(") and s.endswith(")"):
        return -float(s[1:-1])
    return float(s)

def two_numbers(lines, label):
    for line in lines:
        if label in line:
            nums = re.findall(r"\(?\d[\d,]*\.\d+\)?", line)
            return to_number(nums[-2]), to_number(nums[-1])

with pdfplumber.open("data/jkumar_ar_2025.pdf") as pdf:
    bs = (pdf.pages[153].extract_text() or "").split("\n")
    pl = (pdf.pages[154].extract_text() or "").split("\n")

extra = {
    "Total equity and liabilities": two_numbers(bs, "TOTAL EQUITY"),
    "Current tax": two_numbers(pl, "Current tax"),
    "Deferred tax": two_numbers(pl, "Deferred tax"),
}

years = ["FY2024-25", "FY2023-24"]
rows = []
checks = []
for k, year in enumerate(years):
    revenue = get("Revenue from operations", year)
    pbt = get("Profit before tax", year)
    pat = get("Profit for the year", year)
    fin = get("Finance costs", year)
    dep = get("Depreciation", year)
    equity = get("Equity share capital", year) + get("Other equity", year)
    debt = get("Non-current borrowings", year) + get("Current borrowings", year)
    ebitda = pbt + fin + dep

    rows.append({"ratio": "EBITDA (Rs lakh)", "year": year, "value": round(ebitda, 2)})
    rows.append({"ratio": "EBITDA margin %", "year": year, "value": round(ebitda / revenue * 100, 2)})
    rows.append({"ratio": "PAT margin %", "year": year, "value": round(pat / revenue * 100, 2)})
    rows.append({"ratio": "Debt / Equity (x)", "year": year, "value": round(debt / equity, 2)})
    rows.append({"ratio": "Interest cover (x)", "year": year, "value": round((pbt + fin) / fin, 2)})

    gap1 = get("Total assets", year) - extra["Total equity and liabilities"][k]
    checks.append(("Assets = Equity + Liabilities", year, round(gap1, 2), abs(gap1) < 0.05))
    gap2 = pbt - extra["Current tax"][k] - extra["Deferred tax"][k] - pat
    checks.append(("PBT - taxes = Profit for the year", year, round(gap2, 2), abs(gap2) < 0.05))

ratios = pd.DataFrame(rows).pivot(index="ratio", columns="year", values="value")[years]
print(ratios.to_string())
print()
for name, year, gap, ok in checks:
    print(("PASS" if ok else "FLAG"), "|", name, "|", year, "| gap:", gap)

growth = (get("Revenue from operations", years[0]) / get("Revenue from operations", years[1]) - 1) * 100
print()
print("Revenue growth %:", round(growth, 1))

ratios.to_excel("ratios.xlsx")
print("Saved ratios.xlsx")
