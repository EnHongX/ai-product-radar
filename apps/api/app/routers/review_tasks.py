from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.orm import Session, selectinload

from app.db.session import SessionLocal
from app.models.tables import ReviewTask, ProductRelease, RawArticle, Source, Company

router = APIRouter(tags=["review-tasks"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ReviewTaskCompany(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ReviewTaskSource(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ReviewTaskRawArticle(BaseModel):
    id: int
    title: str
    url: str
    content: str | None
    published_at: str | None
    fetched_at: str

    class Config:
        from_attributes = True


class ReviewTaskProductRelease(BaseModel):
    id: int
    release_title: str
    release_url: str
    release_type: str
    summary: str | None
    confidence_score: float | None
    review_status: str
    extraction_payload: dict | None

    class Config:
        from_attributes = True


class ReviewTaskResponse(BaseModel):
    id: int
    raw_article_id: int | None
    product_release_id: int | None
    status: str
    priority: int
    assigned_to: str | None
    reviewer_notes: str | None
    reviewed_at: str | None
    created_at: str
    updated_at: str
    company: ReviewTaskCompany | None
    source: ReviewTaskSource | None
    raw_article: ReviewTaskRawArticle | None
    product_release: ReviewTaskProductRelease | None

    class Config:
        from_attributes = True


class ReviewTaskListResponse(BaseModel):
    id: int
    raw_article_id: int | None
    product_release_id: int | None
    status: str
    priority: int
    reviewed_at: str | None
    created_at: str
    article_title: str | None
    article_url: str | None
    release_title: str | None
    release_url: str | None
    company_name: str | None
    source_name: str | None
    confidence_score: float | None


class ReviewSubmitRequest(BaseModel):
    approved: bool
    notes: str | None = None


class ReviewSubmitResponse(BaseModel):
    success: bool
    message: str
    task_id: int


@router.get("/review-tasks", response_model=list[ReviewTaskListResponse])
def list_review_tasks(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    limit: int = Query(50, ge=1, le=200, description="Number of tasks to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    query = (
        select(ReviewTask)
        .options(
            selectinload(ReviewTask.raw_article).selectinload(RawArticle.source).selectinload(Source.company),
            selectinload(ReviewTask.product_release),
        )
        .order_by(ReviewTask.priority.desc(), ReviewTask.created_at.desc())
    )

    if status is not None:
        query = query.where(ReviewTask.status == status)

    query = query.offset(offset).limit(limit)

    tasks = db.execute(query).scalars().all()

    results: list[ReviewTaskListResponse] = []
    for task in tasks:
        article_title = None
        article_url = None
        release_title = None
        release_url = None
        company_name = None
        source_name = None
        confidence_score = None

        if task.raw_article:
            article_title = task.raw_article.title
            article_url = task.raw_article.url
            if task.raw_article.source:
                source_name = task.raw_article.source.name
                if task.raw_article.source.company:
                    company_name = task.raw_article.source.company.name

        if task.product_release:
            release_title = task.product_release.release_title
            release_url = task.product_release.release_url
            confidence_score = task.product_release.confidence_score

        results.append(
            ReviewTaskListResponse(
                id=task.id,
                raw_article_id=task.raw_article_id,
                product_release_id=task.product_release_id,
                status=task.status,
                priority=task.priority,
                reviewed_at=task.reviewed_at.isoformat() if task.reviewed_at else None,
                created_at=task.created_at.isoformat() if task.created_at else "",
                article_title=article_title,
                article_url=article_url,
                release_title=release_title,
                release_url=release_url,
                company_name=company_name,
                source_name=source_name,
                confidence_score=confidence_score,
            )
        )

    return results


@router.get("/review-tasks/stats")
def get_review_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func

    total = db.execute(select(func.count(ReviewTask.id))).scalar() or 0
    pending = db.execute(select(func.count(ReviewTask.id)).where(ReviewTask.status == "pending")).scalar() or 0
    approved = db.execute(select(func.count(ReviewTask.id)).where(ReviewTask.status == "approved")).scalar() or 0
    rejected = db.execute(select(func.count(ReviewTask.id)).where(ReviewTask.status == "rejected")).scalar() or 0

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
    }


@router.get("/review-tasks/{task_id}", response_model=ReviewTaskResponse)
def get_review_task(task_id: int, db: Session = Depends(get_db)):
    task = db.execute(
        select(ReviewTask)
        .options(
            selectinload(ReviewTask.raw_article).selectinload(RawArticle.source).selectinload(Source.company),
            selectinload(ReviewTask.product_release),
        )
        .where(ReviewTask.id == task_id)
    ).scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Review task not found")

    company = None
    source = None
    raw_article = None
    product_release = None

    if task.raw_article:
        if task.raw_article.source:
            source = ReviewTaskSource(
                id=task.raw_article.source.id,
                name=task.raw_article.source.name,
            )
            if task.raw_article.source.company:
                company = ReviewTaskCompany(
                    id=task.raw_article.source.company.id,
                    name=task.raw_article.source.company.name,
                )

        raw_article = ReviewTaskRawArticle(
            id=task.raw_article.id,
            title=task.raw_article.title,
            url=task.raw_article.url,
            content=task.raw_article.content,
            published_at=task.raw_article.published_at.isoformat() if task.raw_article.published_at else None,
            fetched_at=task.raw_article.fetched_at.isoformat() if task.raw_article.fetched_at else "",
        )

    if task.product_release:
        product_release = ReviewTaskProductRelease(
            id=task.product_release.id,
            release_title=task.product_release.release_title,
            release_url=task.product_release.release_url,
            release_type=task.product_release.release_type,
            summary=task.product_release.summary,
            confidence_score=task.product_release.confidence_score,
            review_status=task.product_release.review_status,
            extraction_payload=task.product_release.extraction_payload,
        )

    return ReviewTaskResponse(
        id=task.id,
        raw_article_id=task.raw_article_id,
        product_release_id=task.product_release_id,
        status=task.status,
        priority=task.priority,
        assigned_to=task.assigned_to,
        reviewer_notes=task.reviewer_notes,
        reviewed_at=task.reviewed_at.isoformat() if task.reviewed_at else None,
        created_at=task.created_at.isoformat() if task.created_at else "",
        updated_at=task.updated_at.isoformat() if task.updated_at else "",
        company=company,
        source=source,
        raw_article=raw_article,
        product_release=product_release,
    )


@router.post("/review-tasks/{task_id}/submit", response_model=ReviewSubmitResponse)
def submit_review(
    task_id: int,
    request: ReviewSubmitRequest,
    db: Session = Depends(get_db),
):
    task = db.execute(
        select(ReviewTask)
        .options(selectinload(ReviewTask.product_release))
        .where(ReviewTask.id == task_id)
    ).scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Review task not found")

    if task.status != "pending":
        raise HTTPException(status_code=400, detail="Task has already been reviewed")

    task.status = "approved" if request.approved else "rejected"
    task.reviewed_at = datetime.utcnow()
    task.reviewer_notes = request.notes

    if task.product_release:
        task.product_release.review_status = "approved" if request.approved else "rejected"

    db.commit()

    return ReviewSubmitResponse(
        success=True,
        message=f"Task {task_id} has been {'approved' if request.approved else 'rejected'}",
        task_id=task_id,
    )
