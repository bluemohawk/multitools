from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from agent import run_agent
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Receives a query, processes it through the agent, and returns the response.
    """
    response_text = run_agent(request.query)
    return QueryResponse(response=response_text)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
