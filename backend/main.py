from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import run_sql_query, validate_sql
from llm import generate_sql, stream_summarize_answer
from geoLocations import get_coords

app = FastAPI()

# Allow frontend (for dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

# Ask Quetion about risk
@app.post("/ask")
def ask_question(req: QueryRequest):
    user_query = req.query

    # Step 1: Generate SQL
    sql = generate_sql(user_query)

    # Step 2: Validate SQL
    if not validate_sql(sql):
        return {"error": "Invalid SQL generated", "sql": sql}

    # Step 3: Run SQL to fetch information from database
    try:
        result = run_sql_query(sql)
    except Exception as error:
        return {"error": str(error), "sql": sql}

    # Step 4: Stream summarization instead of sending data all at once
    def event_stream():
        for chunk in stream_summarize_answer(user_query, result):
            yield chunk

    return StreamingResponse(event_stream(), media_type="text/plain")
