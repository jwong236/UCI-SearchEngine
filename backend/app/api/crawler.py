from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
from typing import List
import asyncio
from ..database import get_db
from ..services.crawler_service import CrawlerService
from ..models.crawler import URL, CrawlStatistics
from datetime import datetime, timezone

router = APIRouter()

# Secret key for crawler control (in production, use environment variables)
CRAWLER_SECRET_KEY = "your-secret-key-here"

# Global crawler state
crawler_running = False
active_websockets: List[WebSocket] = []


@router.post("/start")
async def start_crawler(secret_key: str, db: Session = Depends(get_db)):
    """Start the crawler with the provided secret key."""
    global crawler_running

    if secret_key != CRAWLER_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret key")

    if crawler_running:
        raise HTTPException(status_code=400, detail="Crawler is already running")

    crawler_running = True

    # Start crawler in background task
    asyncio.create_task(run_crawler(db))
    return {"status": "Crawler started"}


@router.post("/stop")
async def stop_crawler(secret_key: str):
    """Stop the crawler with the provided secret key."""
    global crawler_running

    if secret_key != CRAWLER_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret key")

    crawler_running = False
    return {"status": "Crawler stopped"}


@router.get("/status")
async def get_crawler_status(db: Session = Depends(get_db)):
    """Get current crawler status and statistics."""
    stats = db.query(CrawlStatistics).order_by(CrawlStatistics.id.desc()).first()

    return {
        "is_running": crawler_running,
        "statistics": {
            "urls_crawled": stats.urls_crawled if stats else 0,
            "urls_failed": stats.urls_failed if stats else 0,
            "unique_domains": stats.unique_domains if stats else 0,
        },
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time crawler logs."""
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        active_websockets.remove(websocket)


async def broadcast_log(message: str):
    """Broadcast log message to all connected WebSocket clients."""
    for websocket in active_websockets:
        try:
            await websocket.send_json(
                {
                    "message": message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except:
            active_websockets.remove(websocket)


async def run_crawler(db: Session):
    """Main crawler loop."""
    crawler = CrawlerService(db)

    # Start with seed URLs
    seed_urls = [
        "https://www.ics.uci.edu",
        "https://www.cs.uci.edu",
        "https://www.informatics.uci.edu",
        "https://www.stat.uci.edu",
    ]

    for url in seed_urls:
        if not crawler_running:
            break

        await broadcast_log(f"Processing seed URL: {url}")
        await crawler.process_url(url)

    # Process discovered URLs
    while crawler_running:
        url_record = db.query(URL).filter(URL.is_completed == False).first()

        if not url_record:
            await broadcast_log("No more URLs to process")
            break

        await broadcast_log(f"Processing URL: {url_record.url}")
        await crawler.process_url(url_record.url)

    await broadcast_log("Crawler stopped")
