from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from reactpy.backend.fastapi import configure

from app.config import settings
from app.database import init_models
from app.routers import backtest, health, signals
from app.ui import Dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):

    if settings.ENVIRONMENT == "development":
        await init_models()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(signals.router)
app.include_router(backtest.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

configure(app, Dashboard)
