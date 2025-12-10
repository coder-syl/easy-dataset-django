# Django 迁移执行计划

## 📋 项目信息

- **源项目**: Node.js (Next.js + Prisma + SQLite)
- **目标项目**: Django (Django REST Framework + Django ORM + PostgreSQL)
- **数据库**: PostgreSQL
  - Host: localhost
  - Port: 5432
  - User: postgre
  - Password: 123456
- **接口总数**: 89个
- **代码复用**: apps文件夹中的Django代码

## 🎯 迁移目标

1. ✅ 保持所有89个API接口功能完整
2. ✅ 数据库从SQLite迁移到PostgreSQL
3. ✅ 最大化复用apps中的代码（80%+）
4. ✅ 保持API接口兼容性（前端无需修改）

## 📅 迁移时间表

| 阶段 | 时间 | 任务 | 状态 |
|------|------|------|------|
| 阶段1 | 1-2天 | 项目初始化和环境配置 | 进行中 |
| 阶段2 | 2-3天 | 数据库模型迁移 | 待开始 |
| 阶段3 | 1天 | 复用apps核心模块 | 待开始 |
| 阶段4 | 5-7天 | API路由迁移（高优先级） | 待开始 |
| 阶段5 | 3-4天 | API路由迁移（中低优先级） | 待开始 |
| 阶段6 | 2-3天 | 服务层和业务逻辑迁移 | 待开始 |
| 阶段7 | 1-2天 | 任务系统配置（Celery） | 待开始 |
| 阶段8 | 2-3天 | 测试和验证 | 待开始 |
| **总计** | **17-25天** | - | - |

## 🔧 技术栈

### Django 配置
- Django 4.2+
- Django REST Framework 3.14+
- drf-yasg (Swagger文档)
- django-cors-headers (跨域)
- django-celery-beat (定时任务)
- psycopg2 (PostgreSQL驱动)

### 复用模块
- `apps/common/` → `common/` (100%复用)
- `apps/common/handle/` → `files/handlers/` (100%复用)
- `apps/setting/models_provider/` → `llm/providers/` (100%复用)
- `apps/common/util/split_model.py` → `common/util/split_model.py` (100%复用)
- `apps/common/response/` → `common/response/` (100%复用)

## 📐 项目结构

```
easy-dataset-django/
├── manage.py
├── easy_dataset/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── projects/          # 项目管理
├── files/            # 文件管理（复用apps/common/handle/）
├── chunks/           # 文本块管理
├── questions/        # 问题管理
├── datasets/         # 数据集管理
├── conversations/    # 多轮对话
├── images/           # 图像管理
├── image_datasets/   # 图像数据集
├── llm/              # LLM模块（复用apps/setting/models_provider/）
├── tags/             # 标签管理
├── distill/          # 数据蒸馏
├── tasks/             # 任务管理
├── common/            # 公共模块（复用apps/common/）
│
├── requirements.txt
├── .env
└── README.md
```

## 🔄 迁移步骤详解

### 阶段1：项目初始化和环境配置

**任务清单**：
- [x] 分析API接口（已完成）
- [ ] 创建Django项目
- [ ] 配置PostgreSQL数据库
- [ ] 配置Django设置
- [ ] 安装依赖包
- [ ] 配置CORS和中间件

### 阶段2：数据库模型迁移

**任务清单**：
- [ ] 转换Prisma Schema到Django Models
- [ ] 创建所有15个模型
- [ ] 配置模型关系
- [ ] 创建数据库迁移
- [ ] 执行迁移到PostgreSQL

**模型列表**：
1. Projects
2. UploadFiles
3. Chunks
4. Tags
5. Questions
6. Datasets
7. DatasetConversations
8. LlmProviders
9. LlmModels
10. ModelConfig
11. Task
12. CustomPrompts
13. GaPairs
14. Images
15. ImageDatasets
16. QuestionTemplates

### 阶段3：复用apps核心模块

**任务清单**：
- [ ] 复制common模块
- [ ] 复制文件处理模块
- [ ] 复制LLM提供商模块
- [ ] 适配导入路径
- [ ] 测试核心功能

### 阶段4：API路由迁移（高优先级）

**优先级排序**：
1. 项目管理 API (8个接口)
2. 文件管理 API (4个接口)
3. 文本分割 API (10个接口)
4. 问题管理 API (9个接口)
5. 数据集 API (10个接口)
6. LLM相关 API (9个接口)

### 阶段5：API路由迁移（中低优先级）

1. 多轮对话 API (4个接口)
2. 图像数据集 API (12个接口)
3. 标签管理 API (4个接口)
4. 数据蒸馏 API (5个接口)
5. 任务管理 API (5个接口)
6. 其他 API (6个接口)

### 阶段6：服务层迁移

**任务清单**：
- [ ] 迁移文件处理服务
- [ ] 迁移问题生成服务
- [ ] 迁移数据集生成服务
- [ ] 迁移多轮对话服务
- [ ] 迁移图像处理服务

### 阶段7：任务系统配置

**任务清单**：
- [ ] 配置Celery
- [ ] 迁移异步任务处理
- [ ] 配置任务队列
- [ ] 测试任务执行

### 阶段8：测试和验证

**任务清单**：
- [ ] 单元测试
- [ ] 集成测试
- [ ] API兼容性测试
- [ ] 性能测试
- [ ] 文档更新

## 📝 接口迁移映射表

### 高优先级接口（前30个）

| Node.js路径 | Django路径 | 方法 | 优先级 |
|------------|-----------|------|--------|
| `/api/projects` | `projects/views.py::ProjectView` | GET, POST | P0 |
| `/api/projects/{id}` | `projects/views.py::ProjectDetailView` | GET, PUT, DELETE | P0 |
| `/api/projects/{id}/files` | `files/views.py::FileView` | GET, POST, DELETE | P0 |
| `/api/projects/{id}/split` | `chunks/views.py::SplitView` | POST, GET | P0 |
| `/api/projects/{id}/chunks` | `chunks/views.py::ChunkView` | GET, POST | P0 |
| `/api/projects/{id}/questions` | `questions/views.py::QuestionView` | GET, POST | P0 |
| `/api/projects/{id}/datasets` | `datasets/views.py::DatasetView` | GET, POST | P0 |
| `/api/projects/{id}/model-config` | `llm/views.py::ModelConfigView` | GET, POST | P0 |
| `/api/llm/providers` | `llm/views.py::ProviderView` | GET | P0 |
| `/api/llm/model` | `llm/views.py::ModelView` | GET, POST | P0 |

## ✅ 验证标准

### 功能验证
- [ ] 所有89个API接口正常工作
- [ ] 数据库操作正常
- [ ] 文件上传和处理正常
- [ ] LLM调用正常
- [ ] 任务系统正常

### 性能验证
- [ ] API响应时间 < 500ms（简单请求）
- [ ] 文件处理性能不低于Node.js版本
- [ ] 数据库查询性能正常

### 兼容性验证
- [ ] 前端无需修改即可使用
- [ ] API响应格式保持一致
- [ ] 错误处理保持一致

---

**创建时间**: 2025年1月
**状态**: 进行中

