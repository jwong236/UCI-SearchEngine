from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    Query,
    Header,
    UploadFile,
    File,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
from ..database.connection import (
    get_db,
    get_session_factory,
    get_db_path,
    init_db,
    get_engine,
    close_connections,
    setup_connections,
    generate_new_db_name,
    handle_uploaded_db,
)
from .crawler import CrawlerService
from .search import SearchService
from ..database.models import (
    Document,
    CrawlStatistics,
    Term,
    InvertedIndex,
    CrawlerState,
)
from datetime import datetime, timezone
import os
import shutil
from .websocket_utils import active_websockets, broadcast_log
from ..config.globals import (
    logger,
    get_current_db,
    set_current_db,
    get_available_databases,
    is_crawler_running,
    set_crawler_running,
    get_crawler_task,
    set_crawler_task,
    get_current_crawler,
    set_current_crawler,
    get_seed_urls,
    set_seed_urls,
)
from ..config.settings import settings

router = APIRouter()


async def verify_secret_key(
    x_secret_key: Optional[str] = Header(None, alias="X-Secret-Key")
):
    if not x_secret_key or x_secret_key != "jacob-secret-key":
        raise HTTPException(status_code=401, detail="Invalid secret key")
    return x_secret_key


@router.get("/databases")
async def get_databases():
    """Get list of available databases"""
    return {"current": get_current_db(), "available": get_available_databases()}


@router.post("/databases/switch")
async def switch_database(db_name: str, secret_key: str):
    """Switch to a different database"""
    if secret_key != settings.SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid secret key")

    if db_name not in get_available_databases():
        raise HTTPException(status_code=404, detail="Database not found")

    set_current_db(db_name)
    setup_connections(db_name)
    return {"message": f"Switched to database: {db_name}"}


@router.delete("/databases/{db_name}")
async def delete_database(db_name: str, secret_key: str):
    """Delete a database"""
    if secret_key != settings.SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid secret key")

    if db_name not in get_available_databases():
        raise HTTPException(status_code=404, detail="Database not found")

    if db_name == get_current_db():
        raise HTTPException(status_code=400, detail="Cannot delete current database")

    if db_name == settings.DEFAULT_DB_NAME:
        raise HTTPException(status_code=400, detail="Cannot delete default database")

    db_path = os.path.join(settings.DB_DIR, f"{db_name}.sqlite")
    os.remove(db_path)
    return {"message": f"Deleted database: {db_name}"}


@router.post("/databases/upload")
async def upload_database(file: UploadFile = File(...), secret_key: str = None):
    """Upload a new database file"""
    if secret_key != settings.SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid secret key")

    if not file.filename.endswith(".sqlite"):
        raise HTTPException(status_code=400, detail="File must be a SQLite database")

    new_db_name = await handle_uploaded_db(file)
    return {"message": f"Uploaded database: {new_db_name}"}


@router.post("/crawler/start")
async def start_crawler(seed_urls: Optional[List[str]] = None, secret_key: str = None):
    """Start the crawler"""
    if secret_key != settings.SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid secret key")

    if is_crawler_running():
        raise HTTPException(status_code=400, detail="Crawler is already running")

    crawler = CrawlerService()
    await crawler.start(seed_urls)
    return {"message": "Crawler started"}


@router.post("/crawler/stop")
async def stop_crawler(secret_key: str = None):
    """Stop the crawler"""
    if secret_key != settings.SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid secret key")

    if not is_crawler_running():
        raise HTTPException(status_code=400, detail="Crawler is not running")

    crawler = get_current_crawler()
    if crawler:
        await crawler.stop()
    return {"message": "Crawler stopped"}


@router.get("/crawler/status")
async def get_crawler_status():
    """Get crawler status"""
    return {
        "status": "running" if is_crawler_running() else "stopped",
        "statistics": {
            "urls_crawled": 0,  # TODO: Get from CrawlerState
            "urls_failed": 0,  # TODO: Get from CrawlerState
            "urls_in_queue": (
                len(get_current_crawler().to_visit) if get_current_crawler() else 0
            ),
        },
    }


@router.get("/crawler/statistics")
async def get_detailed_statistics(db: Session = Depends(get_db)):
    stats = db.query(CrawlStatistics).order_by(CrawlStatistics.id.desc()).first()
    queue_size = len(get_current_crawler().to_visit) if get_current_crawler() else 0

    total_documents = db.query(Document).count()
    total_terms = db.query(Term).count()
    total_index_entries = db.query(InvertedIndex).count()

    return {
        "crawler_statistics": {
            "status": "running" if is_crawler_running() else "stopped",
            "urls_crawled": stats.urls_crawled if stats else 0,
            "urls_failed": stats.urls_failed if stats else 0,
            "unique_domains": stats.unique_domains if stats else 0,
            "urls_in_queue": queue_size,
        },
        "database_statistics": {
            "total_documents": total_documents,
            "total_terms": total_terms,
            "total_index_entries": total_index_entries,
        },
    }


@router.websocket("/crawler/ws")
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
    logger.info(message)
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


async def run_crawler(mode: str):
    """Main crawler loop."""
    global get_current_crawler, current_db_name
    session_factory = get_session_factory()
    session_factory.configure(bind=get_engine(current_db_name))
    db = session_factory()
    try:
        if mode == "fresh":
            get_current_crawler = CrawlerService(db)
            seed_urls = [
                "https://www.ics.uci.edu",
                "https://www.cs.uci.edu",
                "https://www.informatics.uci.edu",
                "https://www.stat.uci.edu",
            ]
            await get_current_crawler.crawl(seed_urls, mode="fresh")
        elif mode == "continue":
            await get_current_crawler.crawl(
                get_current_crawler.to_visit, mode="continue"
            )
        elif mode == "recrawl":
            get_current_crawler = CrawlerService(db)
            seed_urls = [
                "https://www.ics.uci.edu",
                "https://www.cs.uci.edu",
                "https://www.informatics.uci.edu",
                "https://www.stat.uci.edu",
            ]
            await get_current_crawler.crawl(seed_urls, mode="recrawl")
        await get_current_crawler.close()
    except Exception as e:
        logger.error(f"Crawler error: {str(e)}")
    finally:
        db.close()
        global crawler_running
        crawler_running = False
        get_current_crawler = None


@router.get("/search")
async def search(
    query: str = Query(..., description="Search query"),
    page: int = Query(1, description="Page number", ge=1),
    per_page: int = Query(10, description="Results per page", ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Search the crawled content."""
    search_service = SearchService(db)
    return search_service.search(query, page, per_page)


@router.get("/seed-urls")
async def get_seed_urls():
    """Get current seed URLs"""
    return {"seed_urls": get_seed_urls()}


@router.post("/seed-urls")
async def set_seed_urls(urls: List[str], secret_key: str = None):
    """Set seed URLs"""
    if secret_key != settings.SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid secret key")

    set_seed_urls(urls)
    return {"message": "Seed URLs updated"}
