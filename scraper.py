import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging

# =========================
# CONFIG
# =========================
BACKEND_INGEST_URL = "https://scholarship-alert-backend.onrender.com/ingest/calls"

SOURCE_URL = "https://www.universitystudy.ca/scholarships/"

SOURCE_NAME = "prototype_scraper"
CONFIDENCE_SCORE = 0.65

HEADERS = {
    "User-Agent": "ScholarshipAlertBot/1.0 (+https://github.com/your-repo)"
}

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
    """Fallback deadline: 6 months from now"""
    return (datetime.now() + timedelta(days=180)).date().isoformat()

# =========================
# SCRAPER
# =========================
def scrape_scholarships():
    logging.info("Fetching scholarship source page...")
    response = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    scholarships = []

    # Prototype selector (simple & safe)
    for article in soup.find_all("article"):
        title_el = article.find("h2")
        link_el = article.find("a")

        if not title_el or not link_el:
            continue

        title = title_el.get_text(strip=True)
        link = link_el.get("href")

        if not link.startswith("http"):
            continue

        scholarships.append({
            "title": title,
            "source_url": link
        })

    logging.info(f"Found {len(scholarships)} scholarships")
    return scholarships

# =========================
# INGESTION
# =========================
def ingest_scholarship(item):
    payload = {
        "title": item["title"],
        "host_country": "Canada",
        "field": "General",
        "theme": "Higher Education",
        "degree_level": "Postgraduate",
        "funding_type": "Unknown",
        "deadline": default_deadline(),
        "source_url": item["source_url"],
        "sdg_tags": "SDG4",
        "source_name": SOURCE_NAME,
        "confidence_score": CONFIDENCE_SCORE
    }

    response = requests.post(
        BACKEND_INGEST_URL,
        json=payload,
        timeout=15
    )

    if response.status_code in (200, 201):
        logging.info(f"Ingested: {item['title']}")
    else:
        logging.warning(
            f"Failed ({response.status_code}): {item['title']} | {response.text}"
        )

# =========================
# MAIN
# =========================
def main():
    scholarships = scrape_scholarships()

    if not scholarships:
        logging.warning("No scholarships found. Exiting.")
        return

    for item in scholarships:
        ingest_scholarship(item)

    logging.info("Scraping run completed.")

if __name__ == "__main__":
    main()
