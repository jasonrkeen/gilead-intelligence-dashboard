import feedparser
import pandas as pd


GILEAD_NEWS_RSS = "https://www.gilead.com/news-and-press/press-room/press-releases/rss"

SEC_FILINGS_RSS = (
    "https://www.sec.gov/cgi-bin/browse-edgar?"
    "action=getcompany&CIK=GILD&type=&dateb=&owner=exclude&count=40&output=atom"
)


KEYWORDS = {
    "Regulatory": [
        "FDA", "approval", "approved", "regulatory", "clinical", "trial",
        "Phase 1", "Phase 2", "Phase 3", "PDUFA", "CRL", "fast track",
        "breakthrough therapy", "submission", "review", "advisory committee",
    ],
    "Legal / Compliance": [
        "lawsuit", "settlement", "investigation", "compliance", "litigation",
        "DOJ", "SEC probe", "subpoena", "penalty", "fine", "fraud",
        "whistleblower",
    ],
    "Geopolitical": [
        "China", "sanctions", "war", "conflict", "geopolitical", "Russia",
        "Middle East", "Iran", "Tehran", "Hormuz", "tariff",
        "export controls", "trade restrictions", "supply chain disruption",
        "embargo",
    ],
    "Financial": [
        "earnings", "revenue", "guidance", "quarter", "financial", "results",
        "sales", "EPS", "beat", "miss", "outlook", "forecast", "margin",
        "profit", "loss",
    ],
    "Product / Pipeline": [
        "HIV", "oncology", "Trodelvy", "Veklury", "Biktarvy", "pipeline",
        "treatment", "therapy", "readout", "data", "endpoint",
        "trial results", "efficacy", "safety", "launch",
    ],
    "SEC Filing": [
        "10-K", "10-Q", "8-K", "Form 4", "DEF 14A", "proxy", "filing",
        "annual report", "quarterly report",
    ],
}


URGENCY_KEYWORDS = [
    "warning", "investigation", "lawsuit", "sanctions", "conflict",
    "recall", "breach", "cyber", "decline", "miss", "risk", "CRL",
    "failure", "delay", "halted", "terminated", "downgrade", "cut guidance",
]


NEWS_COLUMNS = [
    "source",
    "title",
    "link",
    "published",
    "summary",
]


def _empty_news_frame():
    """
    Return a consistent empty news dataframe.
    """

    return pd.DataFrame(columns=NEWS_COLUMNS)


def fetch_rss_feed(feed_url, source_name):
    """
    Fetch RSS/Atom feed items and return a dataframe.

    If the feed is unavailable or malformed, return an empty dataframe so the
    dashboard can continue running.
    """

    try:
        feed = feedparser.parse(feed_url)
    except Exception:
        return _empty_news_frame()

    if getattr(feed, "bozo", False) and not getattr(feed, "entries", []):
        return _empty_news_frame()

    rows = []

    for entry in feed.entries:
        rows.append({
            "source": source_name,
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", entry.get("updated", "")),
            "summary": entry.get("summary", ""),
        })

    if not rows:
        return _empty_news_frame()

    return pd.DataFrame(rows, columns=NEWS_COLUMNS)


def classify_news_item(text):
    """
    Classify a news item based on keyword matches.
    """

    if not text:
        return "General"

    text_lower = str(text).lower()
    matched_categories = []

    for category, keywords in KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched_categories.append(category)
                break

    if not matched_categories:
        return "General"

    return ", ".join(matched_categories)


def calculate_urgency_score(text):
    """
    Basic urgency score based on sensitive keywords.
    """

    if not text:
        return 1

    text_lower = str(text).lower()
    score = 1

    for keyword in URGENCY_KEYWORDS:
        if keyword.lower() in text_lower:
            score += 1

    return min(score, 5)


def clean_news_dataframe(news_df):
    """
    Clean and enrich combined news dataframe.
    """

    if news_df is None or news_df.empty:
        return pd.DataFrame(columns=[
            "published",
            "source",
            "category",
            "urgency_score",
            "title",
            "link",
        ])

    news_df = news_df.copy()

    for col in NEWS_COLUMNS:
        if col not in news_df.columns:
            news_df[col] = ""

    news_df["combined_text"] = (
        news_df["title"].fillna("") + " " + news_df["summary"].fillna("")
    )

    news_df["category"] = news_df["combined_text"].apply(classify_news_item)
    news_df["urgency_score"] = news_df["combined_text"].apply(calculate_urgency_score)

    news_df["published_dt"] = pd.to_datetime(
        news_df["published"],
        errors="coerce",
        utc=True,
    )

    news_df = news_df.sort_values(
        "published_dt",
        ascending=False,
        na_position="last",
    )

    return news_df[[
        "published",
        "source",
        "category",
        "urgency_score",
        "title",
        "link",
    ]].reset_index(drop=True)


def build_news_tracker():
    """
    Build combined Gilead news + SEC filings tracker.
    """

    gilead_news = fetch_rss_feed(GILEAD_NEWS_RSS, "Gilead News")
    sec_filings = fetch_rss_feed(SEC_FILINGS_RSS, "SEC Filings")

    news_df = pd.concat([gilead_news, sec_filings], ignore_index=True)

    return clean_news_dataframe(news_df)


def get_news_summary(news_df):
    """
    Create summary metrics for dashboard.
    """

    if news_df is None or news_df.empty:
        return {
            "total_items": 0,
            "top_category": "N/A",
            "max_urgency": 0,
            "latest_headline": "N/A",
        }

    top_category = (
        news_df["category"].value_counts().idxmax()
        if "category" in news_df.columns and not news_df["category"].empty
        else "N/A"
    )
    max_urgency = (
        news_df["urgency_score"].max()
        if "urgency_score" in news_df.columns
        else 0
    )
    latest_headline = (
        news_df.iloc[0]["title"]
        if "title" in news_df.columns and not news_df.empty
        else "N/A"
    )

    return {
        "total_items": len(news_df),
        "top_category": top_category,
        "max_urgency": max_urgency,
        "latest_headline": latest_headline,
    }


def calculate_news_risk_score(news_df):
    """
    Convert recent news / filing activity into a 1-5 risk score.

    Higher score = more urgent or risk-heavy news flow.
    """

    if news_df is None or news_df.empty:
        return {
            "news_risk_score": 1,
            "news_risk_label": "Low",
            "news_risk_summary": "No recent news or filing items detected.",
        }

    max_urgency = news_df["urgency_score"].max() if "urgency_score" in news_df.columns else 1
    avg_urgency = news_df["urgency_score"].mean() if "urgency_score" in news_df.columns else 1

    risk_categories = [
        "Legal / Compliance",
        "Geopolitical",
        "Regulatory",
    ]

    if "category" in news_df.columns:
        risk_hits = news_df[
            news_df["category"].str.contains(
                "|".join(risk_categories),
                case=False,
                na=False,
            )
        ]
    else:
        risk_hits = pd.DataFrame()

    risk_hit_count = len(risk_hits)

    score = 1

    if max_urgency >= 5:
        score += 2
    elif max_urgency >= 4:
        score += 1.5
    elif max_urgency >= 3:
        score += 1

    if avg_urgency >= 3:
        score += 1

    if risk_hit_count >= 5:
        score += 1
    elif risk_hit_count >= 2:
        score += 0.5

    score = max(1, min(5, score))

    if score < 2:
        label = "Low"
    elif score < 3.5:
        label = "Moderate"
    elif score < 4.5:
        label = "Elevated"
    else:
        label = "High"

    return {
        "news_risk_score": score,
        "news_risk_label": label,
        "news_risk_summary": (
            f"News risk is {label.lower()} with max urgency {max_urgency}/5, "
            f"average urgency {avg_urgency:.1f}/5, and {risk_hit_count} risk-category items."
        ),
    }
