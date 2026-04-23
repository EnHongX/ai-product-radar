from datetime import datetime, timezone
from typing import Any, NamedTuple, List, Dict, Optional
import hashlib
import json
import re

import feedparser
import httpx
from bs4 import BeautifulSoup, NavigableString, Tag
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


def extract_article_content_from_html(html_content: str, source_url: str) -> tuple[str, Dict[str, Any]]:
    debug_info = {
        "selectors_tried": [],
        "content_sources": [],
        "final_content_length": 0,
        "final_content_source": None,
    }
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    for unwanted in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "svg"]):
        unwanted.decompose()
    
    content_candidates = []
    
    priority_selectors = [
        ("article.article-content", "article.article-content"),
        ("article.post-content", "article.post-content"),
        ("article .content", "article .content"),
        ("article .entry-content", "article .entry-content"),
        ("article .post-body", "article .post-body"),
        ("article", "article"),
        ("main .content", "main .content"),
        ("main .article-content", "main .article-content"),
        ("main", "main"),
        ("div.article-content", "div.article-content"),
        ("div.post-content", "div.post-content"),
        ("div.content", "div.content"),
        ("div.entry-content", "div.entry-content"),
        ("div.post-body", "div.post-body"),
        ("div#content", "div#content"),
        ("div#article-content", "div#article-content"),
        ("div#post-content", "div#post-content"),
        (".article-content", ".article-content"),
        (".post-content", ".post-content"),
        (".entry-content", ".entry-content"),
        (".post-body", ".post-body"),
        ("[class*='article-content']", "[class*='article-content']"),
        ("[class*='post-content']", "[class*='post-content']"),
        ("[class*='entry-content']", "[class*='entry-content']"),
        ("[id*='article-content']", "[id*='article-content']"),
        ("[id*='post-content']", "[id*='post-content']"),
        ("[id*='entry-content']", "[id*='entry-content']"),
    ]
    
    for selector, desc in priority_selectors:
        debug_info["selectors_tried"].append(desc)
        try:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator="\n", strip=True)
                text_length = len(text)
                if text_length > 200:
                    content_candidates.append({
                        "text": text,
                        "length": text_length,
                        "source": desc,
                        "element_type": element.name,
                    })
                    debug_info["content_sources"].append({
                        "source": desc,
                        "length": text_length,
                    })
        except Exception:
            continue
    
    paragraphs = soup.find_all("p")
    if paragraphs:
        long_paragraphs = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 80:
                long_paragraphs.append(text)
        
        if long_paragraphs:
            combined_text = "\n\n".join(long_paragraphs)
            content_candidates.append({
                "text": combined_text,
                "length": len(combined_text),
                "source": "long_paragraphs",
                "element_type": "p",
            })
            debug_info["content_sources"].append({
                "source": "long_paragraphs",
                "length": len(combined_text),
                "paragraph_count": len(long_paragraphs),
            })
    
    if not content_candidates:
        body = soup.find("body")
        if body:
            text = body.get_text(separator="\n", strip=True)
            if len(text) > 0:
                content_candidates.append({
                    "text": text,
                    "length": len(text),
                    "source": "body",
                    "element_type": "body",
                })
                debug_info["content_sources"].append({
                    "source": "body",
                    "length": len(text),
                })
    
    if content_candidates:
        content_candidates.sort(key=lambda x: x["length"], reverse=True)
        best_candidate = content_candidates[0]
        debug_info["final_content_length"] = best_candidate["length"]
        debug_info["final_content_source"] = best_candidate["source"]
        debug_info["candidates_count"] = len(content_candidates)
        debug_info["all_candidates"] = [
            {"source": c["source"], "length": c["length"]} for c in content_candidates[:5]
        ]
        return best_candidate["text"], debug_info
    
    debug_info["final_content_length"] = 0
    debug_info["final_content_source"] = "none"
    return "", debug_info


def fetch_url_content(url: str) -> Optional[Dict[str, Any]]:
    if not url or not url.startswith(("http://", "https://")):
        return None
    
    try:
        with httpx.Client(follow_redirects=True, timeout=20.0) as client:
            response = client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0",
            })
            response.raise_for_status()
            return {
                "url": url,
                "status_code": response.status_code,
                "content": response.text,
                "content_length": len(response.text),
                "content_type": response.headers.get("content-type", ""),
            }
    except Exception as e:
        return {
            "url": url,
            "status_code": None,
            "content": None,
            "content_length": 0,
            "error": str(e),
        }


def parse_rss_entry(entry: Any, source_url: str, fetch_full_content: bool = True) -> Dict[str, Any]:
    parse_debug = {
        "entry_title": entry.get("title", ""),
        "entry_link": entry.get("link", ""),
        "entry_id": entry.get("id", ""),
        "rss_summary_available": False,
        "rss_content_available": False,
        "rss_description_available": False,
        "rss_summary_length": 0,
        "rss_content_length": 0,
        "rss_description_length": 0,
        "url_fetch_attempted": False,
        "url_fetch_successful": False,
        "url_fetch_error": None,
        "html_extract_debug": None,
        "content_source": "rss",
        "final_content_length": 0,
    }
    
    title = entry.get("title", "Untitled")
    url = entry.get("link") or entry.get("id") or ""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    author = entry.get("author") or entry.get("dc:creator")
    
    rss_summary = ""
    if entry.get("summary"):
        rss_summary = entry["summary"]
        parse_debug["rss_summary_available"] = True
        parse_debug["rss_summary_length"] = len(rss_summary)
    
    rss_content = ""
    if entry.get("content"):
        for content_item in entry["content"]:
            if content_item.get("value"):
                rss_content = content_item["value"]
                parse_debug["rss_content_available"] = True
                parse_debug["rss_content_length"] = len(rss_content)
                break
    
    rss_description = ""
    if hasattr(entry, "description"):
        rss_description = entry.description
        parse_debug["rss_description_available"] = True
        parse_debug["rss_description_length"] = len(rss_description)
    
    rss_combined = ""
    if rss_content:
        rss_combined = rss_content
    elif rss_summary:
        rss_combined = rss_summary
    elif rss_description:
        rss_combined = rss_description
    
    final_content = rss_combined
    content_from_url = False
    
    if fetch_full_content and url and url.startswith(("http://", "https://")):
        parse_debug["url_fetch_attempted"] = True
        
        fetch_result = fetch_url_content(url)
        if fetch_result and fetch_result.get("content"):
            parse_debug["url_fetch_successful"] = True
            parse_debug["url_fetch_content_length"] = fetch_result.get("content_length", 0)
            parse_debug["url_fetch_content_type"] = fetch_result.get("content_type", "")
            
            try:
                extracted_content, extract_debug = extract_article_content_from_html(
                    fetch_result["content"], url
                )
                parse_debug["html_extract_debug"] = extract_debug
                
                if extracted_content:
                    if len(extracted_content) > len(rss_combined):
                        final_content = extracted_content
                        content_from_url = True
                        parse_debug["content_source"] = "url"
                    else:
                        parse_debug["content_source"] = "rss_url_shorter"
                        parse_debug["url_content_length"] = len(extracted_content)
                        parse_debug["rss_content_length_compare"] = len(rss_combined)
                else:
                    parse_debug["content_source"] = "rss_url_empty"
            except Exception as e:
                parse_debug["html_extract_error"] = str(e)
                parse_debug["content_source"] = "rss_url_extract_error"
        else:
            if fetch_result:
                parse_debug["url_fetch_error"] = fetch_result.get("error", "Unknown error")
            parse_debug["content_source"] = "rss_url_failed"
    
    published_at = None
    if published:
        try:
            published_at = datetime(*published[:6], tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass
    
    content_hash = build_content_hash(title, final_content)
    
    parse_debug["final_content_length"] = len(final_content)
    parse_debug["content_from_url"] = content_from_url
    parse_debug["title"] = title
    
    raw_metadata = {
        "source_url": source_url,
        "parse_strategy": "rss",
        "entry_id": entry.get("id"),
        "tags": [tag.get("term") for tag in entry.get("tags", [])] if entry.get("tags") else None,
        "rss_summary_length": len(rss_summary),
        "rss_content_length": len(rss_content),
        "rss_description_length": len(rss_description),
        "final_content_length": len(final_content),
        "content_from_url": content_from_url,
        "content_source": parse_debug["content_source"],
        "parse_debug": parse_debug,
    }
    
    return {
        "title": title,
        "url": url,
        "published_at": published_at,
        "author": author,
        "content": final_content if final_content else None,
        "content_hash": content_hash,
        "raw_metadata": raw_metadata,
        "source_content_length": len(rss_combined),
        "full_content_length": len(final_content) if content_from_url else None,
        "content_from_url": content_from_url,
        "parse_debug": parse_debug,
    }


def parse_html_scraper(html_content: str, source_url: str, index: int) -> Dict[str, Any]:
    parse_debug = {
        "index": index,
        "source_url": source_url,
        "html_content_length": len(html_content),
    }
    
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
    
    parse_debug["title"] = title
    
    url = source_url
    
    author = ""
    author_meta = soup.find("meta", {"name": ["author", "article:author", "og:article:author"]})
    if author_meta and author_meta.get("content"):
        author = author_meta.get("content", "")
    if not author:
        author_meta = soup.find("meta", {"property": ["article:author", "og:article:author"]})
        if author_meta and author_meta.get("content"):
            author = author_meta.get("content", "")
    
    parse_debug["author"] = author
    
    published_at = None
    published_meta = soup.find("meta", {"name": ["article:published_time", "date", "pubdate", "og:pubdate"]})
    if not published_meta:
        published_meta = soup.find("meta", {"property": ["article:published_time", "og:article:published_time", "og:pubdate"]})
    if published_meta and published_meta.get("content"):
        try:
            published_str = published_meta.get("content", "")
            from dateutil import parser as date_parser
            published_at = date_parser.isoparse(published_str)
        except Exception:
            pass
    
    parse_debug["published_at"] = str(published_at) if published_at else None
    
    try:
        content, extract_debug = extract_article_content_from_html(html_content, source_url)
        parse_debug["extract_debug"] = extract_debug
    except Exception as e:
        content = ""
        parse_debug["extract_error"] = str(e)
    
    content_hash = build_content_hash(title, content)
    
    raw_metadata = {
        "source_url": source_url,
        "parse_strategy": "html",
        "article_index": index,
        "content_length": len(content),
        "parse_debug": parse_debug,
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
    parse_debug = {
        "index": index,
        "source_url": source_url,
        "item_fields": list(item.keys()) if isinstance(item, dict) else [],
    }
    
    title = item.get("title", "") or item.get("name", "") or item.get("headline", "") or f"Item #{index + 1}"
    parse_debug["title"] = title
    
    url = item.get("url", "") or item.get("link", "") or item.get("permalink", "") or item.get("html_url", "") or source_url
    parse_debug["url"] = url
    
    author = item.get("author", "") or item.get("creator", "") or item.get("writer", "") or item.get("byline", "")
    if isinstance(author, dict):
        author = author.get("name", "") or str(author)
    parse_debug["author"] = str(author)[:100] if author else None
    
    published_at = None
    published_fields = [
        "published_at", "date", "created_at", "publish_date", "timestamp", "published",
        "updated_at", "modified_at", "pubDate", "publishedDate", "date_published"
    ]
    for field in published_fields:
        if item.get(field):
            try:
                from dateutil import parser as date_parser
                published_at = date_parser.isoparse(str(item[field]))
                parse_debug["published_at_field"] = field
                parse_debug["published_at_value"] = str(item[field])
                break
            except Exception:
                continue
    
    json_content = ""
    content_fields = [
        "content", "body", "description", "summary", "text", "excerpt",
        "full_text", "article_content", "post_content", "html_content"
    ]
    for field in content_fields:
        if item.get(field):
            val = item[field]
            if isinstance(val, dict):
                json_content = json.dumps(val, ensure_ascii=False)
            elif isinstance(val, str):
                json_content = val
            else:
                json_content = str(val)
            if json_content:
                parse_debug["json_content_field"] = field
                parse_debug["json_content_length"] = len(json_content)
                break
    
    final_content = json_content
    content_from_url = False
    
    if url and url.startswith(("http://", "https://")):
        parse_debug["url_fetch_attempted"] = True
        
        fetch_result = fetch_url_content(url)
        if fetch_result and fetch_result.get("content"):
            parse_debug["url_fetch_successful"] = True
            parse_debug["url_fetch_content_length"] = fetch_result.get("content_length", 0)
            
            try:
                extracted_content, extract_debug = extract_article_content_from_html(
                    fetch_result["content"], url
                )
                parse_debug["html_extract_debug"] = extract_debug
                
                if extracted_content and len(extracted_content) > len(json_content):
                    final_content = extracted_content
                    content_from_url = True
                    parse_debug["content_source"] = "url"
                elif extracted_content:
                    parse_debug["content_source"] = "json_url_shorter"
                else:
                    parse_debug["content_source"] = "json_url_empty"
            except Exception as e:
                parse_debug["html_extract_error"] = str(e)
                parse_debug["content_source"] = "json_url_extract_error"
        else:
            if fetch_result:
                parse_debug["url_fetch_error"] = fetch_result.get("error", "Unknown error")
            parse_debug["content_source"] = "json_url_failed"
    else:
        parse_debug["content_source"] = "json_no_url"
    
    parse_debug["final_content_length"] = len(final_content)
    parse_debug["content_from_url"] = content_from_url
    
    content_hash = build_content_hash(str(title), str(final_content))
    
    raw_metadata = {
        "source_url": source_url,
        "parse_strategy": "json",
        "item_index": index,
        "raw_item": item,
        "json_content_length": len(json_content),
        "final_content_length": len(final_content),
        "content_from_url": content_from_url,
        "content_source": parse_debug.get("content_source"),
        "parse_debug": parse_debug,
    }
    
    return {
        "title": str(title)[:512],
        "url": str(url),
        "published_at": published_at,
        "author": str(author)[:255] if author else None,
        "content": str(final_content) if final_content else None,
        "content_hash": content_hash,
        "raw_metadata": raw_metadata,
        "source_content_length": len(json_content),
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
        response = client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml,application/rdf+xml,application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        response.raise_for_status()
        return feedparser.parse(response.content)


def fetch_html_page(url: str) -> str:
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        response.raise_for_status()
        return response.text


def fetch_json_api(url: str) -> Dict[str, Any] | List[Any]:
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json,application/problem+json,*/*;q=0.9",
            "Accept-Language": "en-US,en;q=0.5",
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
            "title": article_data.get("title", "")[:150],
            "url": article_data.get("url", ""),
            "status": "",
            "error_message": None,
            "source_content_length": article_data.get("source_content_length", 0),
            "full_content_length": article_data.get("full_content_length"),
            "content_from_url": article_data.get("content_from_url", False),
            "parse_strategy": strategy,
        }
        
        parse_debug = article_data.get("parse_debug")
        if parse_debug:
            record["content_source"] = parse_debug.get("content_source")
            record["final_content_length"] = parse_debug.get("final_content_length")
        
        try:
            url = article_data.get("url", "")
            content_hash = article_data.get("content_hash", "")
            
            if url in existing_urls:
                record["status"] = ArticleProcessStatus.SKIPPED_URL_EXISTS
                record["reason"] = "URL already exists in database"
                articles_skipped += 1
                article_records.append(record)
                continue
            
            if content_hash in existing_hashes:
                record["status"] = ArticleProcessStatus.SKIPPED_HASH_EXISTS
                record["reason"] = "Content hash already exists in database"
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
            record["error_type"] = type(e).__name__
        
        article_records.append(record)
    
    return articles_found, articles_created, articles_skipped, articles_failed, article_records


def crawl_source_by_strategy(
    db: Session,
    source: Source,
    strategy: str
) -> tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]]:
    log_metadata: Dict[str, Any] = {
        "strategy": strategy,
        "source_id": source.id,
        "source_name": source.name,
        "source_url": source.url,
    }
    articles_data: List[Dict[str, Any]] = []
    parse_records: List[Dict[str, Any]] = []
    
    if strategy == "rss":
        log_metadata["feed_fetch_started"] = datetime.now(timezone.utc).isoformat()
        
        try:
            feed = fetch_rss_feed(source.url)
            log_metadata["feed_fetch_completed"] = datetime.now(timezone.utc).isoformat()
            
            if feed.bozo and feed.bozo_exception:
                log_metadata["feed_bozo_error"] = str(feed.bozo_exception)
            
            entries = feed.entries or []
            log_metadata["feed_title"] = feed.feed.get("title") if feed.feed else None
            log_metadata["feed_subtitle"] = feed.feed.get("subtitle") if feed.feed else None
            log_metadata["entry_count"] = len(entries)
            log_metadata["feed_link"] = feed.feed.get("link") if feed.feed else None
            
            log_metadata["parse_started"] = datetime.now(timezone.utc).isoformat()
            
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
                    
                    parse_debug = article.get("parse_debug")
                    if parse_debug:
                        record["content_source"] = parse_debug.get("content_source")
                        record["final_content_length"] = parse_debug.get("final_content_length")
                        record["url_fetch_attempted"] = parse_debug.get("url_fetch_attempted")
                        record["url_fetch_successful"] = parse_debug.get("url_fetch_successful")
                        
                except Exception as e:
                    record["status"] = ArticleProcessStatus.FAILED_PARSE
                    record["error_message"] = str(e)
                    record["error_type"] = type(e).__name__
                
                parse_records.append(record)
            
            log_metadata["parse_completed"] = datetime.now(timezone.utc).isoformat()
            log_metadata["parsed_count"] = len(articles_data)
            log_metadata["parse_failed_count"] = sum(1 for r in parse_records if r.get("status") == ArticleProcessStatus.FAILED_PARSE)
            
        except Exception as e:
            log_metadata["feed_fetch_error"] = str(e)
            log_metadata["feed_fetch_error_type"] = type(e).__name__
            raise Exception(f"RSS feed fetch/parse error: {e}")
                
    elif strategy == "html":
        log_metadata["html_fetch_started"] = datetime.now(timezone.utc).isoformat()
        
        try:
            html_content = fetch_html_page(source.url)
            log_metadata["html_fetch_completed"] = datetime.now(timezone.utc).isoformat()
            log_metadata["html_content_length"] = len(html_content)
            
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
            
            log_metadata["parsed_count"] = len(articles_data)
            log_metadata["parse_failed_count"] = sum(1 for r in parse_records if r.get("status") == ArticleProcessStatus.FAILED_PARSE)
            
        except Exception as e:
            log_metadata["html_fetch_error"] = str(e)
            raise Exception(f"HTML fetch/parse error: {e}")
            
    elif strategy == "json":
        log_metadata["json_fetch_started"] = datetime.now(timezone.utc).isoformat()
        
        try:
            json_data = fetch_json_api(source.url)
            log_metadata["json_fetch_completed"] = datetime.now(timezone.utc).isoformat()
            log_metadata["response_type"] = "list" if isinstance(json_data, list) else "object"
            
            items = []
            if isinstance(json_data, list):
                items = json_data
            elif isinstance(json_data, dict):
                if "articles" in json_data and isinstance(json_data["articles"], list):
                    items = json_data["articles"]
                    log_metadata["items_source"] = "articles"
                elif "items" in json_data and isinstance(json_data["items"], list):
                    items = json_data["items"]
                    log_metadata["items_source"] = "items"
                elif "data" in json_data and isinstance(json_data["data"], list):
                    items = json_data["data"]
                    log_metadata["items_source"] = "data"
                elif "posts" in json_data and isinstance(json_data["posts"], list):
                    items = json_data["posts"]
                    log_metadata["items_source"] = "posts"
                elif "results" in json_data and isinstance(json_data["results"], list):
                    items = json_data["results"]
                    log_metadata["items_source"] = "results"
                elif "records" in json_data and isinstance(json_data["records"], list):
                    items = json_data["records"]
                    log_metadata["items_source"] = "records"
                else:
                    items = [json_data]
                    log_metadata["items_source"] = "single_object"
            
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
                else:
                    record["status"] = ArticleProcessStatus.FAILED_PARSE
                    record["error_message"] = f"Item is not a dict, type: {type(item).__name__}"
                
                parse_records.append(record)
            
            log_metadata["parsed_count"] = len(articles_data)
            log_metadata["parse_failed_count"] = sum(1 for r in parse_records if r.get("status") == ArticleProcessStatus.FAILED_PARSE)
            
        except Exception as e:
            log_metadata["json_fetch_error"] = str(e)
            raise Exception(f"JSON API fetch/parse error: {e}")
                    
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
        crawl_started_at = datetime.now(timezone.utc)
        
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
        log_metadata["crawl_started_at"] = crawl_started_at.isoformat()
        log_metadata["crawl_completed_at"] = datetime.now(timezone.utc).isoformat()
        
        log_metadata["articles_found"] = articles_found
        log_metadata["articles_created"] = articles_created
        log_metadata["articles_skipped"] = articles_skipped
        log_metadata["articles_failed"] = articles_failed
        
        log_metadata["parse_records"] = parse_records
        log_metadata["process_records"] = process_records
        
        parse_failed_count = sum(1 for r in parse_records if r.get("status") == ArticleProcessStatus.FAILED_PARSE)
        db_failed_count = sum(1 for r in process_records if r.get("status") == ArticleProcessStatus.FAILED_DB)
        skipped_url_count = sum(1 for r in process_records if r.get("status") == ArticleProcessStatus.SKIPPED_URL_EXISTS)
        skipped_hash_count = sum(1 for r in process_records if r.get("status") == ArticleProcessStatus.SKIPPED_HASH_EXISTS)
        total_failed = parse_failed_count + db_failed_count
        
        total_articles = len(parse_records)
        consistency_check = {
            "total_found": total_articles,
            "parse_successful": len([r for r in parse_records if r.get("status") == "parsed"]),
            "parse_failed": parse_failed_count,
            "process_created": articles_created,
            "process_skipped_url": skipped_url_count,
            "process_skipped_hash": skipped_hash_count,
            "process_skipped_total": articles_skipped,
            "process_failed": db_failed_count,
            "total_failed": total_failed,
            "total_accounted_for": articles_created + articles_skipped + total_failed,
            "consistent": (articles_created + articles_skipped + total_failed) == total_articles,
        }
        log_metadata["consistency_check"] = consistency_check
        
        breakdown = {
            "total_articles_found": total_articles,
            "successfully_created": articles_created,
            "skipped_reasons": {
                "url_already_exists": skipped_url_count,
                "content_hash_already_exists": skipped_hash_count,
                "total_skipped": articles_skipped,
            },
            "failed_reasons": {
                "parse_failed": parse_failed_count,
                "database_operation_failed": db_failed_count,
                "total_failed": total_failed,
            },
            "summary": f"Found {total_articles} articles: {articles_created} created, {articles_skipped} skipped ({skipped_url_count} URL exists, {skipped_hash_count} hash exists), {total_failed} failed ({parse_failed_count} parse, {db_failed_count} DB)",
        }
        log_metadata["breakdown"] = breakdown
        
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
                    record_copy["process_reason"] = process_records[index].get("reason")
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
        
        existing_metadata = crawl_log.log_metadata or {}
        existing_metadata["error"] = error_msg
        existing_metadata["error_type"] = type(e).__name__
        crawl_log.log_metadata = existing_metadata
        
        db.commit()
        
        return CrawlResult(
            success=False,
            articles_found=0,
            articles_created=0,
            articles_skipped=0,
            articles_failed=0,
            error_message=error_msg,
        )
