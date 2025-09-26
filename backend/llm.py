import os
from dotenv import load_dotenv
from openai import OpenAI
from geoLocations import extract_cities,get_coords,detect_region
from database import HAZARD_KEYWORDS,SCHEMA,HAZARD_KEYWORDS

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def detect_hazards(user_query: str) -> list:
    
    # Detect which hazard types are relevant to the user's query.
    
    # - Matches keywords in the query against a dictionary of known hazards.
    # - If no hazards are mentioned, defaults to returning all hazards.
    
    normalized_query = user_query.lower()

    matched_hazards = []
    for hazard, keywords in HAZARD_KEYWORDS.items():
        if any(keyword in normalized_query for keyword in keywords):
            matched_hazards.append(hazard)

    # Default: if nothing matched, assume all hazards
    return matched_hazards if matched_hazards else list(HAZARD_KEYWORDS.keys())

def build_city_hazard_block(city: str, lon: float, lat: float, table: str) -> str:
    
    # Build one subquery for a given city & hazard table.
    # Injects the city name as a constant so results can be tied back to the input.
    
    hazard_name = table.strip('"')
    return f"""
    SELECT
    '{city}' AS city,
    '{hazard_name}' AS hazard,
    (SELECT region
        FROM {table}
        ORDER BY geometry <-> ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)
        LIMIT 1) AS region,
    AVG(ssp5_1yr)  AS risk_1yr,
    AVG(ssp5_10yr) AS risk_10yr,
    AVG(ssp5_30yr) AS risk_30yr
    FROM (
    SELECT ssp5_1yr, ssp5_10yr, ssp5_30yr
    FROM {table}
    ORDER BY geometry <-> ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)
    LIMIT 20
    ) nearest
    """.strip()

def generate_sql(user_query: str) -> str:
    # --- Step 1: Extract cities and coordinates ---
    detected_cities = extract_cities(user_query)
    city_coords = [(city, get_coords(city)) for city in detected_cities]
    valid_city_coords = [(city, coords) for city, coords in city_coords if coords]

    # --- Step 2: Detect hazards ---
    hazard_tables = detect_hazards(user_query)

    # --- Step 3A: City-specific queries ---
    if valid_city_coords:
        sql_blocks = [
            build_city_hazard_block(city, lon, lat, hazard)
            for city, (lon, lat) in valid_city_coords
            for hazard in hazard_tables
        ]
        return "\nUNION ALL\n\n".join(sql_blocks)

    # --- Step 3B: Region-level queries (no city, but "US"/continent mentioned) ---
    region = detect_region(user_query)   # <-- new helper function
    if region:
        sql_blocks = [
            f"""
            SELECT
              '{region}' AS region,
              '{hazard.strip('"')}' AS hazard,
              AVG(ssp5_1yr)  AS risk_1yr,
              AVG(ssp5_10yr) AS risk_10yr,
              AVG(ssp5_30yr) AS risk_30yr
            FROM {hazard}
            WHERE region ILIKE '%{region}%
            LIMIT 20'
            """
            for hazard in hazard_tables
        ]
        return "\nUNION ALL\n\n".join(sql_blocks)

    # --- Step 4: Fallback to LLM for weird/global queries ---
    return generate_fallback_sql(user_query)

def generate_fallback_sql(user_query: str) -> str:
    
    # Ask the LLM to generate a safe SQL query when cities/coordinates
    # are not available in the user query.
    
    prompt = f"""
    You are a Postgres SQL expert. Generate ONE safe SELECT query using this schema:

    {SCHEMA}

    User request:
    {user_query}

    Rules:
    - Default to SSP5 if no scenario is mentioned.
    - If horizon is not mentioned, return 1yr, 10yr, and 30yr.
    - Output ONLY the SQL query (no markdown, no explanations).
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    sql = response.choices[0].message.content.strip()

    # Clean up accidental code fences from the model
    if sql.startswith("```"):
        sql = sql.strip("`").replace("sql\n", "").replace("sql", "").strip()

    return sql

def stream_summarize_answer(user_query: str, db_result):
    # Stream markdown-formatted summary of DB result

    prompt = f"""
    User asked: {user_query}
    Database returned: {db_result}

    Write a clear, user-friendly answer in MARKDOWN with this structure:

    ### <City>
    - **Cyclone Risk:** <numeric score(s) mapped to Low/Moderate/High>
    - **Flood Risk:** <numeric score(s) mapped to Low/Moderate/High>
    - **Heat Risk:** <numeric score(s) mapped to Low/Moderate/High>
    - **Wildfire Risk:** <numeric score(s) mapped to Low/Moderate/High>

    ### Summary
    Provide a short paragraph (3–5 sentences) comparing the risks across hazards
    and highlighting the biggest concerns for the user.

    Rules:
    - Always map raw scores (1–7) into categories:
    - 1–3 = Low
    - 4–5 = Moderate
    - 6–7 = High
    - If multiple years (1yr, 10yr, 30yr) are present, mention the trend (e.g. "risk increases from Low to High").
    - Only output markdown. No explanations or code fences.
    """


    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

