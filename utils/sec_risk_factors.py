import re
import requests
import pandas as pd
from bs4 import BeautifulSoup


TEN_K_URL = "https://www.sec.gov/Archives/edgar/data/882095/000088209526000006/gild-20251231.htm"

HEADERS = {
    "User-Agent": "Jason Keen gilead-intelligence-dashboard keenjasonr@gmail.com"
}


RISK_KEYWORDS = {
    "Geopolitical": [
        "geopolitical", "war", "conflict", "sanctions", "terrorism",
        "political instability", "civil unrest", "china", "russia",
        "iran", "middle east", "tariff", "export controls",
        "trade restrictions",
    ],
    "Regulatory / Policy": [
        "regulatory", "regulation", "pricing", "reimbursement",
        "healthcare reform", "government", "fda", "medicare",
        "medicaid", "drug pricing", "policy",
    ],
    "Supply Chain": [
        "supply chain", "manufacturing", "supplier", "shortage",
        "distribution", "logistics", "inventory", "raw materials",
        "outsourcing",
    ],
    "Cybersecurity": [
        "cybersecurity", "cyber attack", "data breach",
        "information security", "ransomware", "hacking",
    ],
    "Clinical / Product": [
        "clinical trial", "approval", "pipeline", "adverse event",
        "safety", "efficacy", "trial failure", "delay",
        "endpoint", "readout",
    ],
    "Competition": [
        "competition", "competitive", "generic", "biosimilar",
        "patent", "exclusivity", "market share", "pricing pressure",
    ],
}


def fetch_10k_text():
    """
    Fetch the 10-K filing text from the SEC archive.

    Returns an empty string if the request fails so the Streamlit app can
    continue running instead of crashing.
    """

    try:
        response = requests.get(TEN_K_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    return soup.get_text(" ", strip=True)


def extract_risk_factors_section(text):
    """
    Attempt to isolate Item 1A. Risk Factors from the 10-K.

    If the section cannot be isolated, the function falls back to the full
    filing text. If no filing text is available, it returns an empty string.
    """

    if not text:
        return ""

    text_clean = re.sub(r"\s+", " ", text)

    start_patterns = [
        r"Item\s+1A\.?\s+Risk\s+Factors",
        r"ITEM\s+1A\.?\s+RISK\s+FACTORS",
    ]

    end_patterns = [
        r"Item\s+1B\.?",
        r"ITEM\s+1B\.?",
        r"Item\s+1C\.?",
        r"ITEM\s+1C\.?",
        r"Item\s+2\.?",
        r"ITEM\s+2\.?",
    ]

    start_match = None
    for pattern in start_patterns:
        start_match = re.search(pattern, text_clean, re.IGNORECASE)
        if start_match:
            break

    if not start_match:
        return text_clean

    section_text = text_clean[start_match.start():]

    end_match = None
    for pattern in end_patterns:
        candidate = re.search(pattern, section_text, re.IGNORECASE)
        if candidate and candidate.start() > 100:
            end_match = candidate
            break

    if end_match:
        section_text = section_text[:end_match.start()]

    return section_text


def count_risk_keywords(section_text, keyword_dict=None):
    """
    Count keyword matches by risk category.

    Multi-word terms are matched as complete phrases. Single-word terms are
    matched with word boundaries to reduce false positives.
    """

    if keyword_dict is None:
        keyword_dict = RISK_KEYWORDS

    results = []

    if not section_text:
        for category in keyword_dict:
            results.append({
                "Risk Category": category,
                "Keyword Count": 0,
                "Matched Terms": "",
            })

        return pd.DataFrame(results).sort_values(
            "Keyword Count",
            ascending=False,
        )

    lower_text = section_text.lower()

    for category, keywords in keyword_dict.items():
        total_count = 0
        matched_terms = []

        for keyword in keywords:
            keyword_clean = keyword.lower().strip()
            pattern = r"\b" + re.escape(keyword_clean) + r"\b"
            matches = re.findall(pattern, lower_text)

            if matches:
                total_count += len(matches)
                matched_terms.append(keyword)

        results.append({
            "Risk Category": category,
            "Keyword Count": total_count,
            "Matched Terms": ", ".join(matched_terms),
        })

    return pd.DataFrame(results).sort_values(
        "Keyword Count",
        ascending=False,
    )


def calculate_sec_risk_score(risk_df):
    """
    Convert keyword intensity into a 1-5 SEC risk score.

    This is a directional monitoring score. It should not be interpreted as a
    probability of loss or as a standalone investment conclusion.
    """

    if risk_df is None or risk_df.empty:
        return {
            "sec_risk_score": 1,
            "sec_risk_label": "Low",
        }

    total_mentions = risk_df["Keyword Count"].sum()

    if total_mentions <= 0:
        score = 1
    elif total_mentions < 200:
        score = 2
    elif total_mentions < 400:
        score = 3
    elif total_mentions < 700:
        score = 4
    else:
        score = 5

    labels = {
        1: "Low",
        2: "Low / Moderate",
        3: "Moderate",
        4: "Elevated",
        5: "High",
    }

    return {
        "sec_risk_score": score,
        "sec_risk_label": labels[score],
    }


def build_sec_risk_factor_analysis():
    """
    Build SEC risk factor keyword analysis for the dashboard.

    Returns a dictionary containing the risk dataframe, top category,
    total mentions, word count, and directional SEC risk score.
    """

    filing_text = fetch_10k_text()
    risk_section = extract_risk_factors_section(filing_text)
    risk_df = count_risk_keywords(risk_section)

    section_word_count = len(risk_section.split()) if risk_section else 0
    total_mentions = risk_df["Keyword Count"].sum() if not risk_df.empty else 0

    if total_mentions > 0:
        risk_df["Share of Mentions"] = (
            risk_df["Keyword Count"] / total_mentions * 100
        )
    else:
        risk_df["Share of Mentions"] = 0.0

    risk_df["Normalized Score"] = (
        risk_df["Keyword Count"] / max(1, section_word_count) * 10000
    )

    top_category = (
        risk_df.iloc[0]["Risk Category"]
        if not risk_df.empty and total_mentions > 0
        else "N/A"
    )

    sec_risk_score = calculate_sec_risk_score(risk_df)

    return {
        "risk_df": risk_df,
        "top_category": top_category,
        "total_mentions": total_mentions,
        "section_word_count": section_word_count,
        "sec_risk_score": sec_risk_score,
        "filing_available": bool(filing_text),
        "risk_section_available": bool(risk_section),
    }
