from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.tables import Company
from slugify import slugify

router = APIRouter(tags=["companies"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CompanyCreate(BaseModel):
    name: str
    website: str | None = None
    country: str | None = None
    company_type: str
    logo_url: str | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("company_type")
    @classmethod
    def company_type_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Company type cannot be empty")
        return v.strip()


class CompanyUpdate(BaseModel):
    name: str | None = None
    website: str | None = None
    country: str | None = None
    company_type: str | None = None
    logo_url: str | None = None
    description: str | None = None


class CompanyResponse(BaseModel):
    id: int
    name: str
    slug: str
    website: str | None
    country: str | None
    company_type: str
    logo_url: str | None
    description: str | None

    class Config:
        from_attributes = True


@router.get("/companies", response_model=list[CompanyResponse])
def list_companies(db: Session = Depends(get_db)):
    companies = db.execute(select(Company).order_by(Company.created_at.desc())).scalars().all()
    return companies


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.id == company_id)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/companies", response_model=CompanyResponse)
def create_company(data: CompanyCreate, db: Session = Depends(get_db)):
    existing = db.execute(select(Company).where(Company.name == data.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Company with this name already exists")

    slug = slugify(data.name)

    existing_slug = db.execute(select(Company).where(Company.slug == slug)).scalar_one_or_none()
    if existing_slug:
        slug = f"{slug}-{data.name.lower().replace(' ', '-')}"

    company = Company(
        name=data.name,
        slug=slug,
        website=data.website,
        country=data.country,
        company_type=data.company_type,
        logo_url=data.logo_url,
        description=data.description,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.put("/companies/{company_id}", response_model=CompanyResponse)
def update_company(company_id: int, data: CompanyUpdate, db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.id == company_id)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing = db.execute(
            select(Company).where(Company.name == update_data["name"], Company.id != company_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Company with this name already exists")
        company.name = update_data["name"]
        company.slug = slugify(update_data["name"])

    for key, value in update_data.items():
        if key != "name" and hasattr(company, key):
            setattr(company, key, value)

    db.commit()
    db.refresh(company)
    return company


@router.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.id == company_id)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    db.delete(company)
    db.commit()
    return {"message": "Company deleted successfully"}
