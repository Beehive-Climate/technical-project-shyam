# Beehive Climate Risk Chat Application

## Problem Statement

The goal of this project is to build a prototype chat application that helps people understand **climate-related physical risks**.  
Users should be able to ask natural questions like:

- “What are the highest risk locations for flooding in the US?”  
- “How many cyclones are expected in Miami in the next 10 years?”  
- “What risks are there for offices in Boston, Charlotte, and London?”  

The system combines **structured data** from a Postgres database with **natural explanations** from an LLM, so responses are both accurate and easy to understand.  

---

## Approach

The backend is organized into modular components:  

- **`database.py`** → connects to Postgres and safely executes SQL queries.  
- **`geoLocations.py`** → minimal helper for region keyword mapping (LLM now handles city coordinates).  
- **`llm.py`** → generates SQL queries and summarizes results using the LLM.  
- **`main.py`** → FastAPI backend that ties everything together.  
- **`Beehive_DB_Context_Summary.docx`** → compact schema context for grounding the LLM.  
- **Frontend (React)** → provides the chat-like user interface.  

Design principles:  
- The **database** provides deterministic, factual risk scores.  
- The **LLM** translates results into structured, human-friendly summaries.  
- Clear separation of responsibilities → easier to maintain and extend.  

---

## How It Works

1. The user asks a question in plain English through the frontend.  
2. The backend interprets whether it’s a **city query** or **region query**.  
3. **For cities** → the LLM determines approximate coordinates and queries the nearest mesh cell.  
4. **For regions** → the query aggregates values across the region using `AVG()`.  
5. `database.py` executes the SQL safely against Postgres.  
6. `llm.py` reformats raw results into a clear markdown answer.  
7. `main.py` streams the response back to the chat UI.  

---

## How to run locally

# Backend
1. Make sure you have python and pip installed.
2. Run `pip install -r requirement.txt`
3. Make sure to create `.env` by taking sample from .env.sample.
4. To run the code - `uvicorn main:app --port 8000` (You can run at any port)

# Frontend
1. Install node and npm.
2. Run `npm install` to install necessary packages
3. Make sure to create `.env` by taking sample from .env.sample.
4. Run `npm run dev` to run locally


## Location Handling

- **Cities** → resolved directly by the LLM into approximate coordinates, then matched to the nearest mesh cell using:  
  ```sql
  ORDER BY geometry <-> ST_SetSRID(ST_MakePoint(lon, lat), 4326)
  LIMIT 1;
  ```
- **Regions** → mapped to one of: `north_america`, `south_america`, `europe`, `asia`, `oceania`, `africa`. Aggregated with `AVG()`.  
- **Multiple locations** → handled with `UNION ALL` (or future optimizations using CTEs/VALUES batching).  

This ensures results are flexible: precise for cities, generalized for regions.  

---

## Project Structure

```
.
├── database.py                 # Database connection + safe query execution
├── geoLocations.py             # Region keyword mapping (LLM handles city coords)
├── llm.py                      # LLM for SQL generation + summarization
├── main.py                     # FastAPI backend
├── Beehive_DB_Context_Summary.docx  # Compact DB schema context for prompts
├── frontend/                   # React chat frontend
```

---

## Key Features

- **Safe SQL generation**  
  - Only allows `SELECT` on approved hazard tables.  
  - Blocks `SELECT *`, `DROP`, `DELETE`, etc.  
  - Always outputs: `risk_score`, `city` (or region), and `hazard`.  

- **Schema-aware prompts**  
  - Knows valid hazard tables: `"CycloneRisk"`, `"FloodRisk"`, `"HeatRisk"`, `"WildfireRisk"`.  
  - Uses correct column families for each hazard (`sspX_Yyr`, flood % columns, heatwave days, wildfire frequencies).  

- **Summarization**  
  - Converts numeric results into:  
    - **1–3 = Low**, **4–5 = Moderate**, **6–7 = High**.  
    - Frequencies explained as expected events.  
    - Flood % explained as proportion of area flooded.  
  - Anchors responses to the **user’s original query location**, even when results are aggregated.  
  - Supplements with **general knowledge** when DB data is too broad.  

- **Performance-aware design**  
  - Prototype uses UNION queries.  
  - Future optimization: batch queries using `VALUES + CROSS JOIN LATERAL` or pre-aggregated materialized views.  

---

## To run the test case

- python -m pytest tests -v

## Outcome

The prototype chat app now supports:  
- Natural questions in plain English.  
- Automatic SQL generation grounded in the schema.  
- Accurate numeric risk retrieval from Postgres.  
- Structured, human-friendly markdown answers.  

It balances **deterministic data retrieval** with **flexible natural language output**, laying the foundation for a production-ready **climate risk assistant**.  

