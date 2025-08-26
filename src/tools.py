import datetime
import gspread
from alpha_vantage.timeseries import TimeSeries
from ddgs import DDGS
from langchain_core.tools import tool
from src.config import settings

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
