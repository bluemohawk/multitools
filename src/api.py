from uuid import uuid4
from fastapi import FastAPI
from src.models import QueryRequest, QueryResponse, State
from src.chat import get_agent_response

app = FastAPI(
    title="Multi-Tool Agent API",
    description="An API for a multi-tool agent that can answer questions using various tools.",
    version="1.0.0",
)

# In-memory storage for conversation states
conversation_states = {}

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """
    Receives a query, processes it through the agent, and returns the response.
    Maintains conversation state using a session ID.
    """
    session_id = request.session_id or uuid4()

    # Retrieve the conversation state or create a new one
    current_state = conversation_states.get(session_id)
    if current_state is None:
        current_state = State(messages=[], next="")

    # Get the agent's response and the updated state
    response_text, updated_state = get_agent_response(request.query, current_state)

    # Store the updated state
    conversation_states[session_id] = updated_state

    return QueryResponse(response=response_text, session_id=session_id)
