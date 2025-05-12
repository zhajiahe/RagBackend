import logging
from datetime import UTC, datetime

from langconnect.auth import AuthenticatedUser
from langconnect.database.connection import get_vectorstore

logger = logging.getLogger(__name__)


async def initialize_database(user: AuthenticatedUser) -> None:
    """Initialize the database by creating necessary extensions and tables."""
    logger.info("Starting database initialization...")

    metadata = {
        # Pass user identity to the collection metadata when creating the default collection
        "owner_id": user.identity,
        # Write current time in ISO-8601 formatted style to created_at
        "created_at": datetime.now(UTC).isoformat(),
    }

    get_vectorstore(collection_metadata=metadata)
    logger.info("Database initialization complete.")
