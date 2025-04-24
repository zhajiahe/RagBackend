from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, UploadFile, Query, File

from langconnect.models import DocumentResponse, SearchQuery, SearchResult
from langconnect.database import (
    get_pgvector_collection_details,
    add_documents_to_vectorstore,
    list_documents_in_vectorstore,
    delete_documents_from_vectorstore,
    search_documents_in_vectorstore,
)
from langconnect.services import process_document

router = APIRouter(tags=["documents"])


@router.post("/collections/{collection_id}/documents", response_model=Dict[str, Any])
async def documents_create(
    collection_id: str,
    file: UploadFile = File(...),
):
    """Processes and indexes (adds) a new document file to the specified collection."""
    try:
        collection = await get_pgvector_collection_details(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking collection: {str(e)}"
        )

    try:
        langchain_docs = await process_document(file)
        if not langchain_docs:
            raise HTTPException(
                status_code=400,
                detail="Failed to process document or document is empty",
            )

        added_ids = await add_documents_to_vectorstore(collection_id, langchain_docs)
        if not added_ids:
            raise HTTPException(
                status_code=500, detail="Failed to add document(s) to vector store"
            )

        return {
            "success": True,
            "message": f"{len(added_ids)} document chunk(s) added.",
            "ids": added_ids,
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        print(f"Error processing/adding document: {exc}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process or add document: {str(exc)}"
        )


@router.get(
    "/collections/{collection_id}/documents", response_model=List[DocumentResponse]
)
async def documents_list(
    collection_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Lists documents within a specific collection. NOTE: Uses placeholder implementation."""
    try:
        collection = await get_pgvector_collection_details(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking collection: {str(e)}"
        )

    documents = await list_documents_in_vectorstore(
        collection_id, limit=limit, offset=offset
    )
    return documents


@router.delete(
    "/collections/{collection_id}/documents/{document_id}",
    response_model=Dict[str, bool],
)
async def documents_delete(
    collection_id: str,
    document_id: str,
):
    """Deletes a specific document (chunk) from a collection by its vector store ID."""
    try:
        collection = await get_pgvector_collection_details(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking collection: {str(e)}"
        )

    success = await delete_documents_from_vectorstore(
        collection_id, document_ids=[document_id]
    )
    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to delete document from vector store"
        )

    return {"success": True}


@router.post(
    "/collections/{collection_id}/documents/search", response_model=List[SearchResult]
)
async def documents_search(
    collection_id: str,
    search_query: SearchQuery,
):
    """Performs semantic search for documents within a specific collection."""
    try:
        collection = await get_pgvector_collection_details(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking collection: {str(e)}"
        )

    if not search_query.query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    results = await search_documents_in_vectorstore(
        collection_id,
        query=search_query.query,
        limit=search_query.limit or 10,
    )
    return results
