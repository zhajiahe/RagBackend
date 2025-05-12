import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from langconnect.auth import AuthenticatedUser, resolve_user
from langconnect.database.init_db import initialize_database

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/admin/initialize-database", status_code=status.HTTP_200_OK)
async def init_db_endpoint(user: Annotated[AuthenticatedUser, Depends(resolve_user)]):
    """Initializes the database schema.

    Creates required extensions and tables if they don't exist.
    Should only be called once or when schema changes are needed.
    """
    try:
        logger.info("Received request to initialize database.")
        await initialize_database(user)
        return {"message": "Database initialization successful."}
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database initialization failed: {e}",
        )
