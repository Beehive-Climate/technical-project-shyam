import os
import sqlparse
import pg8000.native
from dotenv import load_dotenv

load_dotenv()

# Allowed tables (for validation)
ALLOWED_TABLES = ['"CycloneRisk"', '"FloodRisk"', '"HeatRisk"', '"WildfireRisk"']

# Schema to guide SQL generation
SCHEMA = """
Tables available (case-sensitive; ALWAYS wrap table names in double quotes):

"CycloneRisk"(
    id, region, risk_type, risk_id, geometry,
    ssp1_1yr, ssp1_10yr, ssp1_30yr,
    ssp3_1yr, ssp3_10yr, ssp3_30yr,
    ssp5_1yr, ssp5_10yr, ssp5_30yr,
    total_annual_freq, avg_building_exposure
)

"FloodRisk"(
    id, region, risk_type, risk_id, geometry,
    ssp1_1yr, ssp1_10yr, ssp1_30yr,
    ssp3_1yr, ssp3_10yr, ssp3_30yr,
    ssp5_1yr, ssp5_10yr, ssp5_30yr,
    ssp1_30yr_rp200_percent_flooded
)

"HeatRisk"(
    id, region, risk_type, risk_id, geometry,
    ssp1_1yr, ssp3_1yr, ssp5_1yr,
    ssp1_10yr, ssp3_10yr, ssp5_10yr,
    ssp1_30yr, ssp3_30yr, ssp5_30yr,
    ssp5_30yr_ann_days_above_096f
)

"WildfireRisk"(
    id, region, risk_type, risk_id, geometry,
    ssp1_1yr, ssp3_1yr, ssp5_1yr,
    ssp1_10yr, ssp3_10yr, ssp5_10yr,
    ssp1_30yr, ssp3_30yr, ssp5_30yr,
    ssp5_30yr_ann_arid_waves, hist_avg_loss_rate, avg_building_exposure
)

Rules:
- SELECT-only. Never modify data.
- ALWAYS quote table names exactly as shown (e.g. FROM "CycloneRisk").
- For city-specific queries: use provided coordinates inside ST_MakePoint, and
  match polygons with ORDER BY geometry <-> ST_SetSRID(ST_MakePoint(lon, lat), 4326) LIMIT 20.
- If user explicitly mentions SSP1, SSP3, or SSP5: only return columns from that scenario.
- If user does not mention scenario: default to SSP5.
- If user explicitly mentions a time horizon (1, 10, or 30 years): only return that horizon.
- If user does not mention a time horizon: return all three horizons (1yr, 10yr, 30yr) for the chosen scenario.
- Output ONLY the SQL query. No markdown, comments, or explanations.
"""

HAZARD_KEYWORDS = {
    '"CycloneRisk"': ["cyclone", "hurricane", "storm", "typhoon"],
    '"FloodRisk"':   ["flood", "inundation", "water"],
    '"HeatRisk"':    ["heat", "temperature", "heatwave", "hot"],
    '"WildfireRisk"':["wildfire", "fire", "burn"]
}

def validate_sql(sql: str) -> bool:
    # To make sure it's Select and not deleting or updating our data
    try:
        parsed = sqlparse.parse(sql)[0]
    except Exception:
        return False

    # Ensure it's SELECT
    first_token = parsed.token_first(skip_cm=True)
    if not first_token or first_token.normalized.upper() != "SELECT":
        return False

    sql_upper = sql.upper()

    # Require at least one allowed (quoted) table name
    if not any(tbl.upper() in sql_upper for tbl in ALLOWED_TABLES):
        return False

    # Require a LIMIT (case-insensitive)
    if "LIMIT" not in sql_upper:
        return False

    return True


def run_sql_query(sql: str):
    # Run SQL query on Postgres or return dummy if no DB config.
    connection = pg8000.native.Connection(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 5432))
    )
    rows = connection.run(sql)
    connection.close()
    return rows
