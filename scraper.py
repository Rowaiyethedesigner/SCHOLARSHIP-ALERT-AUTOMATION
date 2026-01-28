import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import re

# ==========================================================
# CONFIG
# ==========================================================
BACKEND_INGEST_URL = "https://scholarship-alert-backend.onrender.com/ingest/calls"

HEADERS = {
    "User-Agent": "ScholarshipAlertBot/1.0"
}

# ==========================================================
# LOGGING
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==========================================================
# AI TAGGING MODELS
# ==========================================================

DEGREE_MODEL = {
    "PhD": ["phd", "doctoral", "doctorate"],
    "MEng": ["meng", "master of engineering"],
    "MSc": ["msc", "master of science"],
    "Postgraduate": ["postgraduate", "graduate"],
}

FIELD_MODEL = {
    "Artificial Intelligence": ["ai", "artificial intelligence", "machine learning", "data science"],
    "Engineering": ["engineering", "mechanical", "electrical", "civil", "software"],
    "Agriculture": ["agriculture", "farming", "agritech", "smart farm"],
    "Health": ["health", "medical", "biotech"],
    "Climate": ["climate", "environment", "sustainability", "renewable"],
}

SDG_MODEL = {
    "SDG2": ["agriculture", "food", "farming"],
    "SDG3": ["health", "medical"],
    "SDG4": ["education", "scholarship", "learning"],
    "SDG9": ["engineering", "technology", "innovation"],
    "SDG13": ["climate", "environment", "sustainability"],
}

THEME_MODEL = {
    "Smart Systems": ["ai", "automation", "smart", "intelligent"],
    "Sustainability": ["sustainability", "climate", "green", "renewable"],
    "Innovation": ["innovation", "technology", "research"],
    "Development": ["development", "global", "international"],
}

# ==========================================================
# AI ENGINE
# ==========================================================

def normalize(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\s]", "", text.lower())


def detect_category(model: dict, text: str):
    scores = {}
    for label, keywords in model.items():
        score = 0
        for kw in keywords:
            if kw in text:
                score += 1
        if score > 0:
            scores[label] = score
    return scores


def ai_tag(title: str, description: str = ""):
    text = normalize(title + " " + description)

    degree_scores = detect_category(DEGREE_MODEL, text)
    field_scores = detect_category(FIELD_MODEL, text)
    sdg_scores = detect_category(SDG_MODEL, text)
    theme_scores = detect_category(THEME_MODEL, text)

    degree = max(degree_scores, key=degree_scores.get) if degree_scores else "Postgraduate"
    field = max(field_scores, key=field_scores.get) if field_scores else "General"
    theme = max(theme_scores, key=theme_scores.get) if theme_scores else "Education"
    sdgs = list(sdg_scores.keys()) if sdg_scores else ["SDG4"]

    confidence = (
        len(degree_scores) +
        len(field_scores) +
        len(theme_scores) +
        len(sdg_scores)
    ) / 10.0

    return {
        "degree_level": degree,
        "field": field,
        "theme": theme,
        "sdg_tags": ",".join(sdgs),
        "confidence_score": round(min(confidence, 1.0), 2)
    }

# ==========================================================
# HELPERS
# ==========================================================

def default_deadline():
    return (datetime.now() + timedelta(days=180)).date().isoformat()


def ingest(payload):
    response = requests.post(
        BACKEND_INGEST_URL,
        json=payload,
        timeout=20
    )

    if response.status_code in (200, 201):
        logging.info(f"Ingested: {payload['title']}")
    else:
        logging.warning(
            f"Failed ({response.status_code}): {payload['title']} | {response.text}"
        )

# ==========================================================
# SOURCE 1 — UNIVERSITYSTUDY.CA
# ==========================================================

def scrape_universitystudy():
    logging.info("Scraping universitystudy.ca")
    url = "https://www.universitystudy.ca/scholarships/"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    count = 0
    for article in soup.find_all("article"):
        title_el = article.find("h2")
        link_el = article.find("a")

        if not title_el or not link_el:
            continue

        title = title_el.get_text(strip=True)
        link = link_el.get("href")

        if not link.startswith("http"):
            continue

        ai_data = ai_tag(title)

        payload = {
            "title": title,
            "host_country": "Canada",
            "field": ai_data["field"],
            "theme": ai_data["theme"],
            "degree_level": ai_data["degree_level"],
            "funding_type": "Unknown",
            "deadline": default_deadline(),
            "source_url": link,
            "sdg_tags": ai_data["sdg_tags"],
            "source_name": "universitystudy.ca",
            "confidence_score": ai_data["confidence_score"],
        }

        ingest(payload)
        count += 1

    logging.info(f"universitystudy.ca: {count} items processed")

# ==========================================================
# SOURCE 2 — SCHOLARSHIP-POSITIONS.COM
# ==========================================================

def scrape_scholarshippositions():
    logging.info("Scraping scholarship-positions.com")
    url = "https://scholarship-positions.com/"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    count = 0
    for post in soup.select("h3.entry-title a"):
        title = post.get_text(strip=True)
        link = post.get("href")

        ai_data = ai_tag(title)

        payload = {
            "title": title,
            "host_country": "Various",
            "field": ai_data["field"],
            "theme": ai_data["theme"],
            "degree_level": ai_data["degree_level"],
            "funding_type": "Unknown",
            "deadline": default_deadline(),
            "source_url": link,
            "sdg_tags": ai_data["sdg_tags"],
            "source_name": "scholarship-positions.com",
            "confidence_score": ai_data["confidence_score"],
        }

        ingest(payload)
        count += 1

    logging.info(f"scholarship-positions.com: {count} items processed")

# ==========================================================
# MAIN
# ==========================================================

def main():
    logging.info("Starting AI-powered multi-source scraping run")

    scrape_universitystudy()
    scrape_scholarshippositions()

    logging.info("Scraping run completed successfully")

if __name__ == "__main__":
    main()
