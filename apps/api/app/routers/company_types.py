from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.tables import CompanyType
from slugify import slugify

router = APIRouter(tags=["company-types"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CompanyTypeCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class CompanyTypeUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None


class CompanyTypeResponse(BaseModel):
    id: int
    name: str
    slug: str
    enabled: bool

    class Config:
        from_attributes = True


@router.get("/company-types", response_model=list[CompanyTypeResponse])
def list_company_types(
    enabled: bool | None = None,
    db: Session = Depends(get_db),
):
    query = select(CompanyType).order_by(CompanyType.created_at.desc())
    if enabled is not None:
        query = query.where(CompanyType.enabled == enabled)
    types = db.execute(query).scalars().all()
    return types


@router.get("/company-types/{type_id}", response_model=CompanyTypeResponse)
def get_company_type(type_id: int, db: Session = Depends(get_db)):
    type_obj = db.execute(select(CompanyType).where(CompanyType.id == type_id)).scalar_one_or_none()
    if not type_obj:
        raise HTTPException(status_code=404, detail="Company type not found")
    return type_obj


@router.post("/company-types", response_model=CompanyTypeResponse)
def create_company_type(data: CompanyTypeCreate, db: Session = Depends(get_db)):
    existing = db.execute(select(CompanyType).where(CompanyType.name == data.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Company type with this name already exists")

    slug = slugify(data.name)
    existing_slug = db.execute(select(CompanyType).where(CompanyType.slug == slug)).scalar_one_or_none()
    if existing_slug:
        slug = f"{slug}-{data.name.lower().replace(' ', '-')}"

    type_obj = CompanyType(
        name=data.name,
        slug=slug,
        enabled=True,
    )
    db.add(type_obj)
    db.commit()
    db.refresh(type_obj)
    return type_obj


@router.put("/company-types/{type_id}", response_model=CompanyTypeResponse)
def update_company_type(type_id: int, data: CompanyTypeUpdate, db: Session = Depends(get_db)):
    type_obj = db.execute(select(CompanyType).where(CompanyType.id == type_id)).scalar_one_or_none()
    if not type_obj:
        raise HTTPException(status_code=404, detail="Company type not found")

    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing = db.execute(
            select(CompanyType).where(CompanyType.name == update_data["name"], CompanyType.id != type_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Company type with this name already exists")
        type_obj.name = update_data["name"]
        type_obj.slug = slugify(update_data["name"])

    if "enabled" in update_data:
        type_obj.enabled = update_data["enabled"]

    db.commit()
    db.refresh(type_obj)
    return type_obj


@router.delete("/company-types/{type_id}")
def delete_company_type(type_id: int, db: Session = Depends(get_db)):
    type_obj = db.execute(select(CompanyType).where(CompanyType.id == type_id)).scalar_one_or_none()
    if not type_obj:
        raise HTTPException(status_code=404, detail="Company type not found")

    db.delete(type_obj)
    db.commit()
    return {"message": "Company type deleted successfully"}
