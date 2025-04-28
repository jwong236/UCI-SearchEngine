from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import crawler
from app.api.crawler import router as crawler_router

# Create database tables
crawler.Base.metadata.create_all(bind=engine)

app = FastAPI(title="UCI Search Engine Crawler")

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


@app.get("/")
async def root():
    return {"message": "UCI Search Engine Crawler API"}
