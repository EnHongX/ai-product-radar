from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.tables import ExtractionLog, ProductRelease, RawArticle
from app.services.extraction_service import (
    batch_extract_from_articles,
    extract_from_article,
    get_extraction_stats,
)

router = APIRouter(tags=["extractions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SingleExtractRequest(BaseModel):
    article_id: int


class BatchExtractRequest(BaseModel):
    article_ids: list[int]


class ExtractResponse(BaseModel):
    success: bool
    raw_article_id: int | None
    releases_found: int
    releases_created: int
    releases_skipped: int
    error_message: str | None
    log_id: int | None
    release_ids: list[int]


class BatchExtractResponse(BaseModel):
    success: bool
    articles_processed: int
    articles_with_releases: int
    total_releases_found: int
    total_releases_created: int
    failed_articles: list[int]
    log_ids: list[int]


class TaskTriggerResponse(BaseModel):
    task_id: str
    message: str
    queued: bool


class ExtractionStatsResponse(BaseModel):
    total_extractions: int
    success: int
    failed: int
    running: int
    total_releases: int
    llm_enabled: bool
    llm_provider: str
    llm_model: str


class ExtractionLogResponse(BaseModel):
    id: int
    raw_article_id: int
    product_release_id: int | None
    status: str
    model_name: str | None
    prompt_version: str | None
    confidence_score: float | None
    error_message: str | None
    created_at: str

    class Config:
        from_attributes = True


class ProductReleaseResponse(BaseModel):
    id: int
    source_id: int
    raw_article_id: int | None
    release_title: str
    release_url: str
    release_date: str | None
    release_type: str
    summary: str | None
    confidence_score: float | None
    review_status: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("/extractions/stats", response_model=ExtractionStatsResponse)
def get_stats(db: Session = Depends(get_db)):
    stats = get_extraction_stats(db)
    return ExtractionStatsResponse(**stats)


@router.post("/extractions/extract", response_model=ExtractResponse)
def extract_single(
    request: SingleExtractRequest,
    db: Session = Depends(get_db),
):
    result: ExtractionResult = extract_from_article(db, request.article_id)
    return ExtractResponse(
        success=result.success,
        raw_article_id=result.raw_article_id,
        releases_found=result.releases_found,
        releases_created=result.releases_created,
        releases_skipped=result.releases_skipped,
        error_message=result.error_message,
        log_id=result.log_id,
        release_ids=result.release_ids,
    )


@router.post("/extractions/batch-extract", response_model=BatchExtractResponse)
def extract_batch(
    request: BatchExtractRequest,
    db: Session = Depends(get_db),
):
    result: BatchExtractionResult = batch_extract_from_articles(db, request.article_ids)
    return BatchExtractResponse(
        success=result.success,
        articles_processed=result.articles_processed,
        articles_with_releases=result.articles_with_releases,
        total_releases_found=result.total_releases_found,
        total_releases_created=result.total_releases_created,
        failed_articles=result.failed_articles,
        log_ids=result.log_ids,
    )


@router.post("/extractions/extract-async", response_model=TaskTriggerResponse)
def extract_single_async(
    request: SingleExtractRequest,
    db: Session = Depends(get_db),
):
    article = db.execute(
        select(RawArticle).where(RawArticle.id == request.article_id)
    ).scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    from app.worker.tasks import extract_article_task
    task = extract_article_task.delay(request.article_id)
    
    return TaskTriggerResponse(
        task_id=str(task.id),
        message="Extraction task has been queued",
        queued=True,
    )


@router.post("/extractions/batch-extract-async", response_model=TaskTriggerResponse)
def extract_batch_async(
    request: BatchExtractRequest,
    db: Session = Depends(get_db),
):
    if not request.article_ids:
        raise HTTPException(status_code=400, detail="No article IDs provided")
    
    from app.worker.tasks import batch_extract_task
    task = batch_extract_task.delay(request.article_ids)
    
    return TaskTriggerResponse(
        task_id=str(task.id),
        message=f"Batch extraction task for {len(request.article_ids)} articles has been queued",
        queued=True,
    )


@router.get("/extractions/logs", response_model=list[ExtractionLogResponse])
def list_extraction_logs(
    raw_article_id: Optional[int] = Query(None, description="Filter by article ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Number of logs to return"),
    db: Session = Depends(get_db),
):
    query = select(ExtractionLog).order_by(ExtractionLog.created_at.desc())
    
    if raw_article_id is not None:
        query = query.where(ExtractionLog.raw_article_id == raw_article_id)
    if status is not None:
        query = query.where(ExtractionLog.status == status)
    
    logs = db.execute(query.limit(limit)).scalars().all()
    
    return [
        ExtractionLogResponse(
            id=log.id,
            raw_article_id=log.raw_article_id,
            product_release_id=log.product_release_id,
            status=log.status,
            model_name=log.model_name,
            prompt_version=log.prompt_version,
            confidence_score=log.confidence_score,
            error_message=log.error_message,
            created_at=log.created_at.isoformat() if log.created_at else "",
        )
        for log in logs
    ]


@router.get("/extractions/releases", response_model=list[ProductReleaseResponse])
def list_releases(
    raw_article_id: Optional[int] = Query(None, description="Filter by article ID"),
    review_status: Optional[str] = Query(None, description="Filter by review status"),
    limit: int = Query(50, ge=1, le=200, description="Number of releases to return"),
    db: Session = Depends(get_db),
):
    query = select(ProductRelease).order_by(ProductRelease.created_at.desc())
    
    if raw_article_id is not None:
        query = query.where(ProductRelease.raw_article_id == raw_article_id)
    if review_status is not None:
        query = query.where(ProductRelease.review_status == review_status)
    
    releases = db.execute(query.limit(limit)).scalars().all()
    
    return [
        ProductReleaseResponse(
            id=r.id,
            source_id=r.source_id,
            raw_article_id=r.raw_article_id,
            release_title=r.release_title,
            release_url=r.release_url,
            release_date=r.release_date.isoformat() if r.release_date else None,
            release_type=r.release_type,
            summary=r.summary,
            confidence_score=r.confidence_score,
            review_status=r.review_status,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in releases
    ]


@router.get("/extractions/releases/{release_id}", response_model=ProductReleaseResponse)
def get_release(release_id: int, db: Session = Depends(get_db)):
    release = db.execute(
        select(ProductRelease).where(ProductRelease.id == release_id)
    ).scalar_one_or_none()
    
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    
    return ProductReleaseResponse(
        id=release.id,
        source_id=release.source_id,
        raw_article_id=release.raw_article_id,
        release_title=release.release_title,
        release_url=release.release_url,
        release_date=release.release_date.isoformat() if release.release_date else None,
        release_type=release.release_type,
        summary=release.summary,
        confidence_score=release.confidence_score,
        review_status=release.review_status,
        created_at=release.created_at.isoformat() if release.created_at else "",
    )


@router.get("/extractions/pending-extraction", response_model=list[int])
def get_pending_articles(
    limit: int = Query(100, ge=1, le=500, description="Max number of article IDs to return"),
    db: Session = Depends(get_db),
):
    from sqlalchemy.orm import aliased
    
    extraction_log_alias = aliased(ExtractionLog)
    
    subquery = (
        select(extraction_log_alias.raw_article_id)
        .where(extraction_log_alias.raw_article_id == RawArticle.id)
        .exists()
    )
    
    query = (
        select(RawArticle.id)
        .where(RawArticle.content.is_not(None))
        .where(~subquery)
        .order_by(RawArticle.fetched_at.desc())
        .limit(limit)
    )
    
    article_ids = db.execute(query).scalars().all()
    
    return list(article_ids)
