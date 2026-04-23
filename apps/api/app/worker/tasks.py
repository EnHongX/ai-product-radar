from app.worker.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.crawl_service import crawl_source, CrawlResult


@celery_app.task(name="system.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="crawl.crawl_source", bind=True)
def crawl_source_task(self, source_id: int) -> dict:
    db = SessionLocal()
    try:
        result: CrawlResult = crawl_source(db, source_id)
        return {
            "success": result.success,
            "articles_found": result.articles_found,
            "articles_created": result.articles_created,
            "articles_failed": result.articles_failed,
            "error_message": result.error_message,
            "log_metadata": result.log_metadata,
        }
    finally:
        db.close()
