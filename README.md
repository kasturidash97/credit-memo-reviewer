# Reviewable AI credit memo (draft tool)

A small project to learn how an AI-drafted credit memo can be checked and reviewed by a human.

## What it does
1. Reads the standalone Balance Sheet and Profit and Loss from a public annual report (J. Kumar Infraprojects, FY2024-25, BSE filing) with Python.
2. Calculates ratios (EBITDA margin, debt to equity, interest cover) and checks the statements add up.
3. Builds a facts table where every number has its PDF page.
4. Asks Gemini (free tier) to draft four memo sections using only that table, with a source tag after each number.
5. A script checks that every number in the memo exists in the facts table.
6. A reviewer writes a comment on one section. Only that section is rewritten. Every version and comment is saved in history.json.
7. A Streamlit page shows the memo, the facts, the check and the review box.

## Limits (honest)
- One company, two years of data.
- The number check only confirms that a number exists in the table. It does not check that it sits next to the right label, and it does not catch opinions. A human must read the memo.
- The memo text is written by an LLM. I did not train or fine-tune any model.
- This is a learning project, not a credit decision tool.

## Data
Public filing only: https://www.bseindia.com/xml-data/corpfiling/AttachHis/afa43af4-437c-4f58-9f78-712054b0e355.pdf
Download it into a folder called data and name it jkumar_ar_2025.pdf. No employer or customer data is used.

## Run it
1. pip install -r requirements.txt
2. Get a free Gemini API key from Google AI Studio and save it in a file called .env as GEMINI_API_KEY=your key. Never upload this file.
3. python3 extract_numbers.py then python3 facts.py
4. python3 memo.py
5. python3 check_memo.py memo_v1.json
6. streamlit run app.py

Notes: amounts are in Rs lakh. PDF page numbers are PDF viewer pages (printed page plus 2).
