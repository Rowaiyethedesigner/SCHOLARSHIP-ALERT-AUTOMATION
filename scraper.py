import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging

# =========================
# CONFIG
# =========================
BACKEND_INGEST_URL = "https://scholarship-alert-backend.onrender.com/ingest/calls"

HEADERS = {
    "User-Agent": "ScholarshipAlertBot/1.0"
}

CONFIDENCE_SCORE = 0.65

# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =========================
# HELPERS
# =========================
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

# =========================
# SOURCE 1: UNIVERSITYSTUDY.CA
# =========================
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

        payload = {
            "title": title,
            "host_country": "Canada",
            "field": "General",
            "theme": "Higher Education",
            "degree_level": "Postgraduate",
            "funding_type": "Unknown",
            "deadline": default_deadline(),
            "source_url": link,
            "sdg_tags": "SDG4",
            "source_name": "universitystudy.ca",
            "confidence_score": CONFIDENCE_SCORE,
        }

        ingest(payload)
        count += 1

    logging.info(f"universitystudy.ca: {count} items processed")

# =========================
# SOURCE 2: SCHOLARSHIP POSITIONS
# =========================
def scrape_scholarshippositions():
    logging.info("Scraping scholarshippositions.com")
    url = "https://scholarship-positions.com/"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    count = 0
    for post in soup.select("h3.entry-title a"):
        title = post.get_text(strip=True)
        link = post.get("href")

        payload = {
            "title": title,
            "host_country": "Various",
            "field": "General",
            "theme": "International Scholarships",
            "degree_level": "Postgraduate",
            "funding_type": "Unknown",
            "deadline": default_deadline(),
            "source_url": link,
            "sdg_tags": "SDG4",
            "source_name": "scholarship-positions.com",
            "confidence_score": CONFIDENCE_SCORE,
        }

        ingest(payload)
        count += 1

    logging.info(f"scholarship-positions.com: {count} items processed")

# =========================
# MAIN
# =========================
def main():
    logging.info("Starting multi-source scraping run")

    scrape_universitystudy()
    scrape_scholarshippositions()

    logging.info("Scraping run completed")

if __name__ == "__main__":
    main()
