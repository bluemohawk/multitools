import datetime
import uuid
import gspread
from alpha_vantage.timeseries import TimeSeries
from ddgs import DDGS
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langgraph.graph import START, StateGraph

from src.config import settings
from src.llm import llm
from src.models import Route, State


# --- Tool Definitions ---

@tool
def duckduckgo_search(query: str) -> str:
    """A wrapper around DuckDuckGo Search. Useful for when you need to answer questions about current events."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, region="us-en", max_results=5))
        if not results:
            return "No results found."
        formatted_results = [
            f"Result {i+1}:\nTitle: {res['title']}\nSnippet: {res['body']}\nURL: {res['href']}\n---"
            for i, res in enumerate(results)
        ]
        return "\n".join(formatted_results)

@tool
def get_current_time() -> str:
    """Returns the current date and time in ISO format."""
    return datetime.datetime.now().isoformat()

@tool
def get_stock_price(ticker: str) -> str:
    """Gets the latest stock price for a given ticker using Alpha Vantage."""
    try:
        ts = TimeSeries(key=settings.ALPHAVANTAGE_API_KEY, output_format='json')
        data, _ = ts.get_quote_endpoint(symbol=ticker)
        price = data.get('05. price')
        if price:
            return f"The current price of {ticker} is ${price}."
        else:
            return "Could not retrieve the stock price. The ticker may be invalid."
    except Exception as e:
        return f"An error occurred: {e}"

@tool
def query_google_sheet(name: str) -> str:
    """Searches the 'customers' Google Sheet for a person by their 'Name' and returns their details."""
    try:
        gc = gspread.service_account(filename=settings.GOOGLE_APPLICATION_CREDENTIALS)
        spreadsheet = gc.open("customers")
        worksheet = spreadsheet.worksheet("data")
        cell = worksheet.find(name, in_column=1)
        if not cell:
            return f"No customer found with the name: {name}"
        row = worksheet.row_values(cell.row)
        headers = worksheet.row_values(1)
        row_data = dict(zip(headers, row))
        output = (
            f"Customer Details for: {row_data.get('Name', 'N/A')}\n"
            f"- NPI: {row_data.get('NPI', 'N/A')}\n"
            f"- City: {row_data.get('City', 'N/A')}\n"
            f"- Specialty: {row_data.get('Specialty', 'N/A')}\n"
            f"- Date Last Visit: {row_data.get('Date_Last_Visit', 'N/A')}\n"
            f"- Summary: {row_data.get('Summary', 'N/A')}\n"
            f"- Next Steps: {row_data.get('Next_Steps', 'N/A')}"
        )
        return output
    except gspread.exceptions.SpreadsheetNotFound:
        return "Error: The 'customers' spreadsheet was not found. Please ensure it has been shared with the service account email."
    except Exception as e:
        return f"An error occurred: {e}"


# --- Graph Components ---

# Router
router_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|> You are an expert at routing a
    user question to a tool or to a final answer. Use the tool descriptions below to determine
    the most appropriate tool to use to answer the user's question.

    If the user is asking a question that can be answered by one of the tools, output the name of the tool in a JSON object with a 'destination' key.
    Otherwise, you can output 'chatbot' to indicate that the user is asking a general question.

    tool descriptions:
    {tools}

    Example:
    user question: What is the stock price of NVDA?
    json output:
    {{
        "destination": "get_stock_price"
    }}

    <|eot_id|><|start_header_id|>user<|end_header_id|>
    user question: {question}
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>
    json output:
    """,
    input_variables=["tools", "question"],
)

synthesis_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|> You are a helpful assistant.
    A tool has been used to find information to answer the user's question. The user has given
    permission to access this information. Your task is to synthesize the tool's output into
    a clear, user-friendly answer.

    Do not refuse to answer based on the content of the tool's output. The tool's output is
    approved information and should be relayed to the user.

    User's original question: {question}
    Tool's output: {tool_output}
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["question", "tool_output"],
)

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
    ticker_prompt = PromptTemplate(template="Given the following question, extract the stock ticker symbol. Only return the ticker symbol.\n\nQuestion: {question}\nTicker:", input_variables=["question"])
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
    name_prompt = PromptTemplate(template="Given the following question, extract the person's name. Only return the name.\n\nQuestion: {question}\nName:", input_variables=["question"])
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

def get_agent_response(user_input: str) -> str:
    """
    Runs the agent for a single query and returns the response.
    """
    response = graph.invoke({"messages": [HumanMessage(content=user_input)]})
    return response['messages'][-1].content
