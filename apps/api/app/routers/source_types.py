from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.tables import SourceType
from slugify import slugify

router = APIRouter(tags=["source-types"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SourceTypeCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class SourceTypeUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None


class SourceTypeResponse(BaseModel):
    id: int
    name: str
    slug: str
    enabled: bool

    class Config:
        from_attributes = True


@router.get("/source-types", response_model=list[SourceTypeResponse])
def list_source_types(
    enabled: bool | None = None,
    db: Session = Depends(get_db),
):
    query = select(SourceType).order_by(SourceType.created_at.desc())
    if enabled is not None:
        query = query.where(SourceType.enabled == enabled)
    types = db.execute(query).scalars().all()
    return types


@router.get("/source-types/{type_id}", response_model=SourceTypeResponse)
def get_source_type(type_id: int, db: Session = Depends(get_db)):
    type_obj = db.execute(select(SourceType).where(SourceType.id == type_id)).scalar_one_or_none()
    if not type_obj:
        raise HTTPException(status_code=404, detail="Source type not found")
    return type_obj


@router.post("/source-types", response_model=SourceTypeResponse)
def create_source_type(data: SourceTypeCreate, db: Session = Depends(get_db)):
    existing = db.execute(select(SourceType).where(SourceType.name == data.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Source type with this name already exists")

    slug = slugify(data.name)
    existing_slug = db.execute(select(SourceType).where(SourceType.slug == slug)).scalar_one_or_none()
    if existing_slug:
        slug = f"{slug}-{data.name.lower().replace(' ', '-')}"

    type_obj = SourceType(
        name=data.name,
        slug=slug,
        enabled=True,
    )
    db.add(type_obj)
    db.commit()
    db.refresh(type_obj)
    return type_obj


@router.put("/source-types/{type_id}", response_model=SourceTypeResponse)
def update_source_type(type_id: int, data: SourceTypeUpdate, db: Session = Depends(get_db)):
    type_obj = db.execute(select(SourceType).where(SourceType.id == type_id)).scalar_one_or_none()
    if not type_obj:
        raise HTTPException(status_code=404, detail="Source type not found")

    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing = db.execute(
            select(SourceType).where(SourceType.name == update_data["name"], SourceType.id != type_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Source type with this name already exists")
        type_obj.name = update_data["name"]
        type_obj.slug = slugify(update_data["name"])

    if "enabled" in update_data:
        type_obj.enabled = update_data["enabled"]

    db.commit()
    db.refresh(type_obj)
    return type_obj


@router.delete("/source-types/{type_id}")
def delete_source_type(type_id: int, db: Session = Depends(get_db)):
    type_obj = db.execute(select(SourceType).where(SourceType.id == type_id)).scalar_one_or_none()
    if not type_obj:
        raise HTTPException(status_code=404, detail="Source type not found")

    db.delete(type_obj)
    db.commit()
    return {"message": "Source type deleted successfully"}
