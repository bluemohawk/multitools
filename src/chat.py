import uuid
from typing import Tuple
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langgraph.graph import START, StateGraph

from src.llm import llm
from src.models import Route, State
from src.prompts import router_prompt, synthesis_prompt, ticker_prompt, name_prompt
from src.tools import duckduckgo_search, get_current_time, get_stock_price, query_google_sheet


# --- Graph Components ---

def router(state: State) -> dict:
    """Routes the user question to the appropriate tool or to the chatbot."""
    print("---ROUTING---")
    tools = [duckduckgo_search, get_stock_price, get_current_time, query_google_sheet]
    tool_definitions = [{"name": t.name, "description": t.description} for t in tools]
    tool_definitions.append({"name": "chatbot", "description": "Responds to general questions and conversation."})

    tools_str = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in tool_definitions])

    parser = JsonOutputParser(pydantic_object=Route)
    chain = router_prompt | llm | parser

    question = state['messages'][-1].content
    result = chain.invoke({"tools": tools_str, "question": question})

    return {"next": result['destination']}


# Node Functions
def chatbot_node(state: State) -> dict:
    """Generates a response from the LLM, either as a direct answer or by synthesizing tool output."""
    print("---CHATBOT---")
    if isinstance(state['messages'][-1], ToolMessage):
        original_question = ""
        for msg in reversed(state['messages']):
            if isinstance(msg, HumanMessage):
                original_question = msg.content
                break
        
        tool_output = state['messages'][-1].content
        
        synthesis_chain = synthesis_prompt | llm | StrOutputParser()
        response = synthesis_chain.invoke({
            "question": original_question,
            "tool_output": tool_output
        })
        return {"messages": [AIMessage(content=response)]}
    else:
        return {"messages": [llm.invoke(state["messages"])]}

def search_node(state: State) -> dict:
    """Invokes the DuckDuckGo search tool."""
    print("---SEARCH---")
    question = state['messages'][-1].content
    result = duckduckgo_search.invoke(question)
    return {"messages": [ToolMessage(content=result, name='duckduckgo_search', tool_call_id=str(uuid.uuid4()))]}

def stock_node(state: State) -> dict:
    """Extracts the ticker and invokes the stock price tool."""
    print("---STOCK---")
    question = state['messages'][-1].content
    extraction_chain = ticker_prompt | llm | StrOutputParser()
    ticker = extraction_chain.invoke({"question": question})
    result = get_stock_price.invoke(ticker)
    return {"messages": [ToolMessage(content=result, name='get_stock_price', tool_call_id=str(uuid.uuid4()))]}

def time_node(state: State) -> dict:
    """Invokes the current time tool."""
    print("---TIME---")
    result = get_current_time.invoke(None)
    return {"messages": [ToolMessage(content=result, name='get_current_time', tool_call_id=str(uuid.uuid4()))]}

def google_sheet_node(state: State) -> dict:
    """Extracts the person's name and invokes the Google Sheet tool."""
    print("---GOOGLE_SHEET---")
    question = state['messages'][-1].content
    extraction_chain = name_prompt | llm | StrOutputParser()
    name = extraction_chain.invoke({"question": question})
    result = query_google_sheet.invoke(name)
    return {"messages": [ToolMessage(content=result, name='query_google_sheet', tool_call_id=str(uuid.uuid4()))]}

def where_to_go(state: State) -> str:
    """Determines the next node to visit based on the router's decision."""
    return state['next']


# --- Graph Definition ---

graph_builder = StateGraph(State)
graph_builder.add_node("router", router)
graph_builder.add_node("duckduckgo_search", search_node)
graph_builder.add_node("get_stock_price", stock_node)
graph_builder.add_node("get_current_time", time_node)
graph_builder.add_node("query_google_sheet", google_sheet_node)
graph_builder.add_node("chatbot", chatbot_node)

graph_builder.add_edge(START, "router")
graph_builder.add_conditional_edges("router", where_to_go, {
    "duckduckgo_search": "duckduckgo_search",
    "get_stock_price": "get_stock_price",
    "get_current_time": "get_current_time",
    "query_google_sheet": "query_google_sheet",
    "chatbot": "chatbot",
})
graph_builder.add_edge("duckduckgo_search", "chatbot")
graph_builder.add_edge("get_stock_price", "chatbot")
graph_builder.add_edge("get_current_time", "chatbot")
graph_builder.add_edge("query_google_sheet", "chatbot")

graph = graph_builder.compile()


# --- Agent Interface ---

def get_agent_response(user_input: str, current_state: dict) -> Tuple[str, dict]:

    """
    Runs the agent for a single query and returns the response and the updated state.
    """
    # Append the new user message to the existing messages in the state

    if 'messages' not in current_state:
        current_state['messages'] = []

    current_state['messages'].append(HumanMessage(content=user_input))

    # Invoke the graph with the updated state
    updated_state = graph.invoke(current_state)

    # Extract the latest response from the messages
    response_text = updated_state['messages'][-1].content

    return response_text, updated_state
