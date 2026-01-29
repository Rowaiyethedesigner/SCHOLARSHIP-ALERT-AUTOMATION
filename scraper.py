import requests
from bs4 import BeautifulSoup
import time
import re
import hashlib
from datetime import datetime

# =========================
# CONFIG
# =========================

INGEST_API = "https://scholarship-alert-backend.onrender.com/ingest/calls"
HEADERS = {"Content-Type": "application/json"}

# =========================
# SOURCES (REAL PRODUCTION SOURCES)
# =========================

SOURCES = [

    # ================= GLOBAL =================
    "https://www.scholarships.com",
    "https://www.internationalscholarships.com",
    "https://www.opportunitiesforafricans.com",
    "https://fundingopportunities.com",
    "https://www.scholarshipportal.com",
    "https://www.studyabroad.com",
    "https://www.prospects.ac.uk",
    "https://www.findaphd.com",
    "https://www.findamasters.com",
    "https://www.postgrad.com",

    # ================= CANADA =================
    "https://www.scholarships.gc.ca",
    "https://www.educanada.ca",
    "https://www.canada.ca/en/services/education/student-aid/grants-scholarships.html",
    "https://www.nserc-crsng.gc.ca",
    "https://www.cihr-irsc.gc.ca",
    "https://www.sshrc-crsh.gc.ca",
    "https://vanier.gc.ca",
    "https://banting.fellowships-bourses.gc.ca",
    "https://www.mitacs.ca",

    # Universities
    "https://www.utoronto.ca",
    "https://www.ubc.ca",
    "https://www.mcgill.ca",
    "https://uwaterloo.ca",
    "https://www.uottawa.ca",
    "https://www.concordia.ca",
    "https://www.yorku.ca",
    "https://www.ualberta.ca",
    "https://www.ucalgary.ca",
    "https://www.sfu.ca",

    # ================= USA =================
    "https://www.fulbrightprogram.org",
    "https://foreign.fulbrightonline.org",
    "https://www.nsf.gov/funding",
    "https://www.usaid.gov",
    "https://www.ed.gov",
    "https://www.state.gov/education-culture-exchange",
    "https://www.worldlearning.org",
    "https://www.iie.org",

    # Universities
    "https://www.harvard.edu",
    "https://www.stanford.edu",
    "https://www.mit.edu",
    "https://www.berkeley.edu",
    "https://www.princeton.edu",
    "https://www.columbia.edu",
    "https://www.cmu.edu",
    "https://www.caltech.edu",

    # ================= SDG / DEVELOPMENT =================
    "https://www.undp.org",
    "https://www.unep.org",
    "https://www.un.org/sustainabledevelopment",
    "https://www.unesco.org",
    "https://www.fao.org",
    "https://www.unicef.org",
    "https://www.worldbank.org",
    "https://www.afdb.org",
    "https://www.adb.org",
    "https://www.ifad.org",

    # ================= AGRICULTURE / FOOD =================
    "https://www.cgiar.org",
    "https://www.iita.org",
    "https://www.cimmyt.org",
    "https://www.icrisat.org",
    "https://www.irri.org",
    "https://www.agriculturefunders.org",

    # ================= AI / TECH =================
    "https://ai.google/research",
    "https://research.microsoft.com",
    "https://openai.com/research",
    "https://deepmind.com/research",
    "https://www.nature.com/subjects/artificial-intelligence",
    "https://www.springer.com",
    "https://www.ieee.org",

    # ================= FOUNDATIONS =================
    "https://www.gatesfoundation.org",
    "https://www.rockefellerfoundation.org",
    "https://www.moibrahimfoundation.org",
    "https://www.wellcome.org",
    "https://www.carnegie.org",
    "https://www.fordfoundation.org",

    # ================= RESEARCH FUNDING =================
    "https://www.grants.gov",
    "https://cordis.europa.eu",
    "https://ec.europa.eu/info/funding-tenders",
    "https://www.ukri.org",
    "https://www.nihr.ac.uk"
]

# =========================
# SIMPLE AI TAGGER
# =========================

def ai_tag(text: str):
    text = text.lower()

    field = "general"
    if "ai" in text or "artificial intelligence" in text:
        field = "AI"
    elif "engineering" in text:
        field = "Engineering"
    elif "agriculture" in text or "farm" in text:
        field = "Agriculture"
    elif "health" in text:
        field = "Health"
    elif "climate" in text:
        field = "Climate"

    theme = "general"
    if "sustain" in text:
        theme = "Sustainable Development"
    if "sdg" in text:
        theme = "SDG"

    degree = "General"
    if "phd" in text:
        degree = "PhD"
    elif "master" in text:
        degree = "Masters"
    elif "m.eng" in text or "meng" in text:
        degree = "MEng"

    sdg_tags = []
    if "climate" in text:
        sdg_tags.append("SDG13")
    if "education" in text:
        sdg_tags.append("SDG4")
    if "agriculture" in text:
        sdg_tags.append("SDG2")
    if "innovation" in text:
        sdg_tags.append("SDG9")

    confidence = "0.65"

    return {
        "field": field,
        "theme": theme,
        "degree_level": degree,
        "sdg_tags": ",".join(sdg_tags),
        "confidence_score": confidence
    }

# =========================
# HELPERS
# =========================

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

# =========================
# SCRAPER
# =========================

def scrape_site(url):
    results = []

    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        links = soup.find_all("a", href=True)

        for a in links:
            title = clean_text(a.get_text())
            link = a["href"]

            if not title or len(title) < 15:
                continue

            if not link.startswith("http"):
                continue

            text_blob = title.lower()

            tags = ai_tag(text_blob)

            payload = {
                "title": title,
                "host_country": None,
                "field": tags["field"],
                "theme": tags["theme"],
                "degree_level": tags["degree_level"],
                "funding_type": "Scholarship",
                "deadline": None,
                "source_url": link,
                "sdg_tags": tags["sdg_tags"],
                "source_name": url,
                "confidence_score": tags["confidence_score"]
            }

            results.append(payload)

    except Exception as e:
        print(f"[ERROR] {url} -> {e}")

    return results

# =========================
# INGESTION
# =========================

def send_to_api(data):
    try:
        r = requests.post(INGEST_API, json=data, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print("[INGEST ERROR]", r.status_code, r.text)
        else:
            print("[INGESTED]", data["title"][:60])
    except Exception as e:
        print("[API ERROR]", e)

# =========================
# MAIN PIPELINE
# =========================

def run():
    print("=== AI SCHOLARSHIP SCRAPER STARTED ===")

    for src in SOURCES:
        print(f"\n[SCRAPING] {src}")
        data = scrape_site(src)

        for item in data:
            send_to_api(item)
            time.sleep(0.2)

        time.sleep(2)

    print("\n=== SCRAPING COMPLETE ===")

if __name__ == "__main__":
    run()
