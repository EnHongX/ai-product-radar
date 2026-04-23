import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.logging import get_logger
from app.models.tables import (
    ExtractionLog,
    ProductRelease,
    RawArticle,
    ReviewTask,
)

logger = get_logger(__name__)


@dataclass
class ExtractedRelease:
    release_title: str
    release_url: str
    release_date: str | None = None
    release_type: str = "new"
    summary: str | None = None
    confidence_score: float | None = None
    raw_payload: dict[str, Any] | None = None


@dataclass
class ExtractionResult:
    success: bool = False
    raw_article_id: int | None = None
    releases_found: int = 0
    releases_created: int = 0
    releases_skipped: int = 0
    error_message: str | None = None
    log_id: int | None = None
    release_ids: list[int] = field(default_factory=list)


@dataclass
class BatchExtractionResult:
    success: bool = False
    articles_processed: int = 0
    articles_with_releases: int = 0
    total_releases_found: int = 0
    total_releases_created: int = 0
    failed_articles: list[int] = field(default_factory=list)
    log_ids: list[int] = field(default_factory=list)


def calculate_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def extract_from_article(
    db: Session,
    article_id: int,
) -> ExtractionResult:
    result = ExtractionResult(raw_article_id=article_id)
    
    article = db.execute(
        select(RawArticle).options(
            selectinload(RawArticle.source),
            selectinload(RawArticle.extraction_logs),
        ).where(RawArticle.id == article_id)
    ).scalar_one_or_none()
    
    if not article:
        result.error_message = f"Article with id {article_id} not found"
        logger.error(result.error_message)
        return result
    
    if not article.content:
        result.error_message = f"Article {article_id} has no content to extract from"
        logger.warning(result.error_message)
        return result
    
    log = ExtractionLog(
        raw_article_id=article.id,
        status="running",
        model_name=settings.LLM_MODEL if settings.llm_enabled else "none",
        prompt_version=settings.LLM_EXTRACTION_PROMPT_VERSION,
        input_hash=calculate_hash(article.content),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    result.log_id = log.id
    
    try:
        if not settings.llm_enabled:
            releases = _mock_extract(article)
            logger.info(
                f"LLM disabled, using mock extraction for article {article_id}, found {len(releases)} releases"
            )
        else:
            releases = _llm_extract(article)
            logger.info(
                f"LLM extraction for article {article_id}, found {len(releases)} releases"
            )
        
        result.releases_found = len(releases)
        
        if len(releases) == 0:
            log.status = "success"
            log.output_payload = {"releases": []}
            db.commit()
            result.success = True
            return result
        
        for extracted in releases:
            release = _create_release_from_extracted(db, article, extracted)
            if release:
                result.releases_created += 1
                result.release_ids.append(release.id)
                
                review_task = ReviewTask(
                    raw_article_id=article.id,
                    product_release_id=release.id,
                    status="pending",
                    priority=_calculate_priority(extracted),
                )
                db.add(review_task)
            else:
                result.releases_skipped += 1
        
        log.status = "success"
        log.output_payload = {
            "releases": [r.raw_payload for r in releases if r.raw_payload],
            "count": len(releases),
        }
        log.confidence_score = _calculate_average_confidence(releases)
        db.commit()
        
        result.success = True
        logger.info(
            f"Extraction completed for article {article_id}: "
            f"{result.releases_created} created, {result.releases_skipped} skipped"
        )
        
    except Exception as e:
        db.rollback()
        log.status = "failed"
        log.error_message = str(e)
        db.commit()
        
        result.error_message = str(e)
        logger.exception(f"Extraction failed for article {article_id}: {e}")
    
    return result


def batch_extract_from_articles(
    db: Session,
    article_ids: list[int],
) -> BatchExtractionResult:
    result = BatchExtractionResult()
    
    for article_id in article_ids:
        try:
            ext_result = extract_from_article(db, article_id)
            result.articles_processed += 1
            
            if ext_result.success:
                if ext_result.releases_created > 0:
                    result.articles_with_releases += 1
                result.total_releases_found += ext_result.releases_found
                result.total_releases_created += ext_result.releases_created
                if ext_result.log_id:
                    result.log_ids.append(ext_result.log_id)
            else:
                result.failed_articles.append(article_id)
                logger.warning(f"Extraction failed for article {article_id}: {ext_result.error_message}")
                
        except Exception as e:
            result.failed_articles.append(article_id)
            logger.exception(f"Error processing article {article_id}: {e}")
    
    result.success = len(result.failed_articles) == 0 or result.articles_processed > 0
    
    logger.info(
        f"Batch extraction completed: {result.articles_processed} processed, "
        f"{result.articles_with_releases} with releases, "
        f"{result.total_releases_created} total created, "
        f"{len(result.failed_articles)} failed"
    )
    
    return result


def get_extraction_stats(db: Session) -> dict[str, Any]:
    from sqlalchemy import func
    
    total_logs = db.execute(select(func.count(ExtractionLog.id))).scalar() or 0
    success_logs = db.execute(
        select(func.count(ExtractionLog.id)).where(ExtractionLog.status == "success")
    ).scalar() or 0
    failed_logs = db.execute(
        select(func.count(ExtractionLog.id)).where(ExtractionLog.status == "failed")
    ).scalar() or 0
    running_logs = db.execute(
        select(func.count(ExtractionLog.id)).where(ExtractionLog.status == "running")
    ).scalar() or 0
    
    total_releases = db.execute(select(func.count(ProductRelease.id))).scalar() or 0
    
    return {
        "total_extractions": total_logs,
        "success": success_logs,
        "failed": failed_logs,
        "running": running_logs,
        "total_releases": total_releases,
        "llm_enabled": settings.llm_enabled,
        "llm_provider": settings.LLM_PROVIDER if settings.llm_enabled else "none",
        "llm_model": settings.LLM_MODEL if settings.llm_enabled else "none",
    }


def _mock_extract(article: RawArticle) -> list[ExtractedRelease]:
    releases: list[ExtractedRelease] = []
    
    title_lower = article.title.lower() if article.title else ""
    content_lower = article.content.lower() if article.content else ""
    
    release_keywords = ["release", "launch", "announce", "introduce", "unveil", "beta", "preview", "available"]
    product_keywords = ["gpt", "claude", "model", "api", "feature", "product", "service", "plugin"]
    
    has_release_indicator = any(kw in title_lower for kw in release_keywords)
    has_product_indicator = any(kw in title_lower or kw in content_lower for kw in product_keywords)
    
    if has_release_indicator or has_product_indicator:
        release_type = "update"
        
        if "new" in title_lower or "introduce" in title_lower or "launch" in title_lower:
            release_type = "new"
        elif "update" in title_lower or "upgrade" in title_lower:
            release_type = "update"
        elif "beta" in title_lower or "preview" in title_lower:
            release_type = "beta"
        
        release = ExtractedRelease(
            release_title=article.title,
            release_url=article.url,
            release_date=article.published_at.isoformat() if article.published_at else None,
            release_type=release_type,
            summary=article.content[:500] if article.content and len(article.content) > 500 else article.content,
            confidence_score=0.5,
            raw_payload={
                "source": "mock",
                "title_keywords": [kw for kw in release_keywords if kw in title_lower],
                "content_keywords": [kw for kw in product_keywords if kw in content_lower],
            },
        )
        releases.append(release)
    
    return releases


def _llm_extract(article: RawArticle) -> list[ExtractedRelease]:
    logger.warning(
        f"LLM extraction called but not fully implemented. "
        f"Provider: {settings.LLM_PROVIDER}, Model: {settings.LLM_MODEL}"
    )
    
    return _mock_extract(article)


def _create_release_from_extracted(
    db: Session,
    article: RawArticle,
    extracted: ExtractedRelease,
) -> ProductRelease | None:
    existing = db.execute(
        select(ProductRelease).where(ProductRelease.release_url == extracted.release_url)
    ).scalar_one_or_none()
    
    if existing:
        logger.info(f"Release with URL {extracted.release_url} already exists, skipping")
        return None
    
    release_title = extracted.release_title[:512] if extracted.release_title else article.title
    release_url = extracted.release_url[:2048] if extracted.release_url else article.url
    
    if not release_title or not release_url:
        logger.warning("Cannot create release: missing title or URL")
        return None
    
    try:
        release_date = None
        if extracted.release_date:
            if isinstance(extracted.release_date, str):
                release_date = datetime.fromisoformat(extracted.release_date.replace("Z", "+00:00"))
            else:
                release_date = extracted.release_date
    except ValueError:
        release_date = article.published_at
    
    raw_content_hash = calculate_hash(
        f"{release_title}:{release_url}:{extracted.summary or ''}"
    )
    
    existing_hash = db.execute(
        select(ProductRelease).where(ProductRelease.raw_content_hash == raw_content_hash)
    ).scalar_one_or_none()
    
    if existing_hash:
        logger.info(f"Release with same content already exists (hash: {raw_content_hash}), skipping")
        return None
    
    release = ProductRelease(
        source_id=article.source_id,
        raw_article_id=article.id,
        release_title=release_title,
        release_url=release_url,
        release_date=release_date,
        release_type=extracted.release_type or "new",
        summary=extracted.summary,
        confidence_score=extracted.confidence_score,
        raw_content_hash=raw_content_hash,
        extraction_payload=extracted.raw_payload,
        review_status="pending",
    )
    
    db.add(release)
    db.flush()
    
    return release


def _calculate_priority(extracted: ExtractedRelease) -> int:
    if not extracted.confidence_score:
        return 0
    
    if extracted.confidence_score >= 0.9:
        return 1
    elif extracted.confidence_score >= 0.7:
        return 0
    else:
        return -1


def _calculate_average_confidence(releases: list[ExtractedRelease]) -> float | None:
    scores = [r.confidence_score for r in releases if r.confidence_score is not None]
    if not scores:
        return None
    return sum(scores) / len(scores)
