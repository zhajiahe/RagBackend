# 默认管理员用户

## 概述

系统支持通过环境变量配置默认管理员用户，在应用首次启动时自动创建。

## 环境变量配置

在 `.env` 文件或环境变量中设置以下配置：

```bash
# 默认管理员用户配置
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=your_secure_password
DEFAULT_ADMIN_FULL_NAME=系统管理员
```

## 配置说明

| 环境变量 | 默认值 | 描述 |
|---------|--------|------|
| `DEFAULT_ADMIN_USERNAME` | `admin` | 管理员用户名 |
| `DEFAULT_ADMIN_EMAIL` | `admin@example.com` | 管理员邮箱 |
| `DEFAULT_ADMIN_PASSWORD` | `""` | 管理员密码（必须设置） |
| `DEFAULT_ADMIN_FULL_NAME` | `系统管理员` | 管理员全名 |

## 重要说明

1. **密码必须设置**: 如果 `DEFAULT_ADMIN_PASSWORD` 为空，系统将跳过管理员用户创建
2. **仅创建一次**: 如果用户名或邮箱已存在，系统将跳过创建
3. **安全考虑**: 生产环境中请使用强密码
4. **启动时创建**: 管理员用户在应用启动时自动创建

## 使用流程

1. 设置环境变量中的管理员密码
2. 启动应用
3. 系统会自动创建管理员用户（如果不存在）
4. 使用配置的用户名和密码登录系统

## 示例

```bash
# 设置环境变量
export DEFAULT_ADMIN_PASSWORD="MySecurePassword123!"

# 启动应用
uv run uvicorn ragbackend.server:APP --host 0.0.0.0 --port 8080
```

## 登录

使用配置的管理员账户登录：

```bash
curl -X POST "http://localhost:8080/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "MySecurePassword123!"
  }'
```

## 安全建议

- 在生产环境中使用复杂密码
- 定期更换管理员密码
- 考虑在首次登录后更改默认邮箱和用户名
- 不要在代码中硬编码密码 