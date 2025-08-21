from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import settings

# Instantiate the language model, passing the API key directly
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=settings.GOOGLE_API_KEY
)
