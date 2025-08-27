from uuid import uuid4
from fastapi import FastAPI
from src.models import QueryRequest, QueryResponse, State
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

    Maintains conversation state using a session ID, which is treated as the thread_id by LangGraph.
    """
    # If a session_id is not provided, create a new one.
    # This will be used as the thread_id for the conversation.
    session_id = request.session_id or uuid4()

    # Get the agent's response. The checkpointer handles state management.
    response_text = get_agent_response(request.query, str(session_id))


    return QueryResponse(response=response_text, session_id=session_id)
