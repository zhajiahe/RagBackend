import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ragbackend.api import collections_router, documents_router
from ragbackend.api.auth import router as auth_router
from ragbackend.api.files import router as files_router
from ragbackend.config import ALLOWED_ORIGINS
from ragbackend.database.collections import CollectionsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# Initialize FastAPI app


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for FastAPI application."""
    logger.info("App is starting up. Creating background worker...")
    
    # Initialize MinIO service
    from ragbackend.services import initialize_minio_service
    minio_initialized = await initialize_minio_service()
    if minio_initialized:
        logger.info("MinIO service initialized successfully.")
    else:
        logger.warning("Failed to initialize MinIO service.")
    
    # Setup collections manager
    await CollectionsManager.setup()
    
    # Create users table
    from ragbackend.database.users import create_users_table
    await create_users_table()
    logger.info("Users table created successfully.")
    
    # Create files metadata table
    from ragbackend.database.files import create_files_table
    files_table_created = await create_files_table()
    if files_table_created:
        logger.info("Files metadata table created successfully.")
    else:
        logger.warning("Failed to create files metadata table.")
    
    yield
    logger.info("App is shutting down. Stopping background worker...")


APP = FastAPI(
    title="LangConnect API",
    description="A REST API for a RAG system using FastAPI and LangChain",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
APP.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
APP.include_router(auth_router)
APP.include_router(collections_router)
APP.include_router(documents_router)
APP.include_router(files_router)


@APP.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("ragbackend.server:APP", host="0.0.0.0", port=8080)
