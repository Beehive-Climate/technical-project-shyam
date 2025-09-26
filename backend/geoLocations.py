from typing import Optional
from geopy.geocoders import Nominatim
import spacy

nlp = spacy.load("en_core_web_sm")

REGION_KEYWORDS = {
    "north_america": ["us", "usa", "america", "north america", "canada", "mexico"],
    "europe": ["europe", "uk", "france", "germany", "italy", "spain"],
    "asia": ["asia", "india", "china", "japan", "korea"],
    "south_america": ["brazil", "argentina", "south america"],
    "oceania": ["australia", "oceania", "new zealand"],
    "mideast": ["middle east", "mideast", "uae", "saudi", "israel"],
}

def get_coords(city_name: str):
    geolocator = Nominatim(user_agent="beehive_app")
    location = geolocator.geocode(city_name)
    if location:
        return (location.longitude, location.latitude)
    return None

def extract_cities(user_query: str):
    # Run NLP pipeline
    doc = nlp(user_query)

    cities = []
    for ent in doc.ents:
        if ent.label_ in {"GPE", "LOC"}:
            text = ent.text.strip()
            # Drop if it's in region keywords
            if not any(text.lower() in kws for kws in REGION_KEYWORDS.values()):
                cities.append(text)

    # Deduplicate while preserving order
    return list(dict.fromkeys(cities))

def detect_region(query: str) -> Optional[str]:
    lowercaseQuery = query.lower()
    for region, keywords in REGION_KEYWORDS.items():
        if any(keyword in lowercaseQuery for keyword in keywords):
            return region
    return None