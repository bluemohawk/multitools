from typing import Annotated, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from uuid import UUID

# --- API Models ---

from typing import Optional
from uuid import UUID, uuid4
from pydantic import Field

class QueryRequest(BaseModel):
    """Request model for the /query endpoint."""
    query: str
    session_id: Optional[UUID] = None

class QueryResponse(BaseModel):
    """Response model for the /query endpoint."""
    response: str
    session_id: UUID

# --- Agent Models ---

class Route(TypedDict):
    """Route a user question to the appropriate tool."""
    destination: str

class State(TypedDict):
    """The state of the agent graph."""
    messages: Annotated[list[BaseMessage], add_messages]
    next: str
