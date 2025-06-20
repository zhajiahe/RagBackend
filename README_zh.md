[English](./README.md)

# RagBackend (中文)

RagBackend 是一个基于 FastAPI 和 LangChain 构建的 RAG (Retrieval-Augmented Generation) 服务，它在 [LangConnect](https://github.com/langchain-ai/langconnect) 的基础上进行了改进。它提供了一个用于管理集合和文档的 REST API，并使用 PostgreSQL 和 pgvector 进行向量存储。

## TODO

- [x] 修改 Supabase 认证，实现本地基于 FastAPI 的 JWT 认证。
- [ ] 默认使用免费的硅基流动（silicon-flow）向量 API。
- [ ] 增加本地对象存储 MinIO。
- [x] 使用 `langchain_postgres.PGVectorStore` 替代 `PGVector`。
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

### 开发模式

要在开发模式下运行服务并启用实时重新加载：

```bash
docker-compose up
```

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