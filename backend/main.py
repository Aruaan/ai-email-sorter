import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

app = FastAPI()

# Import and include routers
from routes.auth import router as auth_router
from routes.categories import router as categories_router

app.include_router(auth_router, prefix="/auth")
app.include_router(categories_router, prefix="/categories")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True) 