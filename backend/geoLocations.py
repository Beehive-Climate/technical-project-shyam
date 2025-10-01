from typing import Optional

REGION_KEYWORDS = {
    "north_america": [
        "us", "usa", "america", "united states", "north america",
        "canada", "mexico"
    ],
    "europe": ["europe", "uk", "france", "germany", "italy", "spain"],
    "asia": ["asia", "india", "china", "japan", "korea"],
    "south_america": ["brazil", "argentina", "south america"],
    "oceania": ["australia", "oceania", "new zealand"],
    "africa": ["africa", "egypt", "nigeria", "kenya", "south africa"],
}

def detect_region(query: str) -> Optional[str]:
    lowercaseQuery = query.lower()
    for region, keywords in REGION_KEYWORDS.items():
        if any(keyword in lowercaseQuery for keyword in keywords):
            return region
    return None