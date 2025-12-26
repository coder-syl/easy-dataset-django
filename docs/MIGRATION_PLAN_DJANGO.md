# Node.js 到 Django 后端迁移方案

## 📋 迁移概述

本文档提供将 Easy-Fine-Tunnin 项目的 Node.js 后端迁移到 Django 的完整方案，**最大化复用 apps 文件夹中已有的 Django 代码**。

## 🎯 为什么选择 Django？

### 优势

1. **代码复用率最高**：可以直接使用 apps 中 80%+ 的代码
2. **成熟稳定**：Django 是经过验证的企业级框架
3. **功能完整**：内置 Admin、ORM、认证等
4. **生态丰富**：Django REST Framework、Celery 等成熟插件
5. **团队熟悉**：如果团队熟悉 apps 代码，学习成本低

### 与 FastAPI 对比

| 特性 | Django | FastAPI |
|------|--------|---------|
| 代码复用率 | 80%+ | 30-40% |
| 学习曲线 | 中等（已有参考） | 低 |
| 性能 | 良好 | 优秀 |
| 开发速度 | 快（复用多） | 中等 |
| 生态成熟度 | 非常成熟 | 较新但活跃 |

## 🏗️ 技术栈

### 核心框架

- **Django 4.2+**：Web 框架
- **Django REST Framework (DRF)**：API 框架
- **drf-yasg**：Swagger 文档
- **Django ORM**：数据库操作（替代 Prisma）
- **Celery**：异步任务处理
- **SQLite**：数据库（保持不变）

### 复用 apps 中的模块

| apps 模块 | 用途 | 复用程度 |
|----------|------|---------|
| `common/handle/` | 文件处理 | 100% 复用 |
| `setting/models_provider/` | LLM 提供商 | 100% 复用 |
| `common/util/split_model.py` | 文本分割 | 100% 复用 |
| `common/response/result.py` | 统一响应 | 100% 复用 |
| `common/auth/` | 认证系统 | 90% 复用 |
| `common/cache/` | 缓存机制 | 100% 复用 |

## 📐 项目结构

```
easy-dataset-django/
├── manage.py
├── easy_dataset/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py          # 基础配置（参考 apps/smartdoc/settings/base.py）
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py              # 主路由（参考 apps/smartdoc/urls.py）
│   ├── wsgi.py
│   └── asgi.py
│
├── projects/                # 项目模块（新增）
│   ├── __init__.py
│   ├── models.py            # 项目模型（从 Prisma Schema 转换）
│   ├── serializers.py       # 序列化器（参考 apps/dataset/serializers/）
│   ├── views.py             # 视图（参考 apps/dataset/views/）
│   ├── urls.py
│   └── services.py          # 业务逻辑
│
├── datasets/                # 数据集模块（复用 apps/dataset/）
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py       # 复用 apps/dataset/serializers/
│   ├── views.py             # 复用 apps/dataset/views/
│   └── urls.py
│
├── questions/               # 问题模块（新增）
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── services.py
│
├── files/                   # 文件模块（复用 apps/common/handle/）
│   ├── __init__.py
│   ├── handlers/            # 直接复用 apps/common/handle/
│   │   ├── base_split_handle.py
│   │   └── impl/
│   │       ├── pdf_split_handle.py
│   │       ├── doc_split_handle.py
│   │       └── ...
│   ├── views.py
│   └── urls.py
│
├── llm/                     # LLM 模块（复用 apps/setting/models_provider/）
│   ├── __init__.py
│   ├── providers/           # 直接复用 apps/setting/models_provider/
│   │   ├── base_model_provider.py
│   │   └── impl/
│   │       ├── openai_model_provider/
│   │       ├── ollama_model_provider/
│   │       └── ...
│   ├── views.py
│   └── urls.py
│
├── common/                  # 公共模块（直接复用 apps/common/）
│   ├── __init__.py
│   ├── handle/              # 文件处理（100% 复用）
│   ├── util/                # 工具函数（100% 复用）
│   ├── response/            # 响应格式（100% 复用）
│   ├── auth/                # 认证（90% 复用）
│   └── cache/               # 缓存（100% 复用）
│
├── tasks/                   # 任务模块（新增，使用 Celery）
│   ├── __init__.py
│   ├── celery.py            # Celery 配置
│   └── question_generation.py
│
└── requirements.txt
```

## 🔄 迁移策略

### 阶段 1：项目初始化（1周）

**目标**：搭建 Django 项目骨架，配置基础环境

**任务清单**：
- [ ] 创建 Django 项目
- [ ] 配置 settings（参考 `apps/smartdoc/settings/base.py`）
- [ ] 配置数据库（SQLite）
- [ ] 复制 common 模块（100% 复用）
- [ ] 配置 DRF 和 Swagger

**关键代码**：

```python
# easy_dataset/settings/base.py（参考 apps/smartdoc/settings/base.py）
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_yasg',  # Swagger
    'django_filters',
    'django_celery_beat',
    'corsheaders',
    # 自定义应用
    'projects',
    'datasets',
    'questions',
    'files',
    'llm',
    'common',
    'tasks',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'common.middleware.cross_domain_middleware.CrossDomainMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'common.auth.TokenAuth',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 阶段 2：模型迁移（1-2周）

**目标**：将 Prisma Schema 转换为 Django Models

**任务清单**：
- [ ] 转换 Projects 模型
- [ ] 转换 Chunks 模型
- [ ] 转换 Questions 模型
- [ ] 转换 Datasets 模型
- [ ] 转换其他模型
- [ ] 创建并执行迁移

**关键代码**：

```python
# projects/models.py（从 prisma/schema.prisma 转换）
from django.db import models
from django.utils import timezone

class Project(models.Model):
    id = models.CharField(max_length=12, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    global_prompt = models.TextField(default='')
    question_prompt = models.TextField(default='')
    answer_prompt = models.TextField(default='')
    default_model_config_id = models.CharField(max_length=255, null=True, blank=True)
    create_at = models.DateTimeField(default=timezone.now)
    update_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects'
        ordering = ['-create_at']
    
    def __str__(self):
        return self.name

class Chunk(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='chunks')
    file_id = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    content = models.TextField()
    summary = models.TextField(default='')
    size = models.IntegerField()
    create_at = models.DateTimeField(default=timezone.now)
    update_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chunks'
        indexes = [
            models.Index(fields=['project_id']),
        ]
```

### 阶段 3：复用核心模块（1周）

**目标**：直接复用 apps 中的核心代码

**任务清单**：
- [ ] 复制 `apps/common/` 到项目
- [ ] 复制 `apps/setting/models_provider/` 到 `llm/providers/`
- [ ] 复制 `apps/common/handle/` 到 `files/handlers/`
- [ ] 适配导入路径
- [ ] 测试核心功能

**关键操作**：

```bash
# 1. 复制 common 模块
cp -r apps/common easy-dataset-django/

# 2. 复制文件处理模块
cp -r apps/common/handle easy-dataset-django/files/handlers

# 3. 复制 LLM 提供商模块
cp -r apps/setting/models_provider easy-dataset-django/llm/providers

# 4. 复制工具函数
cp -r apps/common/util easy-dataset-django/common/util
```

### 阶段 4：API 视图迁移（3-4周）

**目标**：迁移所有 API 端点

**迁移顺序**：
1. 项目管理 API
2. 文件上传和处理 API
3. 文本分割 API
4. 问题生成 API
5. 数据集生成 API
6. 其他 API...

**关键代码示例**：

```python
# projects/views.py（对应 app/api/projects/route.js）
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.request import Request
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from common.auth import TokenAuth
from common.response import result
from .serializers import ProjectSerializer, ProjectCreateSerializer
from .models import Project
from django.utils.translation import gettext_lazy as _

class ProjectView(APIView):
    authentication_classes = [TokenAuth]
    
    @action(methods=['POST'], detail=False)
    @swagger_auto_schema(
        operation_summary=_("创建项目"),
        operation_id="create_project",
        request_body=ProjectCreateSerializer,
        responses={201: ProjectSerializer}
    )
    def post(self, request: Request):
        """创建项目（对应 Node.js POST /api/projects）"""
        serializer = ProjectCreateSerializer(data=request.data)
        if serializer.is_valid():
            project = serializer.save()
            return result.success(ProjectSerializer(project).data, status=201)
        return result.error(serializer.errors, code=400)
    
    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(
        operation_summary=_("获取项目列表"),
        operation_id="get_projects",
        responses={200: ProjectSerializer(many=True)}
    )
    def get(self, request: Request):
        """获取项目列表（对应 Node.js GET /api/projects）"""
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        return result.success(serializer.data)
```

```python
# files/views.py（对应 app/api/projects/[projectId]/files/route.js）
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from common.auth import TokenAuth
from common.response import result
from .handlers.impl.pdf_split_handle import PdfSplitHandle  # 复用 apps 代码
from .handlers.impl.doc_split_handle import DocSplitHandle
from django.utils.translation import gettext_lazy as _

class FileView(APIView):
    authentication_classes = [TokenAuth]
    parser_classes = [MultiPartParser]
    
    @action(methods=['POST'], detail=False)
    @swagger_auto_schema(
        operation_summary=_("上传文件"),
        operation_id="upload_file",
        manual_parameters=[
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True)
        ]
    )
    def post(self, request: Request, project_id: str):
        """上传文件（对应 Node.js POST /api/projects/{projectId}/files）"""
        file = request.FILES.get('file')
        if not file:
            return result.error("文件不能为空", code=400)
        
        # 使用复用的文件处理器
        file_type = file.name.split('.')[-1].lower()
        handler = self._get_handler(file_type)
        
        if not handler:
            return result.error(f"不支持的文件类型: {file_type}", code=400)
        
        # 处理文件（复用 apps/common/handle/ 中的逻辑）
        result_data = handler.handle(file, pattern_list=[], with_filter=False, limit=1000)
        return result.success(result_data)
    
    def _get_handler(self, file_type):
        """获取文件处理器（复用 apps 代码）"""
        handlers = {
            'pdf': PdfSplitHandle(),
            'docx': DocSplitHandle(),
            'doc': DocSplitHandle(),
        }
        return handlers.get(file_type)
```

```python
# llm/views.py（对应 app/api/llm/model/route.js）
from rest_framework.views import APIView
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from common.auth import TokenAuth
from common.response import result
from .providers.impl.openai_model_provider.openai_model_provider import OpenAIProvider  # 复用 apps 代码
from .providers.impl.ollama_model_provider.ollama_model_provider import OllamaProvider
from django.utils.translation import gettext_lazy as _

class LLMView(APIView):
    authentication_classes = [TokenAuth]
    
    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(
        operation_summary=_("获取模型列表"),
        operation_id="get_models"
    )
    def get(self, request: Request):
        """获取模型列表（对应 Node.js GET /api/llm/model）"""
        provider_id = request.query_params.get('providerId')
        if not provider_id:
            return result.error("缺少 providerId 参数", code=400)
        
        # 使用复用的模型提供商（复用 apps/setting/models_provider/）
        provider = self._get_provider(provider_id)
        if not provider:
            return result.error("不支持的提供商", code=404)
        
        models = provider.get_model_list('llm')
        return result.success(models)
    
    def _get_provider(self, provider_id):
        """获取模型提供商（复用 apps 代码）"""
        providers = {
            'openai': OpenAIProvider(),
            'ollama': OllamaProvider(),
        }
        return providers.get(provider_id)
```

### 阶段 5：服务层迁移（2-3周）

**目标**：迁移业务逻辑层

**关键代码**：

```python
# questions/services.py（对应 lib/services/questions/index.js）
from llm.providers.base_model_provider import IModelProvider
from llm.providers.impl.openai_model_provider.openai_model_provider import OpenAIProvider
from projects.models import Project
from .models import Question
from chunks.models import Chunk

class QuestionService:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.project = Project.objects.get(id=project_id)
    
    def generate_questions_for_chunk(self, chunk_id: str, model_config: dict, language: str = '中文'):
        """为文本块生成问题（复用 apps 中的逻辑）"""
        chunk = Chunk.objects.get(id=chunk_id, project_id=self.project_id)
        
        # 使用复用的 LLM 提供商（复用 apps/setting/models_provider/）
        provider = self._get_provider(model_config)
        model = provider.get_model('llm', model_config['model'], model_config)
        
        # 生成问题
        prompt = self._build_prompt(chunk.content, language)
        response = model.chat([{'role': 'user', 'content': prompt}])
        
        # 解析并保存问题
        questions = self._parse_questions(response.text)
        for q in questions:
            Question.objects.create(
                project=self.project,
                chunk=chunk,
                question=q['question'],
                label=q.get('label', '')
            )
        
        return {'total': len(questions)}
    
    def _get_provider(self, model_config: dict) -> IModelProvider:
        """获取模型提供商（复用 apps 代码）"""
        provider_id = model_config.get('providerId', 'openai')
        # 复用 apps/setting/models_provider/ 中的实现
        from llm.providers.impl.openai_model_provider.openai_model_provider import OpenAIProvider
        from llm.providers.impl.ollama_model_provider.ollama_model_provider import OllamaProvider
        
        providers = {
            'openai': OpenAIProvider(),
            'ollama': OllamaProvider(),
        }
        return providers.get(provider_id, OpenAIProvider())
```

### 阶段 6：任务系统迁移（1-2周）

**目标**：使用 Celery 实现异步任务

**关键代码**：

```python
# tasks/celery.py
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'easy_dataset.settings')

app = Celery('easy_dataset')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# tasks/question_generation.py（对应 lib/services/tasks/question-generation.js）
from celery import shared_task
from questions.services import QuestionService
from tasks.models import Task

@shared_task
def process_question_generation_task(task_id: str):
    """处理问题生成任务（对应 Node.js 的 processQuestionGenerationTask）"""
    task = Task.objects.get(id=task_id)
    
    try:
        import json
        model_info = json.loads(task.model_info)
        
        # 查询未生成问题的文本块
        from chunks.models import Chunk
        chunks = Chunk.objects.filter(
            project_id=task.project_id
        ).exclude(name__in=['Image Chunk', 'Distilled Content'])
        
        chunks_without_questions = [
            chunk for chunk in chunks 
            if chunk.questions.count() == 0
        ]
        
        if not chunks_without_questions:
            task.status = 1
            task.note = '没有需要生成问题的文本块'
            task.save()
            return
        
        # 批量处理
        service = QuestionService(task.project_id)
        for chunk in chunks_without_questions:
            service.generate_questions_for_chunk(
                chunk.id,
                model_info,
                task.language
            )
            task.completed_count += 1
            task.save()
        
        task.status = 1
        task.save()
    except Exception as e:
        task.status = 2
        task.note = str(e)
        task.save()
        raise
```

## 📝 代码映射关系

### API 路由映射

| Node.js 路径 | Django 路径 | 说明 |
|-------------|------------|------|
| `app/api/projects/route.js` | `projects/views.py::ProjectView` | 项目管理 |
| `app/api/projects/[projectId]/files/route.js` | `files/views.py::FileView` | 文件管理 |
| `app/api/projects/[projectId]/split/route.js` | `chunks/views.py::SplitView` | 文本分割 |
| `app/api/projects/[projectId]/questions/route.js` | `questions/views.py::QuestionView` | 问题管理 |
| `app/api/projects/[projectId]/datasets/route.js` | `datasets/views.py::DatasetView` | 数据集管理 |

### 服务层映射

| Node.js 路径 | Django 路径 | 复用代码 |
|-------------|------------|---------|
| `lib/services/questions/index.js` | `questions/services.py` | - |
| `lib/services/datasets/index.js` | `datasets/services.py` | - |
| `lib/file/text-splitter.js` | `common/util/split_model.py` | ✅ 100% 复用 |
| `lib/llm/core/index.js` | `llm/providers/` | ✅ 100% 复用 apps |
| `lib/file/file-process/` | `files/handlers/` | ✅ 100% 复用 apps |

## 🚀 实施步骤

### 第一步：环境准备

```bash
# 1. 创建 Django 项目
django-admin startproject easy_dataset
cd easy_dataset

# 2. 创建应用
python manage.py startapp projects
python manage.py startapp datasets
python manage.py startapp questions
python manage.py startapp files
python manage.py startapp llm

# 3. 复制 apps 中的代码
cp -r ../apps/common ./common
cp -r ../apps/setting/models_provider ./llm/providers
cp -r ../apps/common/handle ./files/handlers

# 4. 安装依赖
pip install django djangorestframework drf-yasg django-cors-headers
pip install celery django-celery-beat
pip install openai langchain pypdf python-docx
```

### 第二步：配置项目

```python
# easy_dataset/settings/base.py
# 参考 apps/smartdoc/settings/base.py 进行配置
```

### 第三步：模型迁移

```bash
# 1. 创建模型（从 Prisma Schema 转换）
# 编辑 projects/models.py, datasets/models.py 等

# 2. 创建迁移
python manage.py makemigrations

# 3. 执行迁移
python manage.py migrate
```

### 第四步：API 迁移

按照优先级逐个迁移 API 端点，保持接口兼容性。

### 第五步：测试验证

```bash
# 运行测试
python manage.py test

# 启动服务
python manage.py runserver 0.0.0.0:1717
```

## 📊 迁移检查清单

### 功能完整性
- [ ] 所有 73+ 个 API 端点已迁移
- [ ] 文件上传和处理功能正常（复用 apps/common/handle/）
- [ ] 文本分割功能正常（复用 apps/common/util/split_model.py）
- [ ] 问题生成功能正常
- [ ] 数据集生成功能正常
- [ ] LLM 调用功能正常（复用 apps/setting/models_provider/）
- [ ] 任务系统功能正常（Celery）

### 代码复用
- [ ] common 模块 100% 复用
- [ ] 文件处理模块 100% 复用
- [ ] LLM 提供商模块 100% 复用
- [ ] 工具函数 100% 复用
- [ ] 响应格式 100% 复用

## 🎯 迁移时间表

| 阶段 | 时间 | 说明 |
|------|------|------|
| 阶段1：项目初始化 | 1周 | 搭建项目骨架 |
| 阶段2：模型迁移 | 1-2周 | Prisma → Django ORM |
| 阶段3：复用核心模块 | 1周 | 复制 apps 代码 |
| 阶段4：API 视图迁移 | 3-4周 | 迁移所有 API |
| 阶段5：服务层迁移 | 2-3周 | 业务逻辑迁移 |
| 阶段6：任务系统 | 1-2周 | Celery 集成 |
| **总计** | **9-13周** | - |

## 💡 Django vs FastAPI 选择建议

### 选择 Django 如果：
- ✅ 团队熟悉 Django 或 apps 代码
- ✅ 需要快速迁移（代码复用率高）
- ✅ 需要 Admin 后台管理
- ✅ 需要完整的认证和权限系统
- ✅ 项目规模大，需要成熟框架

### 选择 FastAPI 如果：
- ✅ 追求极致性能
- ✅ 需要异步处理能力
- ✅ 团队更熟悉现代 Python 框架
- ✅ 需要自动 API 文档（Swagger）
- ✅ 项目规模中等，需要轻量级框架

## 🔍 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 代码兼容性问题 | 中 | 仔细测试复用的代码，必要时适配 |
| 性能问题 | 低 | Django 性能足够，必要时优化 |
| 学习曲线 | 低 | 已有 apps 代码参考 |
| 迁移时间 | 中 | 分阶段迁移，逐步验证 |

## 📚 参考资源

- Django 文档：https://docs.djangoproject.com/
- DRF 文档：https://www.django-rest-framework.org/
- apps 参考代码：`apps/` 文件夹
- Node.js 原代码：`lib/` 和 `app/api/` 文件夹

---

**最后更新**：2025年1月
**维护者**：开发团队

