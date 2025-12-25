# 测试 API 代理配置

## 验证中间件是否工作

### 1. 启动服务

```bash
# 终端 1: 启动 Django
cd easy-dataset-django
python manage.py runserver 0.0.0.0:8000

# 终端 2: 启动 Next.js
pnpm dev
```

### 2. 测试 API 请求

打开浏览器开发者工具（F12），在 Console 中执行：

```javascript
// 测试 GET 请求
fetch('/api/projects')
  .then(r => r.json())
  .then(data => console.log('Django 响应:', data))
  .catch(err => console.error('错误:', err));
```

### 3. 检查网络请求

在浏览器开发者工具的 Network 标签中：
- 查看 `/api/projects` 请求
- 检查 Request Headers，应该看到请求被发送到 Next.js
- 检查 Response，应该看到 Django 返回的数据

### 4. 验证中间件日志

在 Next.js 的终端输出中，如果看到 "Django API 代理错误"，说明中间件在工作，但可能无法连接到 Django。

### 5. 直接测试 Django

```bash
# 在浏览器或使用 curl
curl http://127.0.0.1:8000/api/projects/
```

应该能看到 Django 返回的 JSON 数据。

## 常见问题排查

### 问题：请求仍然被 Node.js API 路由处理

**原因**：中间件可能没有正确加载

**解决方法**：
1. 确保 `middleware.js` 文件在项目根目录
2. 重启 Next.js 开发服务器
3. 检查 Next.js 启动日志，看是否有中间件相关的错误

### 问题：看到 "无法连接到 Django 后端" 错误

**原因**：Django 后端没有运行或地址不正确

**解决方法**：
1. 确认 Django 运行在 `http://127.0.0.1:8000`
2. 测试直接访问：`http://127.0.0.1:8000/api/projects/`
3. 检查 `middleware.js` 中的 `djangoApiBase` 地址

### 问题：CORS 错误

**原因**：Django 的 CORS 配置不正确

**解决方法**：
1. 检查 Django 的 `settings.py` 中 `CORS_ALLOW_ALL_ORIGINS = True`
2. 确认 `corsheaders` 中间件已添加
3. 中间件已经设置了 CORS 头部，但可能需要 Django 也设置

## 调试技巧

### 1. 添加日志

在 `middleware.js` 中添加：

```javascript
console.log('拦截请求:', request.nextUrl.pathname);
console.log('转发到:', djangoUrl.toString());
```

### 2. 检查请求头

在浏览器 Network 标签中查看请求的详细信息。

### 3. 测试不同的 API 端点

```javascript
// 测试不同的端点
fetch('/api/projects')
fetch('/api/projects/123')
fetch('/api/projects/123/files')
```

