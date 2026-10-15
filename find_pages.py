import pdfplumber

with pdfplumber.open("data/jkumar_ar_2025.pdf") as pdf:
    for i in range(140, 170):
        text = pdf.pages[i].extract_text() or ""
        if "STANDALONE BALANCE SHEET" in text or "STANDALONE STATEMENT OF PROFIT AND LOSS" in text:
            print("index", i, "= PDF viewer page", i + 1)
