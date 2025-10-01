import os
from dotenv import load_dotenv
from openai import OpenAI
from database import HAZARD_KEYWORDS,SCHEMA,HAZARD_KEYWORDS
import re
from documentReader import load_doc_from_db
from typing import List, Optional

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Extract the SQL query from the text from the llm generated text
def extract_sql_from_text(text: str) -> Optional[str]:
    """
    Extract SQL if it contains a valid SELECT statement,
    even if wrapped in parentheses (UNION ALL cases).
    """
    text = text.strip()

    # Look for first occurrence of SELECT
    match = re.search(r"\bSELECT\b", text, re.IGNORECASE)
    if match:
        return text

    return None

# Call the llm model to generate the answer
def call_llm(messages: List[dict], model: str = "gpt-4o-mini", temperature: float = 0.0) -> str:
  
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content


def build_sql_prompt(
    db_context_compact: str,
    user_query: str,
    hazards: List[str],
    region: Optional[str],
) -> List[dict]:
    # Hazard → table mapping
    table_map = {
        "cyclone": "CycloneRisk",
        "flood": "FloodRisk",
        "heat": "HeatRisk",
        "wildfire": "WildfireRisk",
        "CycloneRisk": "CycloneRisk",
        "FloodRisk": "FloodRisk",
        "HeatRisk": "HeatRisk",
        "WildfireRisk": "WildfireRisk",
        "physical": "ALL",
        "risk": "ALL",
        "climate": "ALL",
    }

    tbls = [table_map.get(h, h) for h in hazards]

    # If no hazards detected OR "ALL" is present → use all tables
    if not tbls or "ALL" in tbls:
        tbls = ["CycloneRisk", "FloodRisk", "HeatRisk", "WildfireRisk"]

    system = f"""
    You are a SQL generator for a Postgres climate risk database.

    Use only existing tables/columns.
    Tables: "CycloneRisk", "FloodRisk", "HeatRisk", "WildfireRisk".

    Location rules:
    - If a specific city is mentioned in the user query:
    * Determine its approximate longitude/latitude yourself.
    * Always use those coordinates with:
        ORDER BY geometry <-> ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        LIMIT 1
    * Do not use AVG() here — just return the nearest cell value.

    - If a country is mentioned (but not a specific city):
    * Infer its continent-scale region (one of: north_america, south_america, europe, asia, oceania, africa).
    * Use WHERE region ILIKE '%<region>%' to filter.
    * Apply AVG() to produce a single row per hazard.

    - If multiple cities or countries are mentioned:
    * Generate one SELECT per location × hazard.
    * Wrap each SELECT in parentheses if it contains ORDER BY or LIMIT.
    * Add a literal column with the location name using AS city.
    * Combine them with UNION ALL so each row corresponds to one location × hazard.


    Hazard rules:
    - cyclone → "CycloneRisk"
    - flood → "FloodRisk"
    - heat → "HeatRisk"
    - wildfire → "WildfireRisk"
    - If the user asks about "physical risk", "climate risk", or does not specify hazards → query all four tables.

    Column rules:
    - Risk/severity columns follow the pattern: ssp{{X}}_{{Y}}yr
      * Valid X values: 1, 3, 5
      * Valid Y values: 1, 10, 30
      * Example: ssp1_1yr, ssp3_10yr, ssp5_30yr
    - Counts/frequency:
      * "CycloneRisk" → total_annual_freq or cat{{Z}}_annual_freq
      * "FloodRisk" → ssp{{X}}_{{Y}}yr_rp050_percent_flooded, ssp{{X}}_{{Y}}yr_rp200_percent_flooded
      * "HeatRisk" → ssp{{X}}_{{Y}}yr_ann_days_above_096f, ssp{{X}}_{{Y}}yr_ann_heat_waves_4d5percent
      * "WildfireRisk" → ssp{{X}}_{{Y}}yr_fires_30yr
    - Prefer ssp5_10yr unless the user specifies another valid SSP or horizon.
    - If the user specifies an invalid horizon (e.g., 5 years), map it to the nearest valid horizon (1yr, 10yr, or 30yr).

    Output rules:
    - Return ONLY the SQL query string.
    - Do not include markdown, code fences, or explanations.
    - Always use quoted CamelCase table names.
    - Never use unquoted or lowercase table names.
    - Do not use SELECT * — only select needed columns.
    - Always alias columns with AS <descriptive_name>.
    - Always include a literal column for hazard type using AS hazard.
    - Final result must have: risk_score, city (or region), hazard.
    - For city-based queries:
      * If user asks for a specific city, do NOT include region filters.
      * By default, select the single nearest mesh cell using:
        ORDER BY geometry <-> ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        LIMIT 1
      * If averaging is required (e.g., “on average”), wrap in a subquery that selects the N nearest cells, then apply AVG() in the outer query.
      * Never combine AVG() directly with ORDER BY/LIMIT in the same SELECT.
    - For region-based queries:
      * Use WHERE region ILIKE '%<region>%'.
      * Use AVG() so result is a single row per hazard.
    """

    user = {
        "user_query": user_query,
        "region": region,
        "hazards": tbls,
        "db_context": db_context_compact,
    }

    return [
        {"role": "system", "content": system.strip()},
        {"role": "user", "content": f"{user}"}
    ]


def generate_sql(user_query: str, hazard_tables, region=None) -> str:
    """Master SQL generator with LLM + fallback."""
    database_context = load_doc_from_db('Beehive_DB_Context_Summary.docx')

    # Build messages
    messages = build_sql_prompt(
        db_context_compact=database_context,
        user_query=user_query,
        hazards=hazard_tables,
        region=region,
    )

    try:
        llm_text = call_llm(messages)
        sql = extract_sql_from_text(llm_text)
        if sql:
            return sql
    except Exception as e:
        print(f"[WARN] LLM SQL generation failed: {e}")

    # Fallback: safe deterministic minimal query
    return None

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

def stream_summarize_answer(user_query: str, db_result, sql_query: str, db_context: str):
    """
    Stream a markdown-formatted summary of DB result with context:
    - Only summarize hazards that were queried
    - Distinguish between risk scores vs counts/frequencies vs percentages
    - Include SQL + DB schema context for accurate explanations
    """

    prompt = f"""
    User asked: {user_query}

    SQL query executed:
    {sql_query}

    Database returned (raw values):
    {db_result}

    Database schema context (columns and their meaning):
    {db_context}

    Write a clear, user-friendly answer in MARKDOWN.

    Rules:
    - Only include hazards that are present in the SQL query or DB result.
    - Do not output hazards that were not queried.
    - If multiple hazards are present (e.g., UNION ALL), report each one separately.
    - If only one hazard is present, output just that hazard.

    Interpretation rules:
    - If the column is a risk score (ssp{{X}}_{{Y}}yr, values 1–7), map it to categories:
    * 1–3 = Low
    * 4–5 = Moderate
    * 6–7 = High
    - If the column is a frequency (e.g., total_annual_freq, fires_30yr),
    explain it as "expected number of events" over the relevant period.
    - If the column is a flood extent percent (rp050/rp200),
    explain it as "proportion of area flooded".
    - If multiple horizons are present (1yr, 10yr, 30yr), describe the trend over time.

    Location rules:
    - Always reflect the location from the user query in the heading (city/country).
    - If DB only provides region-level data, clearly state it as:
    "<UserLocation> (data aggregated from <Region>)".
    - If DB granularity is limited, you may add general knowledge about which subregions, states, or cities are most exposed to the hazard.
    - Always clarify which parts come from the database result vs general knowledge.

    Output format:
    ### <User location, with aggregation note if needed>
    - **<Hazard>:** <interpreted values with context + optional regional detail>

    ### Summary
    Provide a 5–6 sentence summary:
    - Anchor on DB result first.
    - If DB result is too broad, enrich the answer with well-known geographic patterns (e.g., “In India, eastern states like Bihar and Assam are particularly flood-prone”).
    - Clearly separate database-based findings from general knowledge insights.
    """

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

def fallback_stream_answer(user_query):
    answer = call_llm([
        {"role": "system", "content": "Answer the user based on general climate risk knowledge."},
        {"role": "user", "content": user_query}
    ])
    yield answer