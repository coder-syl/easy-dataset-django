# API测试指南

## 启动服务器

```bash
cd easy-dataset-django
python manage.py runserver 8000
```

## 测试接口

### 1. 获取项目列表
```bash
curl -X GET http://localhost:8000/api/projects/ \
  -H "Content-Type: application/json"
```

**预期响应**:
```json
{
  "code": 200,
  "message": "Success",
  "data": []
}
```

### 2. 创建项目
```bash
curl -X POST http://localhost:8000/api/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试项目",
    "description": "这是一个测试项目"
  }'
```

**预期响应**:
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "id": "...",
    "name": "测试项目",
    "description": "这是一个测试项目",
    ...
  }
}
```

### 3. 获取项目详情
```bash
curl -X GET http://localhost:8000/api/projects/{project_id}/ \
  -H "Content-Type: application/json"
```

### 4. 更新项目
```bash
curl -X PUT http://localhost:8000/api/projects/{project_id}/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新后的项目名称",
    "description": "更新后的描述"
  }'
```

### 5. 删除项目
```bash
curl -X DELETE http://localhost:8000/api/projects/{project_id}/ \
  -H "Content-Type: application/json"
```

## Swagger文档

访问 http://localhost:8000/swagger/ 查看API文档

## 测试脚本

可以使用Postman、Insomnia或curl进行测试。

