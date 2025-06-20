import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import StreamingResponse

from ragbackend.auth import AuthenticatedUser, resolve_user
from ragbackend.services.minio_service import get_minio_service
from ragbackend.database.files import (
    get_file_metadata,
    get_files_by_collection,
    get_files_by_user,
    get_file_count_by_collection,
    get_total_file_size_by_user,
    delete_file_metadata
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/collections/{collection_id}/files")
async def list_collection_files(
    user: Annotated[AuthenticatedUser, Depends(resolve_user)],
    collection_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List all files in a specific collection."""
    try:
        files = await get_files_by_collection(
            str(collection_id), 
            user.identity, 
            limit=limit, 
            offset=offset
        )
        
        # Format response
        formatted_files = []
        for file_record in files:
            formatted_file = {
                "file_id": file_record['file_id'],
                "collection_id": str(collection_id),
                "filename": file_record['filename'],
                "original_filename": file_record['original_filename'],
                "content_type": file_record['content_type'],
                "file_size": file_record['file_size'],
                "object_path": file_record['object_path'],
                "upload_time": file_record['upload_time'].isoformat() if file_record['upload_time'] else None,
                "created_at": file_record['created_at'].isoformat() if file_record['created_at'] else None
            }
            formatted_files.append(formatted_file)
        
        return {
            "files": formatted_files,
            "total": len(formatted_files),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing files for collection {collection_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list files")


@router.get("/user/files")
async def list_user_files(
    user: Annotated[AuthenticatedUser, Depends(resolve_user)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List all files for the authenticated user."""
    try:
        files = await get_files_by_user(
            user.identity, 
            limit=limit, 
            offset=offset
        )
        
        # Format response
        formatted_files = []
        for file_record in files:
            formatted_file = {
                "file_id": file_record['file_id'],
                "collection_id": file_record['collection_id'],
                "filename": file_record['filename'],
                "original_filename": file_record['original_filename'],
                "content_type": file_record['content_type'],
                "file_size": file_record['file_size'],
                "object_path": file_record['object_path'],
                "upload_time": file_record['upload_time'].isoformat() if file_record['upload_time'] else None,
                "created_at": file_record['created_at'].isoformat() if file_record['created_at'] else None
            }
            formatted_files.append(formatted_file)
        
        return {
            "files": formatted_files,
            "total": len(formatted_files),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing files for user {user.identity}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list files")


@router.get("/collections/{collection_id}/files/stats")
async def get_collection_file_stats(
    user: Annotated[AuthenticatedUser, Depends(resolve_user)],
    collection_id: UUID,
):
    """Get file statistics for a collection."""
    try:
        file_count = await get_file_count_by_collection(str(collection_id), user.identity)
        
        return {
            "collection_id": str(collection_id),
            "file_count": file_count
        }
        
    except Exception as e:
        logger.error(f"Error getting stats for collection {collection_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file statistics")


@router.get("/user/files/stats")
async def get_user_file_stats(
    user: Annotated[AuthenticatedUser, Depends(resolve_user)],
):
    """Get file statistics for the authenticated user."""
    try:
        total_size = await get_total_file_size_by_user(user.identity)
        
        return {
            "user_id": user.identity,
            "total_file_size": total_size,
            "total_file_size_mb": round(total_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting stats for user {user.identity}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file statistics")


@router.get("/{file_id}/info")
async def get_file_info(
    user: Annotated[AuthenticatedUser, Depends(resolve_user)],
    file_id: str,
):
    """Get detailed information about a specific file."""
    try:
        file_metadata = await get_file_metadata(file_id)
        
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if user owns this file
        if file_metadata['user_id'] != user.identity:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get MinIO file info
        minio_service = get_minio_service()
        minio_info = await minio_service.get_file_info(file_metadata['object_path'])
        
        response = {
            "file_id": file_metadata['file_id'],
            "collection_id": file_metadata['collection_id'],
            "filename": file_metadata['filename'],
            "original_filename": file_metadata['original_filename'],
            "content_type": file_metadata['content_type'],
            "file_size": file_metadata['file_size'],
            "object_path": file_metadata['object_path'],
            "upload_time": file_metadata['upload_time'].isoformat() if file_metadata['upload_time'] else None,
            "created_at": file_metadata['created_at'].isoformat() if file_metadata['created_at'] else None,
            "updated_at": file_metadata['updated_at'].isoformat() if file_metadata['updated_at'] else None
        }
        
        # Add MinIO information if available
        if minio_info:
            response["minio_info"] = {
                "size": minio_info['size'],
                "etag": minio_info['etag'],
                "last_modified": minio_info['last_modified'],
                "content_type": minio_info['content_type']
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file info for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file information")


@router.get("/{file_id}/download")
async def download_file(
    user: Annotated[AuthenticatedUser, Depends(resolve_user)],
    file_id: str,
):
    """Download a file from MinIO."""
    try:
        file_metadata = await get_file_metadata(file_id)
        
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if user owns this file
        if file_metadata['user_id'] != user.identity:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get file from MinIO
        minio_service = get_minio_service()
        file_stream = await minio_service.download_file(file_metadata['object_path'])
        
        # Return streaming response
        return StreamingResponse(
            file_stream,
            media_type=file_metadata['content_type'] or 'application/octet-stream',
            headers={
                "Content-Disposition": f"attachment; filename=\"{file_metadata['original_filename']}\""
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")


@router.get("/{file_id}/download-url")
async def get_download_url(
    user: Annotated[AuthenticatedUser, Depends(resolve_user)],
    file_id: str,
    expires_hours: int = Query(1, ge=1, le=24),
):
    """Generate a presigned download URL for a file."""
    try:
        file_metadata = await get_file_metadata(file_id)
        
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if user owns this file
        if file_metadata['user_id'] != user.identity:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Generate presigned URL
        from datetime import timedelta
        minio_service = get_minio_service()
        presigned_url = await minio_service.generate_presigned_url(
            file_metadata['object_path'],
            expires=timedelta(hours=expires_hours)
        )
        
        return {
            "file_id": file_id,
            "filename": file_metadata['original_filename'],
            "download_url": presigned_url,
            "expires_in_hours": expires_hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download URL for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate download URL")


@router.delete("/{file_id}")
async def delete_file(
    user: Annotated[AuthenticatedUser, Depends(resolve_user)],
    file_id: str,
):
    """Delete a file and all associated documents."""
    try:
        file_metadata = await get_file_metadata(file_id)
        
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if user owns this file
        if file_metadata['user_id'] != user.identity:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete from MinIO
        minio_service = get_minio_service()
        minio_deleted = await minio_service.delete_file(file_metadata['object_path'])
        
        # Delete file metadata
        metadata_deleted = await delete_file_metadata(file_id)
        
        # TODO: Also delete associated documents from vector store
        # This would require integration with the Collection class
        
        return {
            "success": True,
            "message": f"File {file_metadata['original_filename']} deleted successfully",
            "file_id": file_id,
            "minio_deleted": minio_deleted,
            "metadata_deleted": metadata_deleted
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file") 