from datetime import datetime, timezone
from typing import Any, NamedTuple
import hashlib

import feedparser
import httpx
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.tables import Source, RawArticle, CrawlLog


class CrawlResult(NamedTuple):
    success: bool
    articles_found: int
    articles_created: int
    error_message: str | None = None
    log_metadata: dict | None = None


def parse_rss_entry(entry: Any, source_url: str) -> dict[str, Any]:
    title = entry.get("title", "Untitled")
    url = entry.get("link") or entry.get("id") or ""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    author = entry.get("author") or entry.get("dc:creator")
    
    content = ""
    if entry.get("summary"):
        content = entry["summary"]
    elif entry.get("content"):
        for content_item in entry["content"]:
            if content_item.get("value"):
                content = content_item["value"]
                break
    
    if hasattr(entry, "description"):
        content = content or entry.description
    
    published_at = None
    if published:
        try:
            published_at = datetime(*published[:6], tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass
    
    content_for_hash = f"{title}|{content}"
    content_hash = hashlib.sha256(content_for_hash.encode("utf-8")).hexdigest()
    
    raw_metadata = {
        "source_url": source_url,
        "entry_id": entry.get("id"),
        "tags": [tag.get("term") for tag in entry.get("tags", [])] if entry.get("tags") else None,
    }
    
    return {
        "title": title,
        "url": url,
        "published_at": published_at,
        "author": author,
        "content": content if content else None,
        "content_hash": content_hash,
        "raw_metadata": raw_metadata,
    }


def fetch_rss_feed(url: str) -> feedparser.FeedParserDict:
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return feedparser.parse(response.content)


def crawl_rss_source(db: Session, source_id: int) -> CrawlResult:
    source = db.execute(select(Source).where(Source.id == source_id)).scalar_one_or_none()
    
    if not source:
        return CrawlResult(
            success=False,
            articles_found=0,
            articles_created=0,
            error_message="Source not found",
        )
    
    if not source.enabled:
        return CrawlResult(
            success=False,
            articles_found=0,
            articles_created=0,
            error_message="Source is disabled",
        )
    
    if source.parse_strategy != "rss_feed":
        return CrawlResult(
            success=False,
            articles_found=0,
            articles_created=0,
            error_message=f"Unsupported parse strategy: {source.parse_strategy}. Only rss_feed is supported.",
        )
    
    crawl_log = CrawlLog(
        source_id=source_id,
        status="running",
        articles_found=0,
        articles_created=0,
    )
    db.add(crawl_log)
    db.commit()
    db.refresh(crawl_log)
    
    try:
        feed = fetch_rss_feed(source.url)
        
        if feed.bozo and feed.bozo_exception:
            raise Exception(f"RSS parsing error: {feed.bozo_exception}")
        
        entries = feed.entries or []
        articles_found = len(entries)
        articles_created = 0
        
        existing_urls = set()
        existing_hashes = set()
        
        if entries:
            urls = [entry.get("link") or entry.get("id") or "" for entry in entries]
            if urls:
                existing_records = db.execute(
                    select(RawArticle.url, RawArticle.content_hash)
                    .where(or_(RawArticle.url.in_(urls)))
                ).all()
                existing_urls = {r[0] for r in existing_records}
                existing_hashes = {r[1] for r in existing_records}
        
        fetched_at = datetime.now(timezone.utc)
        
        for entry in entries:
            try:
                article_data = parse_rss_entry(entry, source.url)
                
                if article_data["url"] in existing_urls:
                    continue
                
                if article_data["content_hash"] in existing_hashes:
                    continue
                
                raw_article = RawArticle(
                    source_id=source_id,
                    title=article_data["title"][:512],
                    url=article_data["url"],
                    published_at=article_data["published_at"],
                    author=article_data["author"][:255] if article_data["author"] else None,
                    content=article_data["content"],
                    content_hash=article_data["content_hash"],
                    fetched_at=fetched_at,
                    raw_metadata=article_data["raw_metadata"],
                )
                db.add(raw_article)
                
                existing_urls.add(article_data["url"])
                existing_hashes.add(article_data["content_hash"])
                articles_created += 1
                
            except Exception:
                continue
        
        source.last_crawled_at = fetched_at
        db.add(source)
        
        crawl_log.status = "success"
        crawl_log.articles_found = articles_found
        crawl_log.articles_created = articles_created
        crawl_log.finished_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return CrawlResult(
            success=True,
            articles_found=articles_found,
            articles_created=articles_created,
            log_metadata={"feed_title": feed.feed.get("title") if feed.feed else None},
        )
        
    except Exception as e:
        error_msg = str(e)
        
        crawl_log.status = "failed"
        crawl_log.error_message = error_msg
        crawl_log.finished_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return CrawlResult(
            success=False,
            articles_found=0,
            articles_created=0,
            error_message=error_msg,
        )
