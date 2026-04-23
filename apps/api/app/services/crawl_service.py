from datetime import datetime, timezone
from typing import Any, NamedTuple, List, Dict, Optional
import hashlib
import json
import re

import feedparser
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import Source, RawArticle, CrawlLog


class ArticleProcessStatus:
    CREATED = "created"
    SKIPPED_URL_EXISTS = "skipped_url_exists"
    SKIPPED_HASH_EXISTS = "skipped_hash_exists"
    FAILED_PARSE = "failed_parse"
    FAILED_FETCH_URL = "failed_fetch_url"
    FAILED_DB = "failed_db"


class ArticleProcessRecord(NamedTuple):
    index: int
    title: str
    url: str
    status: str
    error_message: Optional[str] = None
    source_content_length: int = 0
    full_content_length: Optional[int] = None
    content_from_url: bool = False
    parse_strategy: str = "unknown"


class CrawlResult(NamedTuple):
    success: bool
    articles_found: int
    articles_created: int
    articles_skipped: int
    articles_failed: int
    error_message: Optional[str] = None
    log_metadata: Optional[Dict[str, Any]] = None
    article_records: Optional[List[Dict[str, Any]]] = None


def build_content_hash(title: str, content: str) -> str:
    content_for_hash = f"{title}|{content}"
    return hashlib.sha256(content_for_hash.encode("utf-8")).hexdigest()


def extract_article_content_from_html(html_content: str, source_url: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    
    for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
        script.decompose()
    
    content_selectors = [
        "article",
        "main",
        "[class*='content']",
        "[class*='article']",
        "[class*='post']",
        "[class*='body']",
        "[id*='content']",
        "[id*='article']",
        "[id*='post']",
    ]
    
    for selector in content_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text(separator="\n", strip=True)
            if len(text) > 500:
                return text
    
    paragraphs = soup.find_all("p")
    if paragraphs:
        content_parts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 100:
                content_parts.append(text)
        if content_parts:
            return "\n\n".join(content_parts)
    
    body = soup.find("body")
    if body:
        text = body.get_text(separator="\n", strip=True)
        if len(text) > 0:
            return text
    
    return ""


def fetch_url_content(url: str) -> Optional[str]:
    if not url or not url.startswith(("http://", "https://")):
        return None
    
    try:
        with httpx.Client(follow_redirects=True, timeout=15.0) as client:
            response = client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            })
            response.raise_for_status()
            return response.text
    except Exception:
        return None


def parse_rss_entry(entry: Any, source_url: str, fetch_full_content: bool = True) -> Dict[str, Any]:
    title = entry.get("title", "Untitled")
    url = entry.get("link") or entry.get("id") or ""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    author = entry.get("author") or entry.get("dc:creator")
    
    rss_content = ""
    if entry.get("summary"):
        rss_content = entry["summary"]
    elif entry.get("content"):
        for content_item in entry["content"]:
            if content_item.get("value"):
                rss_content = content_item["value"]
                break
    
    if hasattr(entry, "description"):
        rss_content = rss_content or entry.description
    
    final_content = rss_content
    content_from_url = False
    fetch_error = None
    
    if fetch_full_content and url and url.startswith(("http://", "https://")):
        html_content = fetch_url_content(url)
        if html_content:
            extracted_content = extract_article_content_from_html(html_content, url)
            if extracted_content and len(extracted_content) > len(rss_content):
                final_content = extracted_content
                content_from_url = True
        else:
            fetch_error = "Failed to fetch article URL"
    
    published_at = None
    if published:
        try:
            published_at = datetime(*published[:6], tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass
    
    content_hash = build_content_hash(title, final_content)
    
    raw_metadata = {
        "source_url": source_url,
        "parse_strategy": "rss",
        "entry_id": entry.get("id"),
        "tags": [tag.get("term") for tag in entry.get("tags", [])] if entry.get("tags") else None,
        "rss_content_length": len(rss_content),
        "final_content_length": len(final_content),
        "content_from_url": content_from_url,
        "fetch_error": fetch_error,
    }
    
    return {
        "title": title,
        "url": url,
        "published_at": published_at,
        "author": author,
        "content": final_content if final_content else None,
        "content_hash": content_hash,
        "raw_metadata": raw_metadata,
        "source_content_length": len(rss_content),
        "full_content_length": len(final_content) if content_from_url else None,
        "content_from_url": content_from_url,
    }


def parse_html_scraper(html_content: str, source_url: str, index: int) -> Dict[str, Any]:
    soup = BeautifulSoup(html_content, "html.parser")
    
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)
    if not title:
        h1_tags = soup.find_all("h1")
        if h1_tags:
            title = h1_tags[0].get_text(strip=True)
    if not title:
        title = f"Article #{index + 1} from {source_url}"
    
    url = source_url
    
    author = ""
    author_meta = soup.find("meta", {"name": ["author", "article:author"]})
    if author_meta and author_meta.get("content"):
        author = author_meta.get("content", "")
    if not author:
        author_meta = soup.find("meta", {"property": ["article:author", "og:article:author"]})
        if author_meta and author_meta.get("content"):
            author = author_meta.get("content", "")
    
    published_at = None
    published_meta = soup.find("meta", {"name": ["article:published_time", "date", "pubdate"]})
    if not published_meta:
        published_meta = soup.find("meta", {"property": ["article:published_time", "og:article:published_time", "date", "pubdate"]})
    if published_meta and published_meta.get("content"):
        try:
            published_str = published_meta.get("content", "")
            from dateutil import parser as date_parser
            published_at = date_parser.isoparse(published_str)
        except Exception:
            pass
    
    content = extract_article_content_from_html(html_content, source_url)
    
    content_hash = build_content_hash(title, content)
    
    raw_metadata = {
        "source_url": source_url,
        "parse_strategy": "html",
        "article_index": index,
        "content_length": len(content),
    }
    
    return {
        "title": title[:512],
        "url": url,
        "published_at": published_at,
        "author": author[:255] if author else None,
        "content": content if content else None,
        "content_hash": content_hash,
        "raw_metadata": raw_metadata,
        "source_content_length": len(content),
        "full_content_length": len(content),
        "content_from_url": True,
    }


def parse_json_api_item(item: Dict[str, Any], source_url: str, index: int) -> Dict[str, Any]:
    title = item.get("title", "") or item.get("name", "") or item.get("headline", "") or f"Item #{index + 1}"
    
    url = item.get("url", "") or item.get("link", "") or item.get("permalink", "") or source_url
    
    author = item.get("author", "") or item.get("creator", "") or item.get("writer", "")
    if isinstance(author, dict):
        author = author.get("name", "")
    
    published_at = None
    published_fields = ["published_at", "date", "created_at", "publish_date", "timestamp", "published", "updated_at", "modified_at"]
    for field in published_fields:
        if item.get(field):
            try:
                from dateutil import parser as date_parser
                published_at = date_parser.isoparse(str(item[field]))
                break
            except Exception:
                continue
    
    content = item.get("content", "") or item.get("body", "") or item.get("description", "") or item.get("summary", "") or item.get("text", "") or item.get("excerpt", "")
    if isinstance(content, dict):
        content = json.dumps(content, ensure_ascii=False)
    elif not isinstance(content, str):
        content = str(content)
    
    content_from_url = False
    final_content = content
    
    if url and url.startswith(("http://", "https://")) and len(content) < 500:
        html_content = fetch_url_content(url)
        if html_content:
            extracted_content = extract_article_content_from_html(html_content, url)
            if extracted_content and len(extracted_content) > len(content):
                final_content = extracted_content
                content_from_url = True
    
    content_hash = build_content_hash(str(title), str(final_content))
    
    raw_metadata = {
        "source_url": source_url,
        "parse_strategy": "json",
        "item_index": index,
        "raw_item": item,
        "json_content_length": len(content),
        "final_content_length": len(final_content),
        "content_from_url": content_from_url,
    }
    
    return {
        "title": str(title)[:512],
        "url": str(url),
        "published_at": published_at,
        "author": str(author)[:255] if author else None,
        "content": str(final_content) if final_content else None,
        "content_hash": content_hash,
        "raw_metadata": raw_metadata,
        "source_content_length": len(content),
        "full_content_length": len(final_content) if content_from_url else None,
        "content_from_url": content_from_url,
    }


def parse_custom_script(output: str, source_url: str) -> List[Dict[str, Any]]:
    articles = []
    
    try:
        parsed = json.loads(output)
        
        if isinstance(parsed, list):
            for index, item in enumerate(parsed):
                if isinstance(item, dict):
                    article = parse_json_api_item(item, source_url, index)
                    if article.get("raw_metadata"):
                        article["raw_metadata"]["parse_strategy"] = "custom"
                    articles.append(article)
        
        elif isinstance(parsed, dict):
            if "articles" in parsed and isinstance(parsed["articles"], list):
                for index, item in enumerate(parsed["articles"]):
                    if isinstance(item, dict):
                        article = parse_json_api_item(item, source_url, index)
                        if article.get("raw_metadata"):
                            article["raw_metadata"]["parse_strategy"] = "custom"
                        articles.append(article)
            elif "items" in parsed and isinstance(parsed["items"], list):
                for index, item in enumerate(parsed["items"]):
                    if isinstance(item, dict):
                        article = parse_json_api_item(item, source_url, index)
                        if article.get("raw_metadata"):
                            article["raw_metadata"]["parse_strategy"] = "custom"
                        articles.append(article)
            else:
                article = parse_json_api_item(parsed, source_url, 0)
                if article.get("raw_metadata"):
                    article["raw_metadata"]["parse_strategy"] = "custom"
                articles.append(article)
                
    except json.JSONDecodeError:
        lines = output.strip().split("\n")
        for index, line in enumerate(lines):
            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    article = parse_json_api_item(item, source_url, index)
                    if article.get("raw_metadata"):
                        article["raw_metadata"]["parse_strategy"] = "custom"
                    articles.append(article)
            except json.JSONDecodeError:
                continue
    
    return articles


def fetch_rss_feed(url: str) -> feedparser.FeedParserDict:
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return feedparser.parse(response.content)


def fetch_html_page(url: str) -> str:
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        response.raise_for_status()
        return response.text


def fetch_json_api(url: str) -> Dict[str, Any] | List[Any]:
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json"
        })
        response.raise_for_status()
        return response.json()


def process_articles_with_records(
    db: Session,
    source_id: int,
    articles_data: List[Dict[str, Any]],
    fetched_at: datetime,
    strategy: str
) -> tuple[int, int, int, int, List[Dict[str, Any]]]:
    articles_found = len(articles_data)
    articles_created = 0
    articles_skipped = 0
    articles_failed = 0
    article_records: List[Dict[str, Any]] = []
    
    if articles_found == 0:
        return articles_found, articles_created, articles_skipped, articles_failed, article_records
    
    urls = [article["url"] for article in articles_data]
    existing_records = db.execute(
        select(RawArticle.url, RawArticle.content_hash)
        .where(RawArticle.url.in_(urls))
    ).all()
    existing_urls = {r[0] for r in existing_records}
    existing_hashes = {r[1] for r in existing_records}
    
    for index, article_data in enumerate(articles_data):
        record = {
            "index": index,
            "title": article_data.get("title", "")[:100],
            "url": article_data.get("url", ""),
            "status": "",
            "error_message": None,
            "source_content_length": article_data.get("source_content_length", 0),
            "full_content_length": article_data.get("full_content_length"),
            "content_from_url": article_data.get("content_from_url", False),
            "parse_strategy": strategy,
        }
        
        try:
            url = article_data.get("url", "")
            content_hash = article_data.get("content_hash", "")
            
            if url in existing_urls:
                record["status"] = ArticleProcessStatus.SKIPPED_URL_EXISTS
                articles_skipped += 1
                article_records.append(record)
                continue
            
            if content_hash in existing_hashes:
                record["status"] = ArticleProcessStatus.SKIPPED_HASH_EXISTS
                articles_skipped += 1
                article_records.append(record)
                continue
            
            raw_article = RawArticle(
                source_id=source_id,
                title=article_data["title"][:512],
                url=url,
                published_at=article_data["published_at"],
                author=article_data["author"][:255] if article_data.get("author") else None,
                content=article_data["content"],
                content_hash=content_hash,
                fetched_at=fetched_at,
                raw_metadata=article_data["raw_metadata"],
            )
            db.add(raw_article)
            
            existing_urls.add(url)
            existing_hashes.add(content_hash)
            articles_created += 1
            record["status"] = ArticleProcessStatus.CREATED
            
        except Exception as e:
            articles_failed += 1
            record["status"] = ArticleProcessStatus.FAILED_DB
            record["error_message"] = str(e)
        
        article_records.append(record)
    
    return articles_found, articles_created, articles_skipped, articles_failed, article_records


def crawl_source_by_strategy(
    db: Session,
    source: Source,
    strategy: str
) -> tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]]:
    log_metadata: Dict[str, Any] = {}
    articles_data: List[Dict[str, Any]] = []
    parse_records: List[Dict[str, Any]] = []
    
    if strategy == "rss":
        feed = fetch_rss_feed(source.url)
        
        if feed.bozo and feed.bozo_exception:
            raise Exception(f"RSS parsing error: {feed.bozo_exception}")
        
        entries = feed.entries or []
        log_metadata["feed_title"] = feed.feed.get("title") if feed.feed else None
        log_metadata["entry_count"] = len(entries)
        
        for index, entry in enumerate(entries):
            record = {
                "index": index,
                "title": entry.get("title", "")[:100],
                "url": entry.get("link", "") or entry.get("id", ""),
                "status": "",
                "error_message": None,
                "parse_strategy": "rss",
            }
            
            try:
                article = parse_rss_entry(entry, source.url, fetch_full_content=True)
                articles_data.append(article)
                record["status"] = "parsed"
                record["source_content_length"] = article.get("source_content_length", 0)
                record["full_content_length"] = article.get("full_content_length")
                record["content_from_url"] = article.get("content_from_url", False)
            except Exception as e:
                record["status"] = ArticleProcessStatus.FAILED_PARSE
                record["error_message"] = str(e)
            
            parse_records.append(record)
                
    elif strategy == "html":
        html_content = fetch_html_page(source.url)
        
        soup = BeautifulSoup(html_content, "html.parser")
        article_tags = soup.find_all("article")
        
        if article_tags:
            log_metadata["article_tags_found"] = len(article_tags)
            for index, article_tag in enumerate(article_tags):
                record = {
                    "index": index,
                    "title": "",
                    "url": "",
                    "status": "",
                    "error_message": None,
                    "parse_strategy": "html",
                }
                
                try:
                    article_html = str(article_tag)
                    
                    link = article_tag.find("a", href=True)
                    article_url = source.url
                    if link:
                        href = link.get("href", "")
                        if href and not href.startswith("#"):
                            if href.startswith("/"):
                                from urllib.parse import urljoin
                                href = urljoin(source.url, href)
                            article_url = href
                    
                    article = parse_html_scraper(article_html, article_url, index)
                    article["url"] = article_url
                    
                    h3 = article_tag.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                    if h3:
                        article["title"] = h3.get_text(strip=True)[:512]
                    
                    articles_data.append(article)
                    record["title"] = article.get("title", "")[:100]
                    record["url"] = article_url
                    record["status"] = "parsed"
                    record["source_content_length"] = article.get("source_content_length", 0)
                except Exception as e:
                    record["status"] = ArticleProcessStatus.FAILED_PARSE
                    record["error_message"] = str(e)
                
                parse_records.append(record)
        else:
            record = {
                "index": 0,
                "title": "",
                "url": source.url,
                "status": "",
                "error_message": None,
                "parse_strategy": "html",
            }
            
            try:
                article = parse_html_scraper(html_content, source.url, 0)
                articles_data.append(article)
                log_metadata["single_page_extracted"] = True
                record["title"] = article.get("title", "")[:100]
                record["status"] = "parsed"
                record["source_content_length"] = article.get("source_content_length", 0)
            except Exception as e:
                record["status"] = ArticleProcessStatus.FAILED_PARSE
                record["error_message"] = str(e)
            
            parse_records.append(record)
            
    elif strategy == "json":
        json_data = fetch_json_api(source.url)
        log_metadata["response_type"] = "list" if isinstance(json_data, list) else "object"
        
        items = []
        if isinstance(json_data, list):
            items = json_data
        elif isinstance(json_data, dict):
            if "articles" in json_data and isinstance(json_data["articles"], list):
                items = json_data["articles"]
            elif "items" in json_data and isinstance(json_data["items"], list):
                items = json_data["items"]
            elif "data" in json_data and isinstance(json_data["data"], list):
                items = json_data["data"]
            elif "posts" in json_data and isinstance(json_data["posts"], list):
                items = json_data["posts"]
            else:
                items = [json_data]
        
        log_metadata["items_count"] = len(items)
        
        for index, item in enumerate(items):
            record = {
                "index": index,
                "title": "",
                "url": "",
                "status": "",
                "error_message": None,
                "parse_strategy": "json",
            }
            
            if isinstance(item, dict):
                try:
                    article = parse_json_api_item(item, source.url, index)
                    articles_data.append(article)
                    record["title"] = article.get("title", "")[:100]
                    record["url"] = article.get("url", "")
                    record["status"] = "parsed"
                    record["source_content_length"] = article.get("source_content_length", 0)
                    record["full_content_length"] = article.get("full_content_length")
                    record["content_from_url"] = article.get("content_from_url", False)
                except Exception as e:
                    record["status"] = ArticleProcessStatus.FAILED_PARSE
                    record["error_message"] = str(e)
            
            parse_records.append(record)
                    
    elif strategy == "custom":
        log_metadata["strategy"] = "custom"
        log_metadata["status"] = "not_implemented_yet"
        log_metadata["message"] = "Custom script execution is not implemented yet. Placeholder for future implementation."
        articles_data = []
        
    else:
        raise ValueError(f"Unknown parse strategy: {strategy}")
    
    return articles_data, log_metadata, parse_records


def crawl_source(db: Session, source_id: int) -> CrawlResult:
    source = db.execute(select(Source).where(Source.id == source_id)).scalar_one_or_none()
    
    if not source:
        return CrawlResult(
            success=False,
            articles_found=0,
            articles_created=0,
            articles_skipped=0,
            articles_failed=0,
            error_message="Source not found",
        )
    
    if not source.enabled:
        return CrawlResult(
            success=False,
            articles_found=0,
            articles_created=0,
            articles_skipped=0,
            articles_failed=0,
            error_message="Source is disabled",
        )
    
    strategy = source.parse_strategy
    valid_strategies = ["rss", "html", "json", "custom"]
    
    if strategy not in valid_strategies:
        return CrawlResult(
            success=False,
            articles_found=0,
            articles_created=0,
            articles_skipped=0,
            articles_failed=0,
            error_message=f"Unsupported parse strategy: {strategy}. Supported strategies: {', '.join(valid_strategies)}",
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
        articles_data, log_metadata, parse_records = crawl_source_by_strategy(db, source, strategy)
        
        fetched_at = datetime.now(timezone.utc)
        (
            articles_found, 
            articles_created, 
            articles_skipped, 
            articles_failed, 
            process_records
        ) = process_articles_with_records(
            db, source_id, articles_data, fetched_at, strategy
        )
        
        source.last_crawled_at = fetched_at
        db.add(source)
        
        log_metadata = log_metadata or {}
        log_metadata["parse_strategy"] = strategy
        log_metadata["articles_skipped"] = articles_skipped
        log_metadata["articles_failed"] = articles_failed
        
        log_metadata["parse_records"] = parse_records
        log_metadata["process_records"] = process_records
        
        parse_failed_count = sum(1 for r in parse_records if r.get("status") == ArticleProcessStatus.FAILED_PARSE)
        db_failed_count = sum(1 for r in process_records if r.get("status") == ArticleProcessStatus.FAILED_DB)
        total_failed = parse_failed_count + db_failed_count
        
        total_articles = len(parse_records)
        consistency_check = {
            "total_found": total_articles,
            "parse_successful": len([r for r in parse_records if r.get("status") == "parsed"]),
            "parse_failed": parse_failed_count,
            "process_created": articles_created,
            "process_skipped": articles_skipped,
            "process_failed": db_failed_count,
            "total_accounted_for": articles_created + articles_skipped + total_failed,
            "consistent": (articles_created + articles_skipped + total_failed) == total_articles,
        }
        log_metadata["consistency_check"] = consistency_check
        
        crawl_log.status = "success"
        crawl_log.articles_found = total_articles
        crawl_log.articles_created = articles_created
        crawl_log.finished_at = datetime.now(timezone.utc)
        crawl_log.log_metadata = log_metadata
        
        db.commit()
        
        all_records = []
        for r in parse_records:
            record_copy = dict(r)
            if record_copy.get("status") == "parsed":
                index = record_copy.get("index", 0)
                if index < len(process_records):
                    record_copy["process_status"] = process_records[index].get("status")
                    record_copy["process_error"] = process_records[index].get("error_message")
            all_records.append(record_copy)
        
        return CrawlResult(
            success=True,
            articles_found=total_articles,
            articles_created=articles_created,
            articles_skipped=articles_skipped,
            articles_failed=total_failed,
            log_metadata=log_metadata,
            article_records=all_records,
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
            articles_skipped=0,
            articles_failed=0,
            error_message=error_msg,
        )
