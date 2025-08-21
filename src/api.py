from fastapi import FastAPI
from src.models import QueryRequest, QueryResponse
from src.chat import get_agent_response

app = FastAPI(
    title="Multi-Tool Agent API",
    description="An API for a multi-tool agent that can answer questions using various tools.",
    version="1.0.0",
)

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """
    Receives a query, processes it through the agent, and returns the response.
    """
    response_text = get_agent_response(request.query)
    return QueryResponse(response=response_text)
