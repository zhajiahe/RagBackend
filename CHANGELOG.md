# 更新日志

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 格式，
本项目使用 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

## [1.1.0] - 2024-12-19

### 新增
- 新增完整的API集成测试脚本 test_api_integration.py，覆盖所有API端点
- 测试脚本支持使用 datas 目录中的真实数据文件进行测试  
- 完善README.md文档，添加详细的API端点说明和请求/响应格式
- 增加算法处理逻辑的详细说明（文档处理管道、搜索算法、认证安全机制）
- 同步更新中文版README_zh.md，保持文档一致性
- 添加测试运行指南和测试套件说明

### 改进
- 优化API文档结构，提供更清晰的端点分类
- 增强认证和安全机制的说明文档
- 改进环境变量配置说明

### 新增
- Dockerfile 添加国内镜像源配置，包括清华大学 apt 源和 pip 源，提升国内构建速度
- 增加默认admin用户功能，支持通过环境变量配置管理员账户和密码
- 应用启动时自动创建默认admin用户（如果配置了密码且用户不存在）

### 修复
- 修复CollectionsManager类名不一致导致的导入错误
- 修复认证测试中JWT token时区和精度问题
- 修复Docker构建失败问题，优化国内镜像源配置策略，避免502网关错误
- 修复CollectionsManager.setup()调用方式错误导致的应用启动失败
- 修复JWT token创建时UUID对象JSON序列化错误

## [0.0.1] - 2025-06-20

### 新增
- 初始项目版本
- FastAPI 后端服务
- JWT 认证系统
- RAG 功能支持
- PostgreSQL 数据库集成
- MinIO 文件存储 