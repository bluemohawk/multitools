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

You can send a POST request to the `/query` endpoint to interact with the agent. The API now supports conversational memory. To maintain a conversation, you should capture the `session_id` from the first response and include it in all subsequent requests for that conversation.

**Request Body:**

```json
{
  "query": "Your question here",
  "session_id": "optional_uuid_string"
}
```
- `query` (string, required): The user's query for the agent.
- `session_id` (string, optional): A UUID to identify the conversation. If omitted on the first request, a new session will be created and its ID returned in the response.

**Example using curl:**

**First request (starting a new conversation):**
```bash
curl -X POST "http://127.0.0.1:8000/query" -H "Content-Type: application/json" -d '{"query": "My name is Jules."}'
```

**Example Response:**
```json
{
  "response": "Hello, Jules! How can I help you today?",
  "session_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```

**Subsequent request (continuing the conversation):**
```bash
curl -X POST "http://127.0.0.1:8000/query" -H "Content-Type: application/json" -d '{"query": "What did I say my name was?", "session_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"}'
```

**Response Body:**

The response will contain the agent's answer and the `session_id` for the current conversation.

```json
{
  "response": "You told me your name is Jules.",
  "session_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```
