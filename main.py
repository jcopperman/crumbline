import uvicorn
from app.main import app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    
    uvicorn.run("app.main:app", host=host, port=port, reload=debug) 