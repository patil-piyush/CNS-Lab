from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import pyotp

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserOut
from ..auth import hash_password
from ..dependencies import get_current_user, get_user_by_username

router = APIRouter()

@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first():
        raise HTTPException(status_code=400, detail="Username or email already registered")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role or "user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/mfa/enable")
def enable_mfa(username: str = Body(..., embed=True), db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    secret = pyotp.random_base32()
    user.totp_secret = secret
    user.mfa_enabled = True
    db.add(user)
    db.commit()
    db.refresh(user)

    provisioning_uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Auth-RBAC-MFA-Demo")
    return {"provisioning_uri": provisioning_uri, "note": "Scan this URI with an authenticator app"}

@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user
