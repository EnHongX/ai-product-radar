from app.worker.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.crawl_service import crawl_source, CrawlResult
from app.services.extraction_service import (
    ExtractionResult,
    BatchExtractionResult,
    extract_from_article,
    batch_extract_from_articles,
)


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
            "articles_skipped": result.articles_skipped,
            "articles_failed": result.articles_failed,
            "error_message": result.error_message,
            "log_metadata": result.log_metadata,
            "article_records": result.article_records,
        }
    finally:
        db.close()


@celery_app.task(name="extraction.extract_article", bind=True)
def extract_article_task(self, article_id: int) -> dict:
    db = SessionLocal()
    try:
        result: ExtractionResult = extract_from_article(db, article_id)
        return {
            "success": result.success,
            "raw_article_id": result.raw_article_id,
            "releases_found": result.releases_found,
            "releases_created": result.releases_created,
            "releases_skipped": result.releases_skipped,
            "error_message": result.error_message,
            "log_id": result.log_id,
            "release_ids": result.release_ids,
        }
    finally:
        db.close()


@celery_app.task(name="extraction.batch_extract", bind=True)
def batch_extract_task(self, article_ids: list[int]) -> dict:
    db = SessionLocal()
    try:
        result: BatchExtractionResult = batch_extract_from_articles(db, article_ids)
        return {
            "success": result.success,
            "articles_processed": result.articles_processed,
            "articles_with_releases": result.articles_with_releases,
            "total_releases_found": result.total_releases_found,
            "total_releases_created": result.total_releases_created,
            "failed_articles": result.failed_articles,
            "log_ids": result.log_ids,
        }
    finally:
        db.close()
