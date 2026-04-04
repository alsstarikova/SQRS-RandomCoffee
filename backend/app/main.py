from fastapi import FastAPI

from app.api import auth as auth_router
from app.api import profile as profile_router
from app.db import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RandomCoffee Backend")

app.include_router(auth_router.router)
app.include_router(profile_router.router)


@app.get("/")
def health() -> dict:
    return {"status": "ok"}
