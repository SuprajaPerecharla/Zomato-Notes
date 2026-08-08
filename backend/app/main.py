"""
Zomato Notes — FastAPI application entry point.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import notes, search, tags
from .services.intelligence import warmup_embedder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Zomato Notes API …")
    init_db()
    logger.info("Database initialised.")
    warmup_embedder()  # load model once in main thread before requests start
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Zomato Notes API",
    description="Internal incident knowledge-base for on-call engineers",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Vite dev server and any configured origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes.router)
app.include_router(search.router)
app.include_router(tags.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": "zomato-notes"}
