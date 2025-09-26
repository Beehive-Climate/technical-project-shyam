# Beehive Climate Risk Chat Application

## Problem Statement

The goal was to build a prototype chat app that helps people understand climate-related physical risks.  
Users should be able to ask natural questions like:

- “What are the highest risk locations for flooding in the US?”  
- “How many cyclones are expected in Miami in the next 10 years?”  
- “What risks are there for offices in Boston, Charlotte, and London?”  

The system needed to combine structured data from a Postgres database with natural explanations from an LLM, so responses are both accurate and easy to understand.  

---

## Approach

I broke the system into clear, focused components so it’s easy to extend later:  

- **`database.py`** → connects to Postgres and runs SQL queries.  
- **`geoLocations.py`** → extracts places from user queries and resolves them to coordinates.  
- **`llm.py`** → interacts with the LLM to generate queries and summarize results.  
- **`main.py`** → the FastAPI backend that ties everything together.  

The design separates responsibilities:  
- The database provides factual numeric risk scores.  
- The LLM makes the answers human-friendly, turning raw results into structured summaries.  

---

## How It Works

1. The user asks a question through the chat UI.  
2. `geoLocations.py` checks for cities or regions in the query and fetches coordinates.  
3. `database.py` runs the appropriate query against Postgres.  
4. `llm.py` reformats the raw data into a markdown summary.  
5. `main.py` streams the result back to the frontend, where the user sees a chat-like answer.  

---

## Handling Location Complexity

Cities are not single points — they span large areas and can intersect multiple polygons in the database.  

For the prototype, I used a **city center coordinate** (e.g. the centroid of Miami) and matched it against the nearest regional polygon. This was a pragmatic way to get one set of scores per city.  

However, in a production system, a more robust method would be:  
- Sampling multiple coordinates within the city bounds (grid or bounding box).  

This ensures risk estimates reflect the spatial diversity within large metropolitan areas.  

---

## Project Structure

```
.
├── database.py      # Database queries and connection
├── geoLocations.py  # Location utilities (NER + geocoding)
├── llm.py           # LLM integration
├── main.py          # FastAPI entry point
├── frontend/        # React frontend for chat interface
```

---

## Outcome

The result is a working prototype chat app where:  
- Users can ask questions in plain English.  
- The backend converts those into SQL queries.  
- Risk data is fetched from the database.  
- The LLM explains the results in structured, readable markdown.  

It’s a balance of **deterministic data retrieval** and **flexible natural language output**, with room to evolve into a production-ready climate risk assistant.  
