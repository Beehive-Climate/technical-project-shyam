from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import run_sql_query, validate_sql
from llm import generate_sql, stream_summarize_answer, load_doc_from_db, detect_hazards,fallback_stream_answer

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

# Ask Question about risk
@app.post("/ask")
def ask_question(req: QueryRequest):

    user_query = req.query

    #Step 1: Detect cities and their coordinated

    # Step 2: Detect hazards
    hazard_tables = detect_hazards(user_query)

    # Step 3: Generate SQL
    sqlQuery = generate_sql(
        user_query=user_query,
        hazard_tables=hazard_tables,
    )

    # Step 4: Validate SQL
    if not validate_sql(sqlQuery):
        # fallback directly to LLM narrative answer
        return StreamingResponse(fallback_stream_answer(user_query), media_type="text/plain")
    
    # Step 5: Run SQL
    try:
        result = run_sql_query(sqlQuery)
    except Exception as error:
        # fallback to LLM if DB error
        return StreamingResponse(fallback_stream_answer(user_query), media_type="text/plain")

    # Step 6: Fallback if empty result
    if not result:
        return StreamingResponse(fallback_stream_answer(user_query), media_type="text/plain")

    # Step 7: Stream summarization with data
    # Add DB context + SQL so summarizer knows column meanings
    db_context = load_doc_from_db('Beehive_DB_Context_Summary.docx')

    def event_stream():
        for chunk in stream_summarize_answer(
            user_query=user_query,
            db_result=result,
            sql_query=sqlQuery,
            db_context=db_context
        ):
            yield chunk

    return StreamingResponse(event_stream(), media_type="text/plain")
