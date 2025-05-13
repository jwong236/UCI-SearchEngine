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
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..database.connection import (
    get_db,
    get_session_factory,
    get_engine,
    handle_uploaded_db,
    setup_connections,
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
from .websocket_utils import active_websockets, broadcast_log
from ..config.globals import (
    logger,
    get_current_db,
    set_current_db,
    get_available_databases,
    is_crawler_running,
    get_current_crawler,
    get_seed_urls,
    set_seed_urls,
    set_crawler_running,
    set_crawler_task,
    set_current_crawler,
)
from ..config.settings import settings
from sqlalchemy import select

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
async def start_crawler(
    seed_urls: List[str],
    mode: str = Query(..., description="Crawler mode: fresh, continue, or recrawl"),
    x_secret_key: str = Depends(verify_secret_key),
):
    """Start the crawler with the specified seed URLs"""
    if is_crawler_running():
        raise HTTPException(status_code=400, detail="Crawler is already running")

    try:
        if mode == "fresh":
            crawler = CrawlerService()
            await crawler.start(seed_urls)
        elif mode == "continue":
            crawler = get_current_crawler()
            if crawler:
                await crawler.start(crawler.to_visit)
            else:
                raise HTTPException(
                    status_code=400, detail="No crawler instance found to continue"
                )
        elif mode == "recrawl":
            crawler = CrawlerService()
            await crawler.start(seed_urls)
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid mode. Must be one of: fresh, continue, recrawl",
            )

        return {"message": "Crawler started successfully"}

    except Exception as e:
        logger.error(f"Error starting crawler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crawler/stop")
async def stop_crawler(x_secret_key: str = Depends(verify_secret_key)):
    """Stop the crawler"""
    if not is_crawler_running():
        raise HTTPException(status_code=400, detail="Crawler is not running")

    try:
        crawler = get_current_crawler()
        if crawler:
            await crawler.stop()
            return {"message": "Crawler stopped successfully"}
        else:
            raise HTTPException(
                status_code=400, detail="No crawler instance found to stop"
            )
    except Exception as e:
        logger.error(f"Error stopping crawler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crawler/status")
async def get_crawler_status():
    """Get crawler status"""
    async with get_db() as db:
        state = (
            await db.execute(select(CrawlerState).order_by(CrawlerState.id.desc()))
        ).scalar_one_or_none()
        return {
            "status": "running" if is_crawler_running() else "stopped",
            "statistics": {
                "urls_crawled": state.urls_visited if state else 0,
                "urls_failed": state.urls_failed if state else 0,
                "urls_in_queue": state.urls_queued if state else 0,
            },
        }


@router.get("/crawler/statistics")
async def get_detailed_statistics(db: AsyncSession = Depends(get_db)):
    """Get detailed crawler statistics"""
    stats = (
        await db.execute(select(CrawlStatistics).order_by(CrawlStatistics.id.desc()))
    ).scalar_one_or_none()

    queue_size = len(get_current_crawler().to_visit) if get_current_crawler() else 0

    total_documents = (await db.execute(select(Document))).scalars().count()
    total_terms = (await db.execute(select(Term))).scalars().count()
    total_index_entries = (await db.execute(select(InvertedIndex))).scalars().count()

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
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        if websocket in active_websockets:
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
    async with get_db() as db:
        try:
            if mode == "fresh":
                crawler = CrawlerService()
                seed_urls = [
                    "https://www.ics.uci.edu",
                    "https://www.cs.uci.edu",
                    "https://www.informatics.uci.edu",
                    "https://www.stat.uci.edu",
                ]
                await crawler.start(seed_urls)
            elif mode == "continue":
                crawler = get_current_crawler()
                if crawler:
                    await crawler.start(crawler.to_visit)
            elif mode == "recrawl":
                crawler = CrawlerService()
                seed_urls = [
                    "https://www.ics.uci.edu",
                    "https://www.cs.uci.edu",
                    "https://www.informatics.uci.edu",
                    "https://www.stat.uci.edu",
                ]
                await crawler.start(seed_urls)

            if crawler:
                await crawler.close()
        except Exception as e:
            logger.error(f"Crawler error: {str(e)}")
        finally:
            set_crawler_running(False)
            set_crawler_task(None)
            set_current_crawler(None)


@router.get("/search")
async def search(
    query: str = Query(..., description="Search query"),
    page: int = Query(1, description="Page number", ge=1),
    per_page: int = Query(10, description="Results per page", ge=1, le=50),
    db: AsyncSession = Depends(get_db),
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
