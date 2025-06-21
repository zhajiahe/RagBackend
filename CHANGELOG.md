# 更新日志

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 格式，
本项目使用 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 新增
- Dockerfile 添加国内镜像源配置，包括清华大学 apt 源和 pip 源，提升国内构建速度
- 增加默认admin用户功能，支持通过环境变量配置管理员账户和密码
- 应用启动时自动创建默认admin用户（如果配置了密码且用户不存在）

### 修复
- 修复CollectionsManager类名不一致导致的导入错误
- 修复认证测试中JWT token时区和精度问题
- 修复Docker构建失败问题，优化国内镜像源配置策略，避免502网关错误
- 修复CollectionsManager.setup()调用方式错误导致的应用启动失败

## [0.0.1] - 2025-06-20

### 新增
- 初始项目版本
- FastAPI 后端服务
- JWT 认证系统
- RAG 功能支持
- PostgreSQL 数据库集成
- MinIO 文件存储 