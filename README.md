[简体中文](./README_zh.md)

# RagBackend

RagBackend is a RAG (Retrieval-Augmented Generation) service built with FastAPI and LangChain, improved from [LangConnect](https://github.com/langchain-ai/langconnect). It provides a REST API for managing collections and documents, with PostgreSQL and pgvector for vector storage.

## TODO

- [x] Modify Supabase authentication to implement local FastAPI JWT authentication.
- [x] Use the free `silicon-flow` embedding API by default.
- [x] Add local object storage with MinIO.
- [x] Replace `PGVector` with `langchain_postgres.AsyncPGVectorStore`.
- [ ] Support image encoding/retrieval.
- [ ] Optimize document processing implementation to improve parsing effectiveness.

## Features

- FastAPI-based REST API
- PostgreSQL with pgvector for document storage and vector embeddings
- Docker support for easy deployment

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11 or higher

### Running with Docker

1. Clone the repository:
   ```bash
   # Replace with your repository URL
   git clone https://github.com/zhajiahe/RagBackend.git
   cd RagBackend
   ```

2. Start the services:
   ```bash
   docker-compose up -d
   ```

   This will:
   - Start a PostgreSQL database with pgvector extension
   - Build and start the RagBackend API service

3. Access the API:
   - API documentation: http://localhost:8080/docs
   - Health check: http://localhost:8080/health
   - MinIO Console (for file management): http://localhost:9001 (admin/minioadmin123)

### Development

To run the services in development mode with live reload:

```bash
docker-compose up
```

## Silicon Flow Configuration

This project now supports the free Silicon Flow embedding API as the default option. To use Silicon Flow:

1. Visit [Silicon Flow](https://siliconflow.cn/) and create an account
2. Get your API key from the dashboard
3. Set the environment variables:
   ```bash
   export SILICONFLOW_API_KEY=your_api_key_here
   # Optional: customize model (default is BAAI/bge-m3)
   export SILICONFLOW_MODEL=BAAI/bge-large-zh-v1.5
   ```

**Available Models:**
- `BAAI/bge-m3` - Multi-language, supports 100+ languages, up to 8192 tokens (default)
- `BAAI/bge-large-zh-v1.5` - Optimized for Chinese text
- `BAAI/bge-large-en-v1.5` - Optimized for English text

**Free Tier Benefits:**
- Free embedding API usage
- High-quality vectors with competitive performance
- Support for multiple languages and long texts

## API Documentation

The API documentation is available at http://localhost:8080/docs when the service is running.

## Environment Variables

The following environment variables can be configured in the `docker-compose.yml` file:

| Variable | Description | Default |
|----------|-------------|---------|
| POSTGRES_HOST | PostgreSQL host | postgres |
| POSTGRES_PORT | PostgreSQL port | 5432 |
| POSTGRES_USER | PostgreSQL username | postgres |
| POSTGRES_PASSWORD | PostgreSQL password | postgres |
| POSTGRES_DB | PostgreSQL database name | postgres |
| SILICONFLOW_API_KEY | Silicon Flow API key for embeddings | "" |
| SILICONFLOW_BASE_URL | Silicon Flow API base URL | https://api.siliconflow.cn/v1 |
| SILICONFLOW_MODEL | Silicon Flow embedding model | BAAI/bge-m3 |
| MINIO_ENDPOINT | MinIO server endpoint | localhost:9000 |
| MINIO_ACCESS_KEY | MinIO access key | minioadmin |
| MINIO_SECRET_KEY | MinIO secret key | minioadmin123 |
| MINIO_SECURE | Use HTTPS for MinIO connection | false |
| MINIO_BUCKET_NAME | MinIO bucket name for file storage | ragbackend-documents |

## License

This project is licensed under the terms of the license included in the repository.

## Endpoints

### Collections

#### `/collections` (GET)

List all collections.

#### `/collections` (POST)

Create a new collection.

#### `/collections/{collection_id}` (GET)

Get a specific collection by ID.

#### `/collections/{collection_id}` (DELETE)

Delete a specific collection by ID.

### Documents

#### `/collections/{collection_id}/documents` (GET)

List all documents in a specific collection.

#### `/collections/{collection_id}/documents` (POST)

Create a new document in a specific collection.

#### `/collections/{collection_id}/documents/{document_id}` (DELETE)

Delete a specific document by ID.

#### `/collections/{collection_id}/documents/search` (POST)

Search for documents using semantic search.

### File Management

#### `/files/collections/{collection_id}/files` (GET)

List all files in a specific collection.

#### `/files/user/files` (GET)

List all files for the authenticated user.

#### `/files/collections/{collection_id}/files/stats` (GET)

Get file statistics for a collection.

#### `/files/user/files/stats` (GET)

Get file statistics for the authenticated user.

#### `/files/{file_id}/info` (GET)

Get detailed information about a specific file.

#### `/files/{file_id}/download` (GET)

Download a file from MinIO storage.

#### `/files/{file_id}/download-url` (GET)

Generate a presigned download URL for a file.

#### `/files/{file_id}` (DELETE)

Delete a file and all associated documents.
