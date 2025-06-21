[English](./README.md)

# RagBackend (中文)

RagBackend 是一个基于 FastAPI 和 LangChain 构建的 RAG (Retrieval-Augmented Generation) 服务，它在 [LangConnect](https://github.com/langchain-ai/langconnect) 的基础上进行了改进。它提供了一个用于管理集合和文档的 REST API，并使用 PostgreSQL 和 pgvector 进行向量存储。

## TODO

- [x] 修改 Supabase 认证，实现本地基于 FastAPI 的 JWT 认证。
- [x] 默认使用免费的硅基流动（silicon-flow）向量 API。
- [x] 增加本地对象存储 MinIO。
- [x] 使用 `langchain_postgres.PGVectorStore` 替代 `PGVector`。
- [ ] 支持图片编码/检索。
- [ ] 优化文档处理实现，提高解析效果。

## 特性

- 基于 FastAPI 的 REST API
- 使用 PostgreSQL 和 pgvector 进行文档存储和向量嵌入
- 支持 Docker，方便部署
- 基于 JWT 的身份认证系统
- 与 MinIO 集成的文件存储
- 多格式文档处理（TXT, PDF, MD, DOCX 等）
- 向量相似度语义搜索
- 实时文档索引和检索

## 快速开始

### 环境要求

- Docker 和 Docker Compose
- Python 3.11 或更高版本

### 使用 Docker 运行

1. 克隆仓库:
   ```bash
   # 替换为你的仓库 URL
   git clone https://github.com/zhajiahe/RagBackend.git
   cd RagBackend
   ```

2. 启动服务:
   ```bash
   docker-compose up -d
   ```

   这将：
   - 启动一个带有 pgvector 扩展的 PostgreSQL 数据库
   - 构建并启动 RagBackend API 服务

3. 访问 API:
   - API 文档: http://localhost:8080/docs
   - 健康检查: http://localhost:8080/health
   - MinIO 管理控制台（文件管理）: http://localhost:9001 (minioadmin/minioadmin123)

### 开发模式

要在开发模式下运行服务并启用实时重新加载：

```bash
docker-compose up
```

## 硅基流动配置

本项目现在支持免费的硅基流动嵌入 API 作为默认选项。使用硅基流动：

1. 访问 [硅基流动](https://siliconflow.cn/) 并创建账户
2. 从控制台获取您的 API 密钥
3. 设置环境变量：
   ```bash
   export SILICONFLOW_API_KEY=your_api_key_here
   # 可选：自定义模型（默认为 BAAI/bge-m3）
   export SILICONFLOW_MODEL=BAAI/bge-large-zh-v1.5
   ```

**可用模型：**
- `BAAI/bge-m3` - 多语言支持，支持 100+ 种语言，最多 8192 tokens（默认）
- `BAAI/bge-large-zh-v1.5` - 中文优化
- `BAAI/bge-large-en-v1.5` - 英文优化

**免费版本优势：**
- 免费嵌入 API 使用
- 高质量向量，性能优异
- 支持多语言和长文本

## 算法处理逻辑

### 文档处理管道

1. **文件上传与验证**
   - 验证文件格式和大小限制
   - 将原始文件存储到 MinIO 对象存储
   - 在 PostgreSQL 中创建元数据记录

2. **文档解析**
   - **文本文件 (.txt, .md)**: 直接内容提取
   - **PDF 文件**: 使用 PyPDF2/pdfplumber 进行文本提取
   - **Word 文档 (.docx)**: 使用 python-docx 提取内容
   - **HTML 文件**: 使用 BeautifulSoup 进行文本提取
   - **CSV/Excel**: 结构化数据解析

3. **文本分块策略**
   - **递归字符分割器**: 在保持上下文的同时分割文本
   - **分块大小**: 默认 1000 字符，重叠 200 字符
   - **智能分割**: 尝试在句子边界进行分割
   - **元数据保留**: 维护源信息和分块索引

4. **嵌入向量生成**
   - **硅基流动集成**: 默认使用 BAAI/bge-m3 模型
   - **批处理**: 高效处理多个文本块
   - **错误处理**: 使用指数退避重试失败的嵌入
   - **向量维度**: 1024 维度的嵌入向量

5. **向量存储**
   - **PostgreSQL + pgvector**: 存储向量和元数据
   - **索引**: 为快速相似度搜索创建 HNSW 索引
   - **基于集合的组织**: 按用户集合隔离文档

### 搜索算法

1. **查询处理**
   - **输入清理**: 清理和验证搜索查询
   - **查询嵌入**: 使用相同模型将查询转换为向量
   - **参数验证**: 确保限制和过滤参数有效

2. **相似度搜索**
   - **余弦相似度**: 向量比较的默认距离度量
   - **HNSW 算法**: 用于快速近似搜索的分层可导航小世界
   - **Top-K 检索**: 基于分数阈值返回最相似的文档

3. **结果排序与过滤**
   - **分数归一化**: 将距离转换为相似度分数 (0-1)
   - **元数据过滤**: 支持按来源、日期等过滤
   - **去重**: 消除近似重复结果
   - **上下文保持**: 维护分块上下文和关系

### 身份认证与安全

1. **JWT 令牌系统**
   - **HS256 算法**: 安全的令牌签名
   - **令牌过期**: 可配置的过期时间（默认 1440 分钟）
   - **刷新逻辑**: 在有效请求时自动刷新令牌

2. **用户管理**
   - **密码哈希**: 使用 bcrypt 和盐进行安全密码存储
   - **用户隔离**: 每个用户的数据完全隔离
   - **会话管理**: 跟踪用户登录时间和活动

3. **访问控制**
   - **集合级权限**: 用户只能访问自己的集合
   - **文件级安全**: 严格的文件操作所有权验证  
   - **API 限速**: 防止滥用并确保公平使用

## API 文档

服务运行时，API 文档可在 http://localhost:8080/docs 查看。

## 环境变量

可以在 `docker-compose.yml` 文件中配置以下环境变量:

| 变量 | 描述 | 默认值 |
|----------|-------------|---------|
| POSTGRES_HOST | PostgreSQL 主机 | postgres |
| POSTGRES_PORT | PostgreSQL 端口 | 5432 |
| POSTGRES_USER | PostgreSQL 用户名 | postgres |
| POSTGRES_PASSWORD | PostgreSQL 密码 | postgres |
| POSTGRES_DB | PostgreSQL 数据库名 | postgres |
| SILICONFLOW_API_KEY | 硅基流动 API 密钥（用于嵌入向量） | "" |
| SILICONFLOW_BASE_URL | 硅基流动 API 基础 URL | https://api.siliconflow.cn/v1 |
| SILICONFLOW_MODEL | 硅基流动嵌入模型 | BAAI/bge-m3 |
| MINIO_ENDPOINT | MinIO 服务器端点 | localhost:9000 |
| MINIO_ACCESS_KEY | MinIO 访问密钥 | minioadmin |
| MINIO_SECRET_KEY | MinIO 秘密密钥 | minioadmin123 |
| MINIO_SECURE | MinIO 连接是否使用 HTTPS | false |
| MINIO_BUCKET_NAME | MinIO 文件存储桶名称 | ragbackend-documents |
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT 令牌过期时间 | 1440 |
| SECRET_KEY | JWT 签名密钥 | your-secret-key |

## 许可证

该项目根据仓库中包含的许可证条款进行许可。

## API 端点

### 身份认证

#### `POST /auth/register`
注册新用户账户。

**请求体:**
```json
{
  "username": "string",
  "email": "string",  
  "password": "string",
  "full_name": "string"
}
```

**响应:**
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
使用用户名和密码登录。

**请求体:**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应:**
```json
{
  "access_token": "string",
  "token_type": "bearer",  
  "expires_in": 86400
}
```

#### `POST /auth/token`
OAuth2 兼容的令牌端点，用于交互式 API 文档。

**表单数据:**
- `username`: string
- `password`: string

### 集合 (Collections)

#### `GET /collections`
列出认证用户的所有集合。

**请求头:** `Authorization: Bearer <token>`

**响应:**
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
创建一个新集合。

**请求头:** `Authorization: Bearer <token>`

**请求体:**
```json
{
  "name": "string",
  "metadata": {}
}
```

**响应:**
```json
{
  "id": "uuid",
  "name": "string", 
  "metadata": {}
}
```

#### `GET /collections/{collection_id}`
通过 ID 获取特定集合。

**请求头:** `Authorization: Bearer <token>`

**路径参数:**
- `collection_id`: 集合的 UUID

**响应:**
```json
{
  "id": "uuid",
  "name": "string",
  "metadata": {}
}
```

#### `PATCH /collections/{collection_id}`
更新特定集合。

**请求头:** `Authorization: Bearer <token>`

**请求体:**
```json
{
  "name": "string",
  "metadata": {}
}
```

#### `DELETE /collections/{collection_id}`
通过 ID 删除特定集合。

**请求头:** `Authorization: Bearer <token>`

**响应:** 204 No Content

### 文档 (Documents)

#### `GET /collections/{collection_id}/documents`
列出特定集合中的所有文档。

**请求头:** `Authorization: Bearer <token>`

**查询参数:**
- `limit`: int (1-100, 默认: 10)
- `offset`: int (默认: 0)

**响应:**
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
在集合中上传和处理文档。

**请求头:** `Authorization: Bearer <token>`

**表单数据:**
- `files`: 文件列表
- `metadatas_json`: 可选的 JSON 字符串，包含每个文件的元数据

**响应:**
```json
{
  "processed_files": 2,
  "added_documents": 5,
  "failed_files": [],
  "message": "成功处理文档"
}
```

#### `DELETE /collections/{collection_id}/documents/{document_id}`
通过 ID 删除特定文档。

**请求头:** `Authorization: Bearer <token>`

**响应:**
```json
{
  "success": true
}
```

#### `POST /collections/{collection_id}/documents/search`
使用语义搜索来搜索文档。

**请求头:** `Authorization: Bearer <token>`

**请求体:**
```json
{
  "query": "string",
  "limit": 10
}
```

**响应:**
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

### 文件管理

#### `GET /files/collections/{collection_id}/files`
列出指定集合中的所有文件。

**请求头:** `Authorization: Bearer <token>`

**查询参数:**
- `limit`: int (1-100, 默认: 50)
- `offset`: int (默认: 0)

**响应:**
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
列出当前用户的所有文件。

**请求头:** `Authorization: Bearer <token>`

**查询参数:**
- `limit`: int (1-100, 默认: 50)
- `offset`: int (默认: 0)

#### `GET /files/collections/{collection_id}/files/stats`
获取集合的文件统计信息。

**请求头:** `Authorization: Bearer <token>`

**响应:**
```json
{
  "collection_id": "uuid",
  "file_count": 5
}
```

#### `GET /files/user/files/stats`
获取当前用户的文件统计信息。

**请求头:** `Authorization: Bearer <token>`

**响应:**
```json
{
  "user_id": "string",
  "total_file_size": 1048576,
  "total_file_size_mb": 1.0
}
```

#### `GET /files/{file_id}/info`
获取特定文件的详细信息。

**请求头:** `Authorization: Bearer <token>`

**响应:**
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
从 MinIO 存储下载文件。

**请求头:** `Authorization: Bearer <token>`

**响应:** 文件下载流

#### `GET /files/{file_id}/download-url`
为文件生成预签名下载 URL。

**请求头:** `Authorization: Bearer <token>`

**查询参数:**
- `expires_hours`: int (1-24, 默认: 1)

**响应:**
```json
{
  "file_id": "string",
  "filename": "string",
  "download_url": "string",
  "expires_in_hours": 1
}
```

### 健康检查

#### `GET /health`
健康检查端点。

**响应:**
```json
{
  "status": "ok"
}
```

## 测试

运行完整的测试套件：

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/unit_tests/test_api_integration.py

# 运行带覆盖率的测试
pytest tests/ --cov=ragbackend

# 运行详细输出的测试
pytest tests/ -v
```

测试套件包括：
- 身份认证流程测试
- 集合管理测试
- 文档上传和处理测试
- 文件管理测试
- 搜索功能测试
- 错误处理和边界情况
- 使用 `/datas` 目录中真实数据文件的集成测试 