"""FastAPI application entrypoint."""

import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import FRONTEND_DIR
from .generator_service import generate_and_save
from .routers import admin, auth, practice, questions, stats, wrong

from database import db


def weekly_refresh():
    conn = db.get_conn()
    try:
        db.init_db(conn)
        for subject, count in (("C++", 50), ("Python", 50)):
            generated = generate_and_save(conn, subject, count)
            db.log_refresh(conn, subject, "weekly", generated)
    finally:
        conn.close()


scheduler = BackgroundScheduler()
scheduler.add_job(weekly_refresh, "interval", weeks=1)
scheduler.start()


@asynccontextmanager
async def lifespan(app):
    db.init_db()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="AI Exam Training System", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth.router, questions.router, practice.router, wrong.router, stats.router, admin.router):
    app.include_router(router)

if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
