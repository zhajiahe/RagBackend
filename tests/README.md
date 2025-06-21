# 测试指南

## 概述

本项目包含两种类型的测试：

1. **单元测试** - 使用Mock测试各个组件
2. **集成测试** - 使用真实API和数据库测试

## 集成测试

### 前提条件

1. **启动服务**
   ```bash
   # 启动数据库和MinIO
   docker-compose up postgres minio -d
   
   # 启动API服务
   docker-compose up api -d
   
   # 或者一次性启动所有服务
   docker-compose up -d
   ```

2. **验证服务状态**
   ```bash
   # 检查API健康状态
   curl http://localhost:8080/health
   
   # 应该返回: {"status":"ok"}
   ```

### 运行集成测试

#### 方法1: 使用bash脚本（推荐）
```bash
./run_integration_tests.sh
```

#### 方法2: 使用Python脚本
```bash
python run_integration_tests.py
```

#### 方法3: 直接使用pytest
```bash
# 设置环境变量
export IS_TESTING=false
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_DB=postgres
export API_BASE_URL=http://localhost:8080

# 运行测试
pytest tests/unit_tests/test_api_integration.py -v -s
```

### 测试覆盖范围

集成测试涵盖以下API端点：

#### 健康检查
- `GET /health` - 服务健康状态

#### 认证API
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- 无效凭证测试

#### 集合管理API
- `POST /collections` - 创建集合
- `GET /collections` - 列出集合
- `GET /collections/{id}` - 获取单个集合
- `DELETE /collections/{id}` - 删除集合

#### 文档管理API
- `POST /collections/{id}/documents` - 上传文档
- 文档处理和存储测试

#### 错误处理
- 未授权访问测试
- 无效令牌测试

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `IS_TESTING` | `false` | 使用真实环境 |
| `POSTGRES_HOST` | `localhost` | PostgreSQL主机 |
| `POSTGRES_PORT` | `5432` | PostgreSQL端口 |
| `POSTGRES_USER` | `postgres` | PostgreSQL用户名 |
| `POSTGRES_PASSWORD` | `postgres` | PostgreSQL密码 |
| `POSTGRES_DB` | `postgres` | PostgreSQL数据库名 |
| `API_BASE_URL` | `http://localhost:8080` | API服务地址 |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO服务地址 |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO访问密钥 |
| `MINIO_SECRET_KEY` | `minioadmin123` | MinIO密钥 |

### 测试日志

- 详细的测试日志会保存到 `logs/api_integration_test.md`
- 日志包含请求/响应详情、断言检查和错误信息
- 使用Markdown格式，便于阅读

### 故障排除

#### 常见问题

1. **API服务连接失败**
   ```
   ❌ 无法连接到API服务器
   ```
   - 检查Docker服务是否启动：`docker-compose ps`
   - 检查端口是否被占用：`lsof -i :8080`

2. **数据库连接失败**
   ```
   ❌ PostgreSQL 连接失败
   ```
   - 检查PostgreSQL容器状态：`docker-compose logs postgres`
   - 确认环境变量配置正确

3. **MinIO连接失败**
   ```
   ❌ MinIO 连接失败
   ```
   - 检查MinIO容器状态：`docker-compose logs minio`
   - 访问MinIO控制台：http://localhost:9001

4. **测试数据冲突**
   - 每个测试使用唯一的用户名和邮箱，避免冲突
   - 如需重置，可重新启动数据库容器

#### 调试模式

启用详细日志：
```bash
pytest tests/unit_tests/test_api_integration.py -v -s --log-cli-level=DEBUG
```

## 单元测试

运行传统的Mock单元测试：
```bash
pytest tests/unit_tests/ -k "not test_api_integration" -v
```

## 持续集成

在CI/CD环境中，建议：
1. 使用Docker Compose启动所有依赖服务
2. 等待服务健康检查通过
3. 运行集成测试
4. 清理测试环境

示例GitHub Actions配置：
```yaml
- name: Start services
  run: docker-compose up -d
  
- name: Wait for services
  run: |
    timeout 60 bash -c 'until curl -f http://localhost:8080/health; do sleep 2; done'
    
- name: Run integration tests
  run: ./run_integration_tests.sh
  
- name: Cleanup
  run: docker-compose down -v
```

## 性能考虑

- 集成测试比单元测试慢，因为涉及真实的网络和数据库操作
- 建议在开发过程中主要使用单元测试，在发布前运行集成测试
- 可以并行运行不同的测试类别以提高效率 