from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.db.session import SessionLocal
from app.models.tables import RawArticle, CrawlLog, Source, Company

router = APIRouter(tags=["raw-articles"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class RawArticleSourceResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class RawArticleCompanyResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class RawArticleListResponse(BaseModel):
    id: int
    source_id: int
    title: str
    url: str
    published_at: datetime | None
    author: str | None
    fetched_at: datetime
    source: RawArticleSourceResponse | None = None
    company: RawArticleCompanyResponse | None = None

    class Config:
        from_attributes = True


class RawArticleDetailResponse(BaseModel):
    id: int
    source_id: int
    title: str
    url: str
    published_at: datetime | None
    author: str | None
    content: str | None
    content_hash: str
    fetched_at: datetime
    raw_metadata: dict | None
    source: RawArticleSourceResponse | None = None
    company: RawArticleCompanyResponse | None = None

    class Config:
        from_attributes = True


class CrawlLogSourceResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CrawlLogCompanyResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CrawlLogListResponse(BaseModel):
    id: int
    source_id: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    articles_found: int
    articles_created: int
    error_message: str | None
    log_metadata: dict | None
    created_at: datetime
    source: CrawlLogSourceResponse | None = None
    company: CrawlLogCompanyResponse | None = None

    class Config:
        from_attributes = True


@router.get("/raw-articles", response_model=list[RawArticleListResponse])
def list_raw_articles(
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of articles to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    query = (
        select(RawArticle)
        .options(
            selectinload(RawArticle.source).selectinload(Source.company)
        )
        .order_by(RawArticle.published_at.desc().nulls_last(), RawArticle.fetched_at.desc())
    )

    if source_id is not None:
        query = query.where(RawArticle.source_id == source_id)

    if company_id is not None:
        query = query.join(Source).where(Source.company_id == company_id)

    articles = db.execute(
        query.offset(offset).limit(limit)
    ).scalars().all()

    result = []
    for article in articles:
        article_data = RawArticleListResponse.model_validate(article)
        if article.source:
            article_data.source = RawArticleSourceResponse.model_validate(article.source)
            if article.source.company:
                article_data.company = RawArticleCompanyResponse.model_validate(article.source.company)
        result.append(article_data)

    return result


@router.get("/raw-articles/{article_id}", response_model=RawArticleDetailResponse)
def get_raw_article(article_id: int, db: Session = Depends(get_db)):
    article = db.execute(
        select(RawArticle)
        .options(
            selectinload(RawArticle.source).selectinload(Source.company)
        )
        .where(RawArticle.id == article_id)
    ).scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    result = RawArticleDetailResponse.model_validate(article)
    if article.source:
        result.source = RawArticleSourceResponse.model_validate(article.source)
        if article.source.company:
            result.company = RawArticleCompanyResponse.model_validate(article.source.company)

    return result


@router.delete("/raw-articles/{article_id}")
def delete_raw_article(article_id: int, db: Session = Depends(get_db)):
    article = db.execute(select(RawArticle).where(RawArticle.id == article_id)).scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    db.delete(article)
    db.commit()

    return {"message": "Article deleted successfully"}


@router.get("/crawl-logs", response_model=list[CrawlLogListResponse])
def list_crawl_logs(
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    query = (
        select(CrawlLog)
        .options(
            selectinload(CrawlLog.source).selectinload(Source.company)
        )
        .order_by(CrawlLog.started_at.desc())
    )

    if source_id is not None:
        query = query.where(CrawlLog.source_id == source_id)

    if company_id is not None:
        query = query.join(Source).where(Source.company_id == company_id)

    if status is not None:
        query = query.where(CrawlLog.status == status)

    logs = db.execute(
        query.offset(offset).limit(limit)
    ).scalars().all()

    result = []
    for log in logs:
        log_data = CrawlLogListResponse.model_validate(log)
        if log.source:
            log_data.source = CrawlLogSourceResponse.model_validate(log.source)
            if log.source.company:
                log_data.company = CrawlLogCompanyResponse.model_validate(log.source.company)
        result.append(log_data)

    return result


@router.get("/crawl-logs/{log_id}", response_model=CrawlLogListResponse)
def get_crawl_log(log_id: int, db: Session = Depends(get_db)):
    log = db.execute(
        select(CrawlLog)
        .options(
            selectinload(CrawlLog.source).selectinload(Source.company)
        )
        .where(CrawlLog.id == log_id)
    ).scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Crawl log not found")

    result = CrawlLogListResponse.model_validate(log)
    if log.source:
        result.source = CrawlLogSourceResponse.model_validate(log.source)
        if log.source.company:
            result.company = CrawlLogCompanyResponse.model_validate(log.source.company)

    return result
