from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.db.session import SessionLocal
from app.models.tables import Source, RawArticle, ProductRelease, Company

router = APIRouter(tags=["sources"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SourceCreate(BaseModel):
    company_id: int
    name: str
    url: str
    source_type: str
    parse_strategy: str
    enabled: bool = True
    crawl_interval_hours: int = 24

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("url")
    @classmethod
    def url_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("URL cannot be empty")
        return v.strip()

    @field_validator("source_type")
    @classmethod
    def source_type_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Source type cannot be empty")
        return v.strip()

    @field_validator("parse_strategy")
    @classmethod
    def parse_strategy_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Parse strategy cannot be empty")
        return v.strip()

    @field_validator("crawl_interval_hours")
    @classmethod
    def crawl_interval_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Crawl interval must be positive")
        return v


class SourceUpdate(BaseModel):
    company_id: Optional[int] = None
    name: Optional[str] = None
    url: Optional[str] = None
    source_type: Optional[str] = None
    parse_strategy: Optional[str] = None
    enabled: Optional[bool] = None
    crawl_interval_hours: Optional[int] = None

    @field_validator("crawl_interval_hours")
    @classmethod
    def crawl_interval_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Crawl interval must be positive")
        return v


class SourceCompanyResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SourceResponse(BaseModel):
    id: int
    company_id: int
    name: str
    url: str
    source_type: str
    parse_strategy: str
    enabled: bool
    crawl_interval_hours: int
    last_crawled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    company: SourceCompanyResponse | None = None

    class Config:
        from_attributes = True


class SourceDeleteCheckResponse(BaseModel):
    can_delete: bool
    raw_articles_count: int
    product_releases_count: int
    message: str


@router.get("/sources", response_model=list[SourceResponse])
def list_sources(
    company_id: Optional[int] = Query(None, description="Filter sources by company ID"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: Session = Depends(get_db),
):
    query = select(Source).options(selectinload(Source.company)).order_by(Source.created_at.desc())
    
    if company_id is not None:
        query = query.where(Source.company_id == company_id)
    if enabled is not None:
        query = query.where(Source.enabled == enabled)
    
    sources = db.execute(query).scalars().all()
    return sources


@router.get("/sources/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, db: Session = Depends(get_db)):
    source = db.execute(
        select(Source).options(selectinload(Source.company)).where(Source.id == source_id)
    ).scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.get("/sources/{source_id}/delete-check", response_model=SourceDeleteCheckResponse)
def check_source_delete(source_id: int, db: Session = Depends(get_db)):
    source = db.execute(select(Source).where(Source.id == source_id)).scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    raw_articles_count = db.execute(
        select(func.count(RawArticle.id)).where(RawArticle.source_id == source_id)
    ).scalar() or 0
    
    product_releases_count = db.execute(
        select(func.count(ProductRelease.id)).where(ProductRelease.source_id == source_id)
    ).scalar() or 0
    
    can_delete = raw_articles_count == 0 and product_releases_count == 0
    
    if can_delete:
        message = "Source can be safely deleted"
    else:
        parts = []
        if raw_articles_count > 0:
            parts.append(f"{raw_articles_count} article(s)")
        if product_releases_count > 0:
            parts.append(f"{product_releases_count} release(s)")
        message = f"Cannot delete: has {', '.join(parts)}"
    
    return SourceDeleteCheckResponse(
        can_delete=can_delete,
        raw_articles_count=raw_articles_count,
        product_releases_count=product_releases_count,
        message=message,
    )


@router.post("/sources", response_model=SourceResponse)
def create_source(data: SourceCreate, db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.id == data.company_id)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=400, detail="Company not found")
    
    existing = db.execute(select(Source).where(Source.url == data.url)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Source with this URL already exists")
    
    source = Source(
        company_id=data.company_id,
        name=data.name,
        url=data.url,
        source_type=data.source_type,
        parse_strategy=data.parse_strategy,
        enabled=data.enabled,
        crawl_interval_hours=data.crawl_interval_hours,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    
    source = db.execute(
        select(Source).options(selectinload(Source.company)).where(Source.id == source.id)
    ).scalar_one()
    return source


@router.put("/sources/{source_id}", response_model=SourceResponse)
def update_source(source_id: int, data: SourceUpdate, db: Session = Depends(get_db)):
    source = db.execute(
        select(Source).options(selectinload(Source.company)).where(Source.id == source_id)
    ).scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    if "company_id" in update_data:
        company = db.execute(select(Company).where(Company.id == update_data["company_id"])).scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=400, detail="Company not found")
    
    if "url" in update_data:
        existing = db.execute(
            select(Source).where(Source.url == update_data["url"], Source.id != source_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Source with this URL already exists")
    
    for key, value in update_data.items():
        if hasattr(source, key):
            setattr(source, key, value)
    
    db.commit()
    db.refresh(source)
    
    source = db.execute(
        select(Source).options(selectinload(Source.company)).where(Source.id == source.id)
    ).scalar_one()
    return source


@router.delete("/sources/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.execute(select(Source).where(Source.id == source_id)).scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    raw_articles_count = db.execute(
        select(func.count(RawArticle.id)).where(RawArticle.source_id == source_id)
    ).scalar() or 0
    
    product_releases_count = db.execute(
        select(func.count(ProductRelease.id)).where(ProductRelease.source_id == source_id)
    ).scalar() or 0
    
    if raw_articles_count > 0 or product_releases_count > 0:
        parts = []
        if raw_articles_count > 0:
            parts.append(f"{raw_articles_count} article(s)")
        if product_releases_count > 0:
            parts.append(f"{product_releases_count} release(s)")
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete source: has {', '.join(parts)}. Please disable it instead.",
        )
    
    db.delete(source)
    db.commit()
    return {"message": "Source deleted successfully"}
