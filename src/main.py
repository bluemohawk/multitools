import uvicorn
from src.api import app

if __name__ == "__main__":
    # Note: This is for local development only.
    # In production, you would run the app with a Gunicorn/Uvicorn process manager.
    uvicorn.run(app, host="0.0.0.0", port=8000)
