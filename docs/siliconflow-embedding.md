# 硅基流动嵌入 API 使用指南

## 概述

本项目现在支持使用硅基流动（Silicon Flow）的免费嵌入 API 来替代 OpenAI 的嵌入服务。硅基流动提供了高质量的中文和多语言嵌入模型，特别适合 RAG（检索增强生成）应用。

## 优势

- **免费使用**：提供免费的嵌入 API 服务
- **高质量**：基于 BAAI 的 BGE 模型系列，性能优异
- **多语言支持**：支持中文、英文和 100+ 种语言
- **长文本处理**：支持最多 8192 个 token 的长文本

## 配置步骤

### 1. 获取 API 密钥

1. 访问 [硅基流动官网](https://siliconflow.cn/)
2. 注册并登录账户
3. 在控制台中创建 API 密钥
4. 复制您的 API 密钥

### 2. 配置环境变量

#### 方式一：使用环境变量

```bash
export SILICONFLOW_API_KEY=your_api_key_here
export SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
export SILICONFLOW_MODEL=BAAI/bge-m3
```

#### 方式二：修改 .env 文件

```ini
# Silicon Flow Configuration
SILICONFLOW_API_KEY=your_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=BAAI/bge-m3
```

#### 方式三：Docker Compose

修改 `docker-compose.yml` 文件：

```yaml
environment:
  SILICONFLOW_API_KEY: your_api_key_here
  SILICONFLOW_BASE_URL: https://api.siliconflow.cn/v1
  SILICONFLOW_MODEL: BAAI/bge-m3
```

## 可用模型

### BAAI/bge-m3（默认推荐）
- **特点**：多语言支持，支持 100+ 种语言
- **上下文长度**：最多 8192 tokens
- **适用场景**：多语言文档、跨语言检索
- **性能**：在多语言场景下表现优异

### BAAI/bge-large-zh-v1.5
- **特点**：专为中文优化
- **向量维度**：1024 维
- **适用场景**：中文文档处理、中文语义搜索
- **性能**：在中文场景下表现卓越

### BAAI/bge-large-en-v1.5
- **特点**：专为英文优化
- **向量维度**：1024 维
- **适用场景**：英文文档处理、英文语义搜索
- **性能**：在英文场景下表现优异

## 使用示例

### 基本使用

```python
from ragbackend.config import get_embeddings

# 获取嵌入模型实例
embeddings = get_embeddings()

# 生成单个文本的嵌入向量
text = "人工智能技术正在快速发展"
vector = embeddings.embed_query(text)
print(f"向量维度: {len(vector)}")

# 批量生成嵌入向量
texts = [
    "人工智能技术正在快速发展",
    "机器学习是人工智能的重要分支",
    "深度学习推动了AI的发展"
]
vectors = embeddings.embed_documents(texts)
print(f"生成了 {len(vectors)} 个向量")
```

### 模型切换

```python
import os

# 切换到中文优化模型
os.environ["SILICONFLOW_MODEL"] = "BAAI/bge-large-zh-v1.5"

# 切换到英文优化模型
os.environ["SILICONFLOW_MODEL"] = "BAAI/bge-large-en-v1.5"

# 重新初始化配置
from ragbackend.config import get_embeddings
embeddings = get_embeddings()
```

## 性能比较

| 模型 | 中文性能 | 英文性能 | 多语言支持 | 长文本处理 | 资源消耗 |
|------|----------|----------|------------|------------|----------|
| BAAI/bge-m3 | 优秀 | 优秀 | 100+ 语言 | 8192 tokens | 中等 |
| BAAI/bge-large-zh-v1.5 | 卓越 | 良好 | 有限 | 标准 | 较低 |
| BAAI/bge-large-en-v1.5 | 良好 | 卓越 | 有限 | 标准 | 较低 |

## 故障排除

### 常见问题

1. **API 密钥错误**
   ```
   检查 SILICONFLOW_API_KEY 是否正确设置
   确保密钥未过期或被禁用
   ```

2. **网络连接问题**
   ```
   确保可以访问 api.siliconflow.cn
   检查防火墙设置
   ```

3. **模型不存在**
   ```
   检查 SILICONFLOW_MODEL 是否为支持的模型名称
   确保模型名称拼写正确
   ```

### 测试配置

运行测试脚本验证配置：

```bash
python test_siliconflow.py
```

### 回退机制

如果硅基流动 API 不可用，系统会自动回退到以下选项：

1. OpenAI API（如果配置了 OPENAI_API_KEY）
2. 本地假嵌入模型（用于测试）

## 最佳实践

1. **模型选择**：
   - 中文为主的项目选择 `BAAI/bge-large-zh-v1.5`
   - 英文为主的项目选择 `BAAI/bge-large-en-v1.5`
   - 多语言项目选择 `BAAI/bge-m3`

2. **性能优化**：
   - 批量处理文本以提高效率
   - 对长文本进行适当分块
   - 缓存常用的嵌入向量

3. **监控**：
   - 监控 API 调用次数和成本
   - 设置错误处理和重试机制
   - 记录关键指标用于优化

## API 限制

- **免费版本**：每月有一定的免费调用额度
- **速率限制**：请求频率有限制，避免过于频繁的调用
- **文本长度**：单次请求的文本长度有限制

## 支持

如果遇到问题，可以：

1. 查看硅基流动官方文档
2. 在项目仓库中提交 Issue
3. 联系硅基流动技术支持 