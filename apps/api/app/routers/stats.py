from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.tables import Company, Product, Source, RawArticle, CrawlLog

router = APIRouter(tags=["stats"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)) -> dict:
    companies_count = db.execute(select(func.count(Company.id))).scalar() or 0
    sources_count = db.execute(select(func.count(Source.id))).scalar() or 0
    products_count = db.execute(select(func.count(Product.id))).scalar() or 0
    raw_articles_count = db.execute(select(func.count(RawArticle.id))).scalar() or 0
    crawl_logs_count = db.execute(select(func.count(CrawlLog.id))).scalar() or 0
    
    success_crawl_count = db.execute(
        select(func.count(CrawlLog.id)).where(CrawlLog.status == "success")
    ).scalar() or 0
    failed_crawl_count = db.execute(
        select(func.count(CrawlLog.id)).where(CrawlLog.status == "failed")
    ).scalar() or 0

    return {
        "companies": companies_count,
        "sources": sources_count,
        "products": products_count,
        "raw_articles": raw_articles_count,
        "crawl_logs": crawl_logs_count,
        "crawl_stats": {
            "success": success_crawl_count,
            "failed": failed_crawl_count,
        },
    }
