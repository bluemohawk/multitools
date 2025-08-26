from langchain_core.prompts import PromptTemplate

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

ticker_prompt = PromptTemplate(
    template="Given the following question, extract the stock ticker symbol. Only return the ticker symbol.\n\nQuestion: {question}\nTicker:",
    input_variables=["question"],
)

name_prompt = PromptTemplate(
    template="Given the following question, extract the person's name. Only return the name.\n\nQuestion: {question}\nName:",
    input_variables=["question"],
)
