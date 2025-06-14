# test_basic.py
print("Basic test running...")
try:
    import fastapi
    print(f"FastAPI version: {fastapi.__version__}")
    import uvicorn
    print(f"Uvicorn version: {uvicorn.__version__}")
    import sqlalchemy
    print(f"SQLAlchemy version: {sqlalchemy.__version__}")
    import feedparser
    print(f"Feedparser version: {feedparser.__version__}")
    print("All required modules imported successfully")
except Exception as e:
    print(f"Error importing modules: {e}")
