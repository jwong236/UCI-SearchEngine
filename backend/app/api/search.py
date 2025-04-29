from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..services.search_service import SearchService

router = APIRouter()


@router.get("/")
async def search(
    query: str = Query(..., description="Search query"),
    page: int = Query(1, description="Page number", ge=1),
    per_page: int = Query(10, description="Results per page", ge=1, le=50),
    db: Session = Depends(get_db),
):
    search_service = SearchService(db)
    return search_service.search(query, page, per_page)
