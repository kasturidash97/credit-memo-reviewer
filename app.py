import glob
import json
import os
import re
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

st.set_page_config(page_title="Credit memo draft", layout="wide")
st.title("Draft credit memo: J. Kumar Infraprojects")
st.caption("Source: FY2024-25 annual report, public BSE filing. Amounts in Rs lakh. "
           "Draft for human review. Not an approval.")

facts = pd.read_csv("facts.csv")

def version_number(filename):
    return int(re.findall(r"\d+", filename)[0])

files = sorted(glob.glob("memo_v[0-9]*.json"), key=version_number)

def check(memo, facts):
    allowed = []
    for col in ["FY2024-25", "FY2023-24"]:
        allowed += [float(x) for x in pd.to_numeric(facts[col], errors="coerce").dropna()]
    flags = []
    for title, text in memo.items():
        clean = re.sub(r"\[[^\]]{0,}\]", " ", text)
        clean = re.sub(r"FY\s?\d{4}(-\d{2,4})?", " ", clean)
        clean = re.sub(r"\b(19|20)\d{2}\b", " ", clean)
        found = []
        for n in re.findall(r"\d[\d,]{0,}\.?\d{0,}", clean):
            n = n.strip(",.")
            if n:
                found.append(n)
        for n in found:
            x = float(n.replace(",", ""))
            ok = any(abs(abs(x) - abs(a)) <= 0.011 + abs(a) / 2000 for a in allowed)
            if not ok:
                flags.append(title + ": number not in facts table: " + n)
        if found and "[" not in text:
            flags.append(title + ": has numbers but no source tag")
    return flags

def revise(memo, title, comment, facts):
    facts_text = facts.to_csv(index=False)
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
""" + memo[title] + """

REVIEWER COMMENT:
""" + comment + """

FACTS TABLE:
""" + facts_text
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    for m in ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]:
        try:
            reply = client.models.generate_content(
                model=m, contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2))
            return reply.text.strip()
        except Exception as e:
            st.warning("Model " + m + " failed: " + str(e)[:100])
    return None

if not files:
    st.error("No memo files found. Run memo.py first.")
    st.stop()

chosen = st.sidebar.selectbox("Memo version", files, index=len(files) - 1)
memo = json.load(open(chosen))

tab_memo, tab_review, tab_facts, tab_check, tab_history = st.tabs(
    ["Memo", "Review", "Facts table", "Number check", "History"])

with tab_memo:
    st.subheader("Showing " + chosen)
    for title, text in memo.items():
        st.markdown("#### " + title)
        st.write(text)

with tab_review:
    st.write("You are the reviewer. Pick one section, write your comment, and only that section is rewritten.")
    if chosen != files[-1]:
        st.info("You are looking at an older version. Switch the sidebar to " + files[-1] + " to revise the latest.")
    else:
        section = st.selectbox("Section", list(memo.keys()))
        comment = st.text_area("Your reviewer comment (your own words)")
        if st.button("Revise this section"):
            if not comment.strip():
                st.error("Write a comment first.")
            else:
                with st.spinner("Asking Gemini..."):
                    new_text = revise(memo, section, comment, facts)
                if new_text is None:
                    st.error("No model worked. Wait a minute and try again.")
                else:
                    new_memo = dict(memo)
                    new_memo[section] = new_text
                    new_file = "memo_v%d.json" % (version_number(chosen) + 1)
                    json.dump(new_memo, open(new_file, "w"), indent=2)
                    history = []
                    if os.path.exists("history.json"):
                        history = json.load(open("history.json"))
                    history.append({"time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "from": chosen, "to": new_file, "section": section,
                                    "comment": comment, "old": memo[section], "new": new_text})
                    json.dump(history, open("history.json", "w"), indent=2)
                    st.session_state["last"] = {"file": new_file, "section": section,
                                                "old": memo[section], "new": new_text,
                                                "flags": check(new_memo, facts)}
                    st.rerun()
    last = st.session_state.get("last")
    if last:
        st.success("Saved " + last["file"] + ". Only the section " + last["section"] + " changed.")
        left, right = st.columns(2)
        left.markdown("#### Old")
        left.write(last["old"])
        right.markdown("#### New")
        right.write(last["new"])
        if last["flags"]:
            for f in last["flags"]:
                st.warning(f)
        else:
            st.success("Number check: PASS. Now read it yourself. Numbers can pass while an opinion slips in.")

with tab_facts:
    st.write("The AI only sees this table. Every number in the memo must come from here.")
    st.dataframe(facts, width="stretch")

with tab_check:
    flags = check(memo, facts)
    if flags:
        for f in flags:
            st.warning(f)
        st.write("A human must look at these before using the memo.")
    else:
        st.success("PASS: every number is in the facts table, and numbers have source tags.")
    st.caption("This check does not catch wrong labels or opinions. Read the memo yourself.")

with tab_history:
    if os.path.exists("history.json"):
        history = json.load(open("history.json"))
        st.dataframe(pd.DataFrame(history)[["time", "from", "to", "section", "comment"]], width="stretch")
        st.write("Old and new text for every change are in history.json.")
    else:
        st.write("No revisions yet.")
