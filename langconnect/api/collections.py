from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends

from langchain_postgres.vectorstores import ConnectionOptions

from langconnect.models import CollectionCreate, CollectionUpdate, CollectionResponse
from langconnect.database import (
    get_db_connection,
    create_collection_in_db,
    list_collections_from_db,
    get_collection_from_db,
    update_collection_in_db,
    delete_collection_from_db,
)

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post("", response_model=CollectionResponse)
async def collections_create(
    collection: CollectionCreate,
    connection: ConnectionOptions = Depends(get_db_connection),
):
    """Creates a new collection."""
    result = await create_collection_in_db(collection.dict(), connection)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create collection")
    return result


@router.get("", response_model=List[CollectionResponse])
async def collections_list(connection: ConnectionOptions = Depends(get_db_connection)):
    """Lists all available collections."""
    return await list_collections_from_db(connection)


@router.get("/{collection_id}", response_model=CollectionResponse)
async def collections_get(
    collection_id: str, connection: ConnectionOptions = Depends(get_db_connection)
):
    """Retrieves details of a specific collection."""
    collection = await get_collection_from_db(collection_id, connection)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.put("/{collection_id}", response_model=CollectionResponse)
async def collections_update(
    collection_id: str,
    collection: CollectionUpdate,
    connection: ConnectionOptions = Depends(get_db_connection),
):
    """Updates/replaces an existing collection."""
    # Check if collection exists
    existing = await get_collection_from_db(collection_id, connection)
    if not existing:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Update collection
    result = await update_collection_in_db(
        collection_id, collection.dict(exclude_unset=True), connection
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update collection")
    return result


@router.patch("/{collection_id}", response_model=CollectionResponse)
async def collections_partial_update(
    collection_id: str,
    collection: CollectionUpdate,
    connection: ConnectionOptions = Depends(get_db_connection),
):
    """Partially updates an existing collection."""
    # Check if collection exists
    existing = await get_collection_from_db(collection_id, connection)
    if not existing:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Update only provided fields
    update_data = collection.dict(exclude_unset=True)
    result = await update_collection_in_db(collection_id, update_data, connection)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update collection")
    return result


@router.delete("/{collection_id}", response_model=Dict[str, bool])
async def collections_delete(
    collection_id: str, connection: ConnectionOptions = Depends(get_db_connection)
):
    """Deletes a specific collection."""
    # Check if collection exists
    existing = await get_collection_from_db(collection_id, connection)
    if not existing:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Delete collection
    result = await delete_collection_from_db(collection_id, connection)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to delete collection")
    return {"success": True}
