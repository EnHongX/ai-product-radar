from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded, TimeLimitExceeded
from datetime import datetime, timezone

from app.worker.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.crawl_service import crawl_source, CrawlResult
from app.services.extraction_service import (
    ExtractionResult,
    BatchExtractionResult,
    extract_from_article,
    batch_extract_from_articles,
)
from app.models.tables import CrawlLog, ExtractionLog
from app.core.config import settings


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
    except (SoftTimeLimitExceeded, TimeLimitExceeded) as e:
        _handle_crawl_timeout(db, source_id, str(e))
        return {
            "success": False,
            "articles_found": 0,
            "articles_created": 0,
            "articles_skipped": 0,
            "articles_failed": 0,
            "error_message": f"Crawl task timed out after {settings.CRAWL_TIMEOUT_SECONDS} seconds",
            "log_metadata": None,
            "article_records": [],
        }
    except Exception as e:
        return {
            "success": False,
            "articles_found": 0,
            "articles_created": 0,
            "articles_skipped": 0,
            "articles_failed": 0,
            "error_message": str(e),
            "log_metadata": None,
            "article_records": [],
        }
    finally:
        db.close()


def _handle_crawl_timeout(db: SessionLocal, source_id: int, error_msg: str):
    from sqlalchemy import select
    from app.models.tables import CrawlLog
    
    try:
        log = db.execute(
            select(CrawlLog)
            .where(CrawlLog.source_id == source_id)
            .where(CrawlLog.status == "running")
            .order_by(CrawlLog.started_at.desc())
        ).scalar_one_or_none()
        
        if log:
            log.status = "failed"
            log.error_message = f"Crawl task timed out after {settings.CRAWL_TIMEOUT_SECONDS} seconds"
            log.finished_at = datetime.now(timezone.utc)
            
            existing_metadata = log.log_metadata or {}
            existing_metadata["timeout"] = True
            existing_metadata["timeout_seconds"] = settings.CRAWL_TIMEOUT_SECONDS
            log.log_metadata = existing_metadata
            
            db.commit()
    except Exception:
        db.rollback()


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
    except (SoftTimeLimitExceeded, TimeLimitExceeded) as e:
        _handle_extraction_timeout(db, article_id, str(e))
        return {
            "success": False,
            "raw_article_id": article_id,
            "releases_found": 0,
            "releases_created": 0,
            "releases_skipped": 0,
            "error_message": f"Extraction task timed out after {settings.EXTRACTION_TIMEOUT_SECONDS} seconds",
            "log_id": None,
            "release_ids": [],
        }
    except Exception as e:
        return {
            "success": False,
            "raw_article_id": article_id,
            "releases_found": 0,
            "releases_created": 0,
            "releases_skipped": 0,
            "error_message": str(e),
            "log_id": None,
            "release_ids": [],
        }
    finally:
        db.close()


def _handle_extraction_timeout(db: SessionLocal, article_id: int, error_msg: str):
    from sqlalchemy import select
    from app.models.tables import ExtractionLog
    
    try:
        log = db.execute(
            select(ExtractionLog)
            .where(ExtractionLog.raw_article_id == article_id)
            .where(ExtractionLog.status == "running")
            .order_by(ExtractionLog.created_at.desc())
        ).scalar_one_or_none()
        
        if log:
            log.status = "failed"
            log.error_message = f"Extraction task timed out after {settings.EXTRACTION_TIMEOUT_SECONDS} seconds"
            db.commit()
    except Exception:
        db.rollback()


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
    except (SoftTimeLimitExceeded, TimeLimitExceeded) as e:
        return {
            "success": False,
            "articles_processed": 0,
            "articles_with_releases": 0,
            "total_releases_found": 0,
            "total_releases_created": 0,
            "failed_articles": article_ids,
            "log_ids": [],
            "error_message": f"Batch extraction task timed out",
        }
    except Exception as e:
        return {
            "success": False,
            "articles_processed": 0,
            "articles_with_releases": 0,
            "total_releases_found": 0,
            "total_releases_created": 0,
            "failed_articles": article_ids,
            "log_ids": [],
            "error_message": str(e),
        }
    finally:
        db.close()
