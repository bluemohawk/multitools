# Multi-Tool Agent Web Application

This project is a web application that exposes a multi-tool agent via a REST API. It can be queried by other applications, such as an iOS app.

## Setup

### 1. Environment Variables

This application requires several API keys to be configured as environment variables.

Create a file named `.env` in the root of the project and add the following, replacing the placeholder values with your actual API keys:

```
GOOGLE_API_KEY=your_google_api_key
ALPHAVANTAGE_API_KEY=your_alphavantage_api_key
# You also need to set up Google Application Credentials for the Google Sheets API.
# See the gspread documentation for more details: https://docs.gspread.org/en/latest/oauth2.html
# After setting up, set the path to your credentials file here:
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
```

### 2. Installation

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 3. Running the Application

To start the web server, run the following command:

```bash
uvicorn src.api:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

## API

### POST /query

You can send a POST request to the `/query` endpoint to interact with the agent.

**Request Body:**

```json
{
  "query": "Your question here"
}
```

**Example using curl:**

```bash
curl -X POST "http://127.0.0.1:8000/query" -H "Content-Type: application/json" -d '{"query": "What is the stock price of GOOG?"}'
```

**Response Body:**

```json
{
  "response": "The agent's response will be here."
}
```
