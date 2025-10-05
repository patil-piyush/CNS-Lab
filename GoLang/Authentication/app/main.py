from fastapi import FastAPI
from .database import Base, engine, SessionLocal
from .models import User
from .auth import hash_password
from .routes import users, auth_routes, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth RBAC MFA Demo")

# include routes
app.include_router(users.router, tags=["Users"])
app.include_router(auth_routes.router, tags=["Auth"])
app.include_router(admin.router, tags=["Admin"])

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=hash_password("AdminPass123!"),
                role="admin",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
