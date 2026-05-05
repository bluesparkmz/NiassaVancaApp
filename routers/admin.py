from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import models
import schemmas
from auth import get_current_user, get_password_hash
from database import get_db
from routers.companies import (
    _company_out,
    _company_type_value,
    _create_company_profile,
    _ensure_company_profiles_for_type,
    _ensure_unique_slug,
    _slugify,
)


router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role != models.UserRole.ADMIN.value and not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Apenas admin")
    return current_user


def _normalize_username(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value.strip())
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned[:32] or "utilizador"


def _ensure_unique_username(db: Session, username: str) -> str:
    base_username = _normalize_username(username)
    candidate = base_username
    index = 2
    while db.query(models.User).filter(models.User.username == candidate).first():
        candidate = f"{base_username}_{index}"
        index += 1
    return candidate


def _get_or_create_owner_user(
    db: Session,
    email: str,
    full_name: str | None,
    phone: str | None,
    password: str | None,
) -> tuple[models.User, str | None]:
    normalized_email = email.lower().strip()
    user = db.query(models.User).filter(models.User.email == normalized_email).first()
    if user:
        return user, None

    temp_password = password or secrets.token_urlsafe(12)
    username_seed = normalized_email.split("@")[0]

    user = models.User(
        name=(full_name or username_seed).strip(),
        username=_ensure_unique_username(db, username_seed),
        full_name=(full_name or username_seed).strip(),
        email=normalized_email,
        phone=(phone or "").strip() or None,
        password_hash=get_password_hash(temp_password),
        role=models.UserRole.PARTNER,
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.flush()
    return user, (None if password else temp_password)


class AdminOwnerIn(BaseModel):
    email: str = Field(..., max_length=140)
    full_name: str | None = Field(default=None, max_length=140)
    phone: str | None = Field(default=None, max_length=30)
    password: str | None = Field(default=None, min_length=4)


class AdminCreateCompanyIn(BaseModel):
    owner: AdminOwnerIn
    company: schemmas.CompanyCreate


class AdminCreateCompanyOut(BaseModel):
    owner_user: schemmas.UserOut
    company: schemmas.CompanyOut
    owner_temp_password: str | None = None


@router.post("/companies", response_model=AdminCreateCompanyOut, status_code=status.HTTP_201_CREATED)
def admin_create_company(
    payload: AdminCreateCompanyIn,
    db: Session = Depends(get_db),
    _: models.User = Depends(_require_admin),
):
    owner, temp_password = _get_or_create_owner_user(
        db,
        email=str(payload.owner.email),
        full_name=payload.owner.full_name,
        phone=payload.owner.phone,
        password=payload.owner.password,
    )

    company_slug = _ensure_unique_slug(db, _slugify(payload.company.name))
    company = models.Company(
        owner_user_id=owner.id,
        name=payload.company.name.strip(),
        slug=company_slug,
        company_type=_company_type_value(payload.company),
        category=payload.company.category,
        location=payload.company.location.strip(),
        district=payload.company.district,
        description=payload.company.description,
        short_description=payload.company.short_description,
        phone=payload.company.phone.strip(),
        email=str(payload.company.email) if payload.company.email else None,
        whatsapp=payload.company.whatsapp,
        website=payload.company.website,
        instagram=payload.company.instagram,
        facebook=payload.company.facebook,
        logo_url=payload.company.logo_url,
        cover_url=payload.company.cover_url,
        status=models.CompanyStatus.PENDING,
        is_verified=False,
        is_featured=False,
    )
    db.add(company)
    db.flush()

    _create_company_profile(db, company, payload.company)

    db.commit()
    db.refresh(company)
    db.refresh(owner)

    return AdminCreateCompanyOut(
        owner_user=schemmas.UserOut.model_validate(owner),
        company=_company_out(company),
        owner_temp_password=temp_password,
    )


@router.get("/companies", response_model=list[schemmas.CompanyOut])
def admin_list_companies(
    db: Session = Depends(get_db),
    _: models.User = Depends(_require_admin),
):
    companies = db.query(models.Company).all()
    return [_company_out(company) for company in companies]


@router.patch("/companies/{company_id}", response_model=schemmas.CompanyOut)
def admin_update_company(
    company_id: int,
    payload: schemmas.CompanyUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(_require_admin),
):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada")

    data = payload.model_dump(exclude_unset=True)
    new_company_type = data.get("company_type")
    for key, value in data.items():
        setattr(company, key, value)

    if new_company_type is not None:
        company_type_value = new_company_type.value if hasattr(new_company_type, "value") else str(new_company_type)
        _ensure_company_profiles_for_type(db, company, company_type_value)

    db.commit()
    db.refresh(company)
    return _company_out(company)
