from typing import Optional
from geopy.geocoders import Nominatim
import spacy
import re

nlp = spacy.load("en_core_web_sm")

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

def get_coords(city_name: str):
    geolocator = Nominatim(user_agent="beehive_app")
    location = geolocator.geocode(city_name)
    if location:
        return (location.longitude, location.latitude)
    return None

def extract_cities(user_query: str):
    doc = nlp(user_query)
    cities = []

    # Flatten + lowercase all region keywords
    flat_keywords = {kw.lower() for kws in REGION_KEYWORDS.values() for kw in kws}

    for ent in doc.ents:
        if ent.label_ in {"GPE", "LOC", "NORP", "FAC"}:
            text = ent.text.strip()

            # Skip region keywords
            if any(text.lower() == kw or kw in text.lower() for kw in flat_keywords):
                continue

            # Clean modifiers like "north side of Austin" → "Austin"
            m = re.search(r'\b([A-Z][a-z]+)\b$', text)
            if m:
                clean_name = m.group(1)
            else:
                clean_name = text

            cities.append(clean_name)

    return list(dict.fromkeys(cities))

def detect_region(query: str) -> Optional[str]:
    lowercaseQuery = query.lower()
    for region, keywords in REGION_KEYWORDS.items():
        if any(keyword in lowercaseQuery for keyword in keywords):
            return region
    return None