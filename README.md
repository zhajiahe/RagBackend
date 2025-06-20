[简体中文](./README_zh.md)

# RagBackend

RagBackend is a RAG (Retrieval-Augmented Generation) service built with FastAPI and LangChain, improved from [LangConnect](https://github.com/langchain-ai/langconnect). It provides a REST API for managing collections and documents, with PostgreSQL and pgvector for vector storage.

## TODO

- [ ] Modify Supabase authentication to implement local FastAPI JWT authentication.
- [ ] Use the free `silicon-flow` embedding API by default.
- [ ] Add local object storage with MinIO.
- [ ] Replace `PGVector` with `langchain_postgres.PGVectorStore`.

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

### Development

To run the services in development mode with live reload:

```bash
docker-compose up
```

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
