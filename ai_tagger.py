import re

# =========================
# KEYWORD MODELS
# =========================

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

# =========================
# AI TAGGER
# =========================

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
