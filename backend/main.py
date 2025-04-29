from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.database import engine, init_db
from backend.app.models import crawler
from backend.app.api.crawler import router as crawler_router
from backend.app.api.search import router as search_router
import logging
import sys

# Configure logging to output to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Initialize database
init_db()

app = FastAPI(title="UCI Search Engine")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include crawler routes
app.include_router(crawler_router, prefix="/api/crawler", tags=["crawler"])
app.include_router(search_router, prefix="/api/search", tags=["search"])


@app.get("/")
async def root():
    return {"message": "UCI Search Engine API"}
