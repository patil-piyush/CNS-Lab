from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import pyotp

from ..database import get_db
from ..models import User
from ..schemas import Token, OTPVerify
from ..auth import create_access_token, verify_password
from ..dependencies import get_user_by_username

router = APIRouter()

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    if user.mfa_enabled:
        raise HTTPException(status_code=206, detail="MFA required for this account. Call /verify-otp with the OTP.")

    access_token = create_access_token(data={"sub": str(user.id), "username": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/verify-otp", response_model=Token)
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    user = get_user_by_username(db, data.username)
    if not user or not user.mfa_enabled or not user.totp_secret:
        raise HTTPException(status_code=400, detail="MFA not enabled for this user")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(data.otp, valid_window=1):
        raise HTTPException(status_code=401, detail="Invalid OTP")

    access_token = create_access_token(data={"sub": str(user.id), "username": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}
