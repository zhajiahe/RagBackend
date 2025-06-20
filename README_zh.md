[English](./README.md)

# RagBackend (中文)

RagBackend 是一个基于 FastAPI 和 LangChain 构建的 RAG (Retrieval-Augmented Generation) 服务，它在 [LangConnect](https://github.com/langchain-ai/langconnect) 的基础上进行了改进。它提供了一个用于管理集合和文档的 REST API，并使用 PostgreSQL 和 pgvector 进行向量存储。

## TODO

- [x] 修改 Supabase 认证，实现本地基于 FastAPI 的 JWT 认证。
- [x] 默认使用免费的硅基流动（silicon-flow）向量 API。
- [x] 增加本地对象存储 MinIO。
- [x] 使用 `langchain_postgres.AsyncPGVectorStore` 替代 `PGVector`。
- [ ] 支持图片编码/检索。
- [ ] 优化文档处理实现，提高解析效果。

## 特性

- 基于 FastAPI 的 REST API
- 使用 PostgreSQL 和 pgvector 进行文档存储和向量嵌入
- 支持 Docker，方便部署

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

## 许可证

该项目根据仓库中包含的许可证条款进行许可。

## API 端点

### 集合 (Collections)

#### `/collections` (GET)

列出所有集合。

#### `/collections` (POST)

创建一个新集合。

#### `/collections/{collection_id}` (GET)

通过 ID 获取特定集合。

#### `/collections/{collection_id}` (DELETE)

通过 ID 删除特定集合。

### 文档 (Documents)

#### `/collections/{collection_id}/documents` (GET)

列出特定集合中的所有文档。

#### `/collections/{collection_id}/documents` (POST)

在特定集合中创建一个新文档。

#### `/collections/{collection_id}/documents/{document_id}` (DELETE)

通过 ID 删除特定文档。

#### `/collections/{collection_id}/documents/search` (POST)

使用语义搜索来搜索文档。

### 文件管理

#### `/files/collections/{collection_id}/files` (GET)

列出指定集合中的所有文件。

#### `/files/user/files` (GET)

列出当前用户的所有文件。

#### `/files/collections/{collection_id}/files/stats` (GET)

获取集合的文件统计信息。

#### `/files/user/files/stats` (GET)

获取当前用户的文件统计信息。

#### `/files/{file_id}/info` (GET)

获取特定文件的详细信息。

#### `/files/{file_id}/download` (GET)

从MinIO存储下载文件。

#### `/files/{file_id}/download-url` (GET)

为文件生成预签名下载URL。

#### `/files/{file_id}` (DELETE)

删除文件及其关联的所有文档。 