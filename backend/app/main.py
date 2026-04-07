import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from app.api import auth as auth_router
from app.api import matching as matching_router
from app.api import profile as profile_router
from app.db import Base
from app.db.session import engine, get_db_context
from app.services.matching import MatchingService

logger = logging.getLogger(__name__)


def run_weekly_matching() -> None:
    try:
        with get_db_context() as db:
            service = MatchingService(db=db)
            matches = service.run_matching()
            logger.info("Weekly matching done: %d pairs created", len(matches))
    except Exception as exc:
        logger.error("Weekly matching failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_weekly_matching, "cron", day_of_week="mon", hour=0, minute=0)
    scheduler.start()
    yield
    scheduler.shutdown()


Base.metadata.create_all(bind=engine)

app = FastAPI(title="RandomCoffee Backend", lifespan=lifespan)

app.include_router(auth_router.router)
app.include_router(profile_router.router)
app.include_router(matching_router.router)


@app.get("/")
def health() -> dict:
    return {"status": "ok"}
