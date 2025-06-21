[简体中文](./README_zh.md)

# RagBackend

RagBackend is a RAG (Retrieval-Augmented Generation) service built with FastAPI and LangChain, improved from [LangConnect](https://github.com/langchain-ai/langconnect). It provides a REST API for managing collections and documents, with PostgreSQL and pgvector for vector storage.

## TODO

- [x] Modify Supabase authentication to implement local FastAPI JWT authentication.
- [x] Use the free `silicon-flow` embedding API by default.
- [x] Add local object storage with MinIO.
- [x] Replace `PGVector` with `langchain_postgres.PGVectorStore`.
- [ ] Support image encoding/retrieval.
- [ ] Optimize document processing implementation to improve parsing effectiveness.

## Features

- FastAPI-based REST API
- PostgreSQL with pgvector for document storage and vector embeddings
- Docker support for easy deployment
- JWT-based authentication system
- File storage with MinIO integration
- Multi-format document processing (TXT, PDF, MD, DOCX, etc.)
- Semantic search with vector similarity
- Real-time document indexing and retrieval

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

## Algorithm Processing Logic

### Document Processing Pipeline

1. **File Upload & Validation**
   - Validates file format and size constraints
   - Stores original files in MinIO object storage
   - Creates metadata records in PostgreSQL

2. **Document Parsing**
   - **Text Files (.txt, .md)**: Direct content extraction
   - **PDF Files**: Text extraction using PyPDF2/pdfplumber
   - **Word Documents (.docx)**: Content extraction with python-docx
   - **HTML Files**: Text extraction with BeautifulSoup
   - **CSV/Excel**: Structured data parsing

3. **Text Chunking Strategy**
   - **Recursive Character Splitter**: Splits text while preserving context
   - **Chunk Size**: Default 1000 characters with 200 character overlap
   - **Smart Splitting**: Attempts to split at sentence boundaries
   - **Metadata Preservation**: Maintains source information and chunk indices

4. **Embedding Generation**
   - **Silicon Flow Integration**: Uses BAAI/bge-m3 model by default
   - **Batch Processing**: Processes multiple chunks efficiently
   - **Error Handling**: Retries failed embeddings with exponential backoff
   - **Vector Dimensions**: 1024-dimensional embeddings

5. **Vector Storage**
   - **PostgreSQL + pgvector**: Stores vectors with metadata
   - **Indexing**: Creates HNSW indices for fast similarity search
   - **Collection-based Organization**: Isolates documents by user collections

### Search Algorithm

1. **Query Processing**
   - **Input Sanitization**: Cleans and validates search queries
   - **Query Embedding**: Converts query to vector using same model
   - **Parameter Validation**: Ensures limit and filter parameters are valid

2. **Similarity Search**
   - **Cosine Similarity**: Default distance metric for vector comparison
   - **HNSW Algorithm**: Hierarchical Navigable Small World for fast approximate search
   - **Top-K Retrieval**: Returns most similar documents based on score threshold

3. **Result Ranking & Filtering**
   - **Score Normalization**: Converts distances to similarity scores (0-1)
   - **Metadata Filtering**: Supports filtering by source, date, etc.
   - **Duplicate Removal**: Eliminates near-duplicate results
   - **Context Preservation**: Maintains chunk context and relationships

### Authentication & Security

1. **JWT Token System**
   - **HS256 Algorithm**: Secure token signing
   - **Token Expiration**: Configurable expiry times (default 1440 minutes)
   - **Refresh Logic**: Automatic token refresh on valid requests

2. **User Management**
   - **Password Hashing**: bcrypt with salt for secure password storage  
   - **User Isolation**: Each user's data is completely isolated
   - **Session Management**: Tracks user login times and activity

3. **Access Control**
   - **Collection-level Permissions**: Users can only access their own collections
   - **File-level Security**: Strict ownership validation for file operations
   - **API Rate Limiting**: Prevents abuse and ensures fair usage

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
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT token expiration time | 1440 |
| SECRET_KEY | JWT signing secret key | your-secret-key |

## License

This project is licensed under the terms of the license included in the repository.

## API Endpoints

### Authentication

#### `POST /auth/register`
Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",  
  "password": "string",
  "full_name": "string"
}
```

**Response:**
```json
{
  "id": "string",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### `POST /auth/login`
Login with username and password.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",  
  "expires_in": 86400
}
```

#### `POST /auth/token`
OAuth2-compatible token endpoint for interactive API docs.

**Form Data:**
- `username`: string
- `password`: string

### Collections

#### `GET /collections`
List all collections for the authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "string",
    "metadata": {}
  }
]
```

#### `POST /collections`
Create a new collection.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "string",
  "metadata": {}
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "string", 
  "metadata": {}
}
```

#### `GET /collections/{collection_id}`
Get a specific collection by ID.

**Headers:** `Authorization: Bearer <token>`

**Path Parameters:**
- `collection_id`: UUID of the collection

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "metadata": {}
}
```

#### `PATCH /collections/{collection_id}`
Update a specific collection.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "string",
  "metadata": {}
}
```

#### `DELETE /collections/{collection_id}`
Delete a specific collection by ID.

**Headers:** `Authorization: Bearer <token>`

**Response:** 204 No Content

### Documents

#### `GET /collections/{collection_id}/documents`
List all documents in a specific collection.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit`: int (1-100, default: 10)
- `offset`: int (default: 0)

**Response:**
```json
[
  {
    "id": "string",
    "content": "string",
    "metadata": {}
  }
]
```

#### `POST /collections/{collection_id}/documents`
Upload and process documents in a collection.

**Headers:** `Authorization: Bearer <token>`

**Form Data:**
- `files`: list of files
- `metadatas_json`: optional JSON string with metadata for each file

**Response:**
```json
{
  "processed_files": 2,
  "added_documents": 5,
  "failed_files": [],
  "message": "Successfully processed documents"
}
```

#### `DELETE /collections/{collection_id}/documents/{document_id}`
Delete a specific document by ID.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true
}
```

#### `POST /collections/{collection_id}/documents/search`
Search for documents using semantic search.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "query": "string",
  "limit": 10
}
```

**Response:**
```json
[
  {
    "id": "string",
    "content": "string", 
    "metadata": {},
    "score": 0.95
  }
]
```

### File Management

#### `GET /files/collections/{collection_id}/files`
List all files in a specific collection.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit`: int (1-100, default: 50)
- `offset`: int (default: 0)

**Response:**
```json
{
  "files": [
    {
      "file_id": "string",
      "collection_id": "uuid",
      "filename": "string",
      "original_filename": "string",
      "content_type": "string",
      "file_size": 1024,
      "object_path": "string",
      "upload_time": "2024-01-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### `GET /files/user/files`
List all files for the authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit`: int (1-100, default: 50)
- `offset`: int (default: 0)

#### `GET /files/collections/{collection_id}/files/stats`
Get file statistics for a collection.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "collection_id": "uuid",
  "file_count": 5
}
```

#### `GET /files/user/files/stats`
Get file statistics for the authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "user_id": "string",
  "total_file_size": 1048576,
  "total_file_size_mb": 1.0
}
```

#### `GET /files/{file_id}/info`
Get detailed information about a specific file.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "file_id": "string",
  "collection_id": "uuid",
  "filename": "string",
  "original_filename": "string",
  "content_type": "string",
  "file_size": 1024,
  "object_path": "string",
  "upload_time": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "minio_info": {
    "size": 1024,
    "etag": "string",
    "last_modified": "2024-01-01T00:00:00Z",
    "content_type": "string"
  }
}
```

#### `GET /files/{file_id}/download`
Download a file from MinIO storage.

**Headers:** `Authorization: Bearer <token>`

**Response:** File download stream

#### `GET /files/{file_id}/download-url`
Generate a presigned download URL for a file.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `expires_hours`: int (1-24, default: 1)

**Response:**
```json
{
  "file_id": "string",
  "filename": "string",
  "download_url": "string",
  "expires_in_hours": 1
}
```

### Health Check

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit_tests/test_api_integration.py

# Run with coverage
pytest tests/ --cov=ragbackend

# Run tests with verbose output
pytest tests/ -v
```

The test suite includes:
- Authentication flow testing
- Collection management testing  
- Document upload and processing testing
- File management testing
- Search functionality testing
- Error handling and edge cases
- Integration tests using real data files from `/datas` directory
