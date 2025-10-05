from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserOut
from ..dependencies import role_checker

router = APIRouter()

@router.get("/admin/dashboard")
def admin_dashboard(current_user: User = Depends(role_checker(["admin"]))):
    return {"message": f"Welcome to admin dashboard, {current_user.username}!"}

@router.get("/admin/users", response_model=list[UserOut])
def list_users(current_user: User = Depends(role_checker(["admin"])), db: Session = Depends(get_db)):
    return db.query(User).all()
