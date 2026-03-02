from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import schemmas
import models
from auth import create_access_token, get_current_user
from controllers import user as user_controller
from database import get_db

router = APIRouter(prefix="/users", tags=["users"])

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"


@router.post("/register", response_model=schemmas.UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    phone: str | None = Form(None),
    sex: str | None = Form(None),
    birth_date: str | None = Form(None),
    avatar: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    # Comentario: validar senha minima (4).
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Senha deve ter pelo menos 4 caracteres")

    # Comentario: validar unicidade de username e telefone.
    if db.query(models.User).filter(models.User.username == username).first():
        raise HTTPException(status_code=400, detail="Username ja existe")
    if phone and db.query(models.User).filter(models.User.phone == phone).first():
        raise HTTPException(status_code=400, detail="Telefone ja existe")

    avatar_path: str | None = None
    if avatar:
        if not avatar.content_type or not avatar.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Avatar deve ser uma imagem")
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        file_ext = Path(avatar.filename).suffix.lower() if avatar.filename else ""
        filename = f"{username}_{uuid4().hex}{file_ext}"
        file_path = UPLOADS_DIR / filename
        content = await avatar.read()
        file_path.write_bytes(content)
        avatar_path = f"uploads/{filename}"

    parsed_birth_date = None
    if birth_date:
        try:
            parsed_birth_date = schemmas.date.fromisoformat(birth_date)
        except Exception:
            raise HTTPException(status_code=400, detail="birth_date invalida, use YYYY-MM-DD")

    user_in = schemmas.UserCreate(
        name=name,
        avatar=avatar_path,
        username=username,
        phone=phone,
        sex=sex,
        birth_date=parsed_birth_date,
        password=password,
    )
    return user_controller.create_user(db, user_in)


@router.post("/login", response_model=schemmas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Comentario: login via form-data (Swagger UI).
    user = user_controller.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais invalidas")
    token = create_access_token({"sub": user.id})
    return schemmas.Token(access_token=token)


@router.post("/login-json", response_model=schemmas.Token)
def login_json(payload: schemmas.LoginRequest, db: Session = Depends(get_db)):
    # Comentario: login via JSON para clientes custom.
    user = user_controller.authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais invalidas")
    token = create_access_token({"sub": user.id})
    return schemmas.Token(access_token=token)


@router.get("/me", response_model=schemmas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=schemmas.UserOut)
def update_me(
    user_in: schemmas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return user_controller.update_user(db, current_user, user_in)


@router.post("/me/avatar", response_model=schemmas.UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Comentario: valida tipo do arquivo e salva na pasta uploads.
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    filename = f"{current_user.id}_{uuid4().hex}{file_ext}"
    file_path = UPLOADS_DIR / filename

    content = await file.read()
    file_path.write_bytes(content)

    current_user.avatar = f"uploads/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user_controller.delete_user(db, current_user)
    return None
