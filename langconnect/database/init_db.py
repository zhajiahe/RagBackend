import logging
from langconnect.database.connection import get_vectorstore

logger = logging.getLogger(__name__)


async def initialize_database():
    """Initialize the database by creating necessary extensions and tables."""
    logger.info("Starting database initialization...")

    store = get_vectorstore()
    # Create collection if it doesn't exist
    store.create_collection()
    # Create tables if they don't exist
    store.create_tables_if_not_exists()
    logger.info("Document vector store tables created or already exist.")

    logger.info("Database initialization complete.")
