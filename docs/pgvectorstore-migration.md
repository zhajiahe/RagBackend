# PGVectorStore Migration Guide

## Overview

This project has been upgraded from the deprecated `PGVector` to the new `PGVectorStore` implementation in langchain-postgres v0.0.14+.

## Key Changes

### 1. Database Driver
- **Before**: Used `psycopg2` with connection strings like `postgresql+psycopg2://...`
- **After**: Uses `psycopg3` with connection strings like `postgresql+psycopg://...`

### 2. API Changes
- **Before**: `from langchain_postgres.vectorstores import PGVector`
- **After**: `from langchain_postgres import PGVectorStore`
- **New**: `from langchain_postgres import PGEngine`

### 3. Initialization Pattern
- **Before**: Direct instantiation with connection parameters
```python
store = PGVector(
    embeddings=embeddings,
    collection_name=collection_name,
    connection=engine,
    use_jsonb=True,
    collection_metadata=collection_metadata,
)
```

- **After**: Uses `PGEngine` for connection management and `create_sync()` method
```python
engine = PGEngine.from_connection_string(url=connection_string)
engine.init_vectorstore_table(table_name=collection_name, vector_size=vector_size)
store = PGVectorStore.create_sync(
    engine=engine,
    table_name=collection_name,
    embedding_service=embeddings,
)
```

### 4. Table Schema
- **Before**: Used `langchain_pg_*` table prefixes
- **After**: Uses `vectorstore_*` table prefixes

## Migration Benefits

1. **Improved Performance**: Better handling of user-specified IDs and document operations
2. **Enhanced Schema**: More efficient database schema design
3. **Better Manageability**: Cleaner API and better separation of concerns
4. **Active Maintenance**: The new implementation is actively maintained and receives updates

## Database Schema Changes

The migration updates the following table structures:
- `langchain_pg_collection` → `vectorstore_collection`
- `langchain_pg_embedding` → `vectorstore_embedding`

## Connection String Migration

Update your connection strings:
```bash
# Before
POSTGRES_CONNECTION_STRING="postgresql+psycopg2://user:pass@host:port/db"

# After  
POSTGRES_CONNECTION_STRING="postgresql+psycopg://user:pass@host:port/db"
```

## Code Changes Made

### 1. Updated `ragbackend/database/connection.py`
- Replaced `PGVector` import with `PGVectorStore`
- Added `PGEngine` import
- Updated `get_vectorstore_engine()` to return `PGEngine`
- Modified `get_vectorstore()` to use new initialization pattern

### 2. Updated `ragbackend/database/collections.py`
- Updated SQL queries to use new table names
- Modified collection and document management to work with new schema
- Updated metadata handling for new JSON structure

### 3. Dependencies
- Project already includes `langchain-postgres>=0.0.2` which supports the new API

## Migration Steps

1. **Update Dependencies** (if needed)
   ```bash
   uv add "langchain-postgres>=0.0.14"
   ```

2. **Update Environment Variables**
   ```bash
   # Update connection strings to use psycopg instead of psycopg2
   POSTGRES_CONNECTION_STRING="postgresql+psycopg://user:pass@host:port/db"
   ```

3. **Database Migration**
   The new implementation will create new tables with the `vectorstore_*` prefix. 
   Existing data in `langchain_pg_*` tables will need to be migrated manually if preservation is required.

4. **Code Updates**
   All code changes have been implemented in this migration.

## Verification

After migration, verify the system works by:
1. Starting the application
2. Creating a new collection
3. Adding documents to the collection
4. Performing similarity searches
5. Checking that new tables are created with `vectorstore_*` prefixes

## Rollback Plan

If issues occur, you can rollback by:
1. Reverting the code changes in this commit
2. Restoring the original table schema
3. Updating connection strings back to `psycopg2` format

## References

- [LangChain PGVector Documentation](https://python.langchain.com/docs/integrations/vectorstores/pgvector/)
- [langchain-postgres GitHub Repository](https://github.com/langchain-ai/langchain-postgres)
- [Migration Warning in v0.0.14+](https://python.langchain.com/docs/integrations/vectorstores/pgvector/)
- [DeepWiki langchain-postgres](https://deepwiki.com/langchain-ai/langchain-postgres) 