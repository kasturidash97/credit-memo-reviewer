import pandas as pd

df = pd.read_csv("numbers.csv").set_index("item")
Y1, Y0 = "FY2024-25", "FY2023-24"

def v(item, y):
    return float(df.loc[item, y])

def page(item):
    return int(df.loc[item, "pdf_page"])

rows = []

def add(label, a, b, unit, src):
    rows.append({"fact": label, Y1: round(a, 2), Y0: None if b is None else round(b, 2),
                 "unit": unit, "source": src})

for item in ["Revenue from operations", "Profit before tax", "Profit for the year",
             "Finance costs", "Depreciation", "Total assets"]:
    add(item, v(item, Y1), v(item, Y0), "Rs lakh", "PDF page %d" % page(item))

def debt(y):
    return v("Non-current borrowings", y) + v("Current borrowings", y)

def equity(y):
    return v("Equity share capital", y) + v("Other equity", y)

def pbit(y):
    return v("Profit before tax", y) + v("Finance costs", y)

def ebitda(y):
    return pbit(y) + v("Depreciation", y)

add("Total borrowings", debt(Y1), debt(Y0), "Rs lakh", "PDF page 154")
add("Total equity", equity(Y1), equity(Y0), "Rs lakh", "PDF page 154")
add("Profit before interest and tax (PBIT)", pbit(Y1), pbit(Y0), "Rs lakh",
    "PDF page 155, calculated: profit before tax + finance costs, includes other income")
add("EBITDA", ebitda(Y1), ebitda(Y0), "Rs lakh", "PDF page 155, calculated")
add("EBITDA margin", ebitda(Y1) / v("Revenue from operations", Y1) * 100,
    ebitda(Y0) / v("Revenue from operations", Y0) * 100, "%", "calculated")
add("PAT margin", v("Profit for the year", Y1) / v("Revenue from operations", Y1) * 100,
    v("Profit for the year", Y0) / v("Revenue from operations", Y0) * 100, "%", "calculated")
add("Debt / Equity", debt(Y1) / equity(Y1), debt(Y0) / equity(Y0), "x", "calculated, borrowings only")
add("Interest cover", pbit(Y1) / v("Finance costs", Y1), pbit(Y0) / v("Finance costs", Y0),
    "x", "calculated: PBIT / finance costs")
g = (v("Revenue from operations", Y1) / v("Revenue from operations", Y0) - 1) * 100
add("Revenue growth", g, None, "%", "calculated, FY2024-25 over FY2023-24")

out = pd.DataFrame(rows)
out.to_csv("facts.csv", index=False)
print(out.to_string(index=False))
print("Saved facts.csv with", len(out), "rows")
