# Django 后端集成指南

## 问题说明

当前配置允许前端（Next.js）在不启动 Node.js API 路由的情况下，直接使用 Django 后端的接口。

## 配置说明

### 1. Next.js 配置

#### 中间件 (`middleware.js`)

已创建中间件来拦截所有 `/api/*` 请求并转发到 Django 后端。中间件的优先级高于 Next.js 的 API 路由，确保请求被正确转发。

**工作原理**：
- 中间件在 API 路由之前执行
- 拦截所有 `/api/*` 请求
- 转发到 Django 后端 `http://127.0.0.1:8000`
- 返回 Django 的响应给前端

#### Next.js 配置 (`next.config.js`)

虽然 `rewrites` 配置存在，但由于 Next.js API 路由优先级更高，实际使用的是中间件来处理转发。

### 2. 端口分配

- **Next.js 前端**: `http://localhost:1717`
- **Django 后端**: `http://127.0.0.1:8000`

## 启动步骤

### 方法 1：使用启动脚本（推荐）

1. **启动 Django 后端**（在 `easy-dataset-django` 目录）：
   ```bash
   cd easy-dataset-django
   python manage.py runserver 0.0.0.0:8000
   ```

2. **启动 Next.js 前端**（在项目根目录）：
   ```bash
   # Windows
   start-dev.bat
   
   # 或手动执行
   pnpm dev
   ```

### 方法 2：手动启动

1. **清理端口冲突**（如果有）：
   ```bash
   # Windows
   fix-port-conflict.bat
   ```

2. **启动 Django**：
   ```bash
   cd easy-dataset-django
   python manage.py runserver 0.0.0.0:8000
   ```

3. **启动 Next.js**：
   ```bash
   pnpm dev
   ```

## 验证

启动后，访问以下地址验证：

- ✅ **前端页面**: `http://localhost:1717/` - 应该显示 Next.js 前端页面
- ✅ **API 代理**: `http://localhost:1717/api/projects` - 应该被代理到 Django 后端
- ✅ **Django 后端**: `http://127.0.0.1:8000/api/projects` - 直接访问 Django API

## 常见问题

### 问题 1: 访问 `http://localhost:1717/` 显示 Django 404

**原因**：
- Django 错误地运行在 1717 端口
- 或者 Next.js 没有正确启动

**解决方法**：
1. 确保 Django 运行在 8000 端口，而不是 1717
2. 运行 `fix-port-conflict.bat` 清理端口冲突
3. 重新启动 Next.js：`pnpm dev`

### 问题 2: 端口被占用

**解决方法**：
```bash
# Windows - 查找占用端口的进程
netstat -ano | findstr :1717
netstat -ano | findstr :8000

# 停止进程（替换 PID 为实际进程 ID）
taskkill /PID <PID> /F
```

### 问题 3: API 请求失败

**检查项**：
1. Django 是否运行在 `http://127.0.0.1:8000`
2. Django 的 CORS 配置是否正确（`CORS_ALLOW_ALL_ORIGINS = True`）
3. 浏览器控制台是否有错误信息

## 工作原理

1. 用户在浏览器访问 `http://localhost:1717/`
2. Next.js 处理页面路由，返回前端页面
3. 前端代码发起 API 请求（如 `/api/projects`）
4. Next.js 的 `rewrites` 将 `/api/*` 请求代理到 `http://127.0.0.1:8000/api/*`
5. Django 处理 API 请求并返回响应
6. Next.js 将响应返回给前端

## 注意事项

- ⚠️ **不要**在 1717 端口运行 Django
- ⚠️ **确保**Django 运行在 8000 端口
- ✅ Next.js 的 `rewrites` 只影响服务器端请求，客户端直接请求不受影响
- ✅ 开发模式下，Next.js 会自动处理热重载

