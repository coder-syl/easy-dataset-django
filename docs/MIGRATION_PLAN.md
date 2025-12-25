# Node.js 到 Python 后端迁移方案

## 📋 迁移概述

本文档提供将 Easy Dataset 项目的 Node.js 后端迁移到 Python 的完整方案，结合现有 Next.js API 代码和 apps 文件夹中的 Django 参考代码。

## 🎯 迁移目标

- **保持功能完整性**：所有 73+ 个 API 端点功能保持不变
- **提升开发效率**：利用 Python 在 AI/ML 领域的优势
- **代码复用**：最大化利用 apps 中的现有代码
- **平滑过渡**：支持渐进式迁移，不影响现有功能

## 🏗️ 技术选型

### 推荐方案：FastAPI + SQLAlchemy

**选择理由：**
1. **性能优秀**：基于 Starlette，性能接近 Node.js
2. **异步支持**：原生支持 async/await，适合 I/O 密集型任务
3. **自动文档**：自动生成 OpenAPI/Swagger 文档
4. **类型安全**：基于 Pydantic 的类型验证
5. **生态兼容**：与 Python AI 生态（LangChain、OpenAI SDK）完美集成
6. **学习曲线**：相比 Django 更轻量，迁移成本更低

### 技术栈对比

| 组件 | Node.js (当前) | Python (目标) |
|------|---------------|---------------|
| Web框架 | Next.js API Routes | FastAPI |
| ORM | Prisma | SQLAlchemy + Alembic |
| 数据库 | SQLite | SQLite (保持不变) |
| LLM SDK | @ai-sdk/openai | openai / langchain |
| 文件处理 | pdf2md, mammoth | pypdf, python-docx |
| 任务队列 | 内置异步任务 | Celery (可选) |
| 认证 | Next.js 中间件 | FastAPI 依赖注入 |

## 📐 架构设计

### 项目结构

```
easy-dataset-python/
├── app/
│   ├── main.py                    # FastAPI 应用入口
│   ├── config.py                  # 配置管理
│   ├── dependencies.py            # 依赖注入
│   │
│   ├── api/                       # API 路由层
│   │   ├── __init__.py
│   │   ├── projects.py            # 项目相关 API
│   │   ├── datasets.py            # 数据集 API
│   │   ├── questions.py           # 问题 API
│   │   ├── chunks.py              # 文本块 API
│   │   ├── files.py               # 文件 API
│   │   ├── llm.py                 # LLM 相关 API
│   │   └── tasks.py               # 任务 API
│   │
│   ├── models/                    # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── dataset.py
│   │   ├── question.py
│   │   └── ...
│   │
│   ├── schemas/                   # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── dataset.py
│   │   └── ...
│   │
│   ├── services/                  # 业务逻辑层（复用 apps 代码）
│   │   ├── __init__.py
│   │   ├── file_processing.py    # 文件处理（参考 apps/common/handle/）
│   │   ├── llm_service.py        # LLM 服务（参考 apps/setting/models_provider/）
│   │   ├── question_service.py    # 问题生成
│   │   ├── dataset_service.py    # 数据集生成
│   │   └── task_service.py       # 任务处理
│   │
│   ├── db/                        # 数据库访问层
│   │   ├── __init__.py
│   │   ├── base.py                # 数据库连接
│   │   ├── projects.py
│   │   ├── datasets.py
│   │   └── ...
│   │
│   ├── core/                      # 核心模块（复用 apps 代码）
│   │   ├── __init__.py
│   │   ├── file_handlers/         # 文件处理器（参考 apps/common/handle/）
│   │   │   ├── base.py
│   │   │   ├── pdf_handler.py
│   │   │   ├── docx_handler.py
│   │   │   └── markdown_handler.py
│   │   ├── llm_providers/         # LLM 提供商（参考 apps/setting/models_provider/）
│   │   │   ├── base.py
│   │   │   ├── openai_provider.py
│   │   │   ├── ollama_provider.py
│   │   │   └── zhipu_provider.py
│   │   └── text_splitter.py      # 文本分割（参考 apps/common/util/split_model.py）
│   │
│   └── utils/                     # 工具函数（复用 apps 代码）
│       ├── __init__.py
│       ├── response.py            # 统一响应（参考 apps/common/response/result.py）
│       ├── file_util.py           # 文件工具
│       └── cache.py               # 缓存工具
│
├── alembic/                       # 数据库迁移
│   ├── versions/
│   └── env.py
│
├── tests/                         # 测试
│   ├── test_api/
│   └── test_services/
│
├── requirements.txt               # 依赖
├── .env                           # 环境变量
└── README.md
```

## 🔄 迁移策略

### 阶段 1：基础架构搭建（1-2周）

**目标**：搭建 FastAPI 项目骨架，建立数据库连接

**任务清单**：
- [ ] 创建 FastAPI 项目结构
- [ ] 配置 SQLAlchemy 和 Alembic
- [ ] 迁移 Prisma Schema 到 SQLAlchemy Models
- [ ] 实现统一响应格式（参考 apps/common/response/result.py）
- [ ] 配置环境变量和日志

**关键代码示例**：

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import projects, datasets, questions
from app.db.base import engine, Base

app = FastAPI(title="Easy Dataset API", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(datasets.router, prefix="/api/projects/{project_id}/datasets", tags=["datasets"])
app.include_router(questions.router, prefix="/api/projects/{project_id}/questions", tags=["questions"])

@app.on_event("startup")
async def startup():
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
```

### 阶段 2：核心服务迁移（2-3周）

**目标**：迁移核心业务逻辑，复用 apps 中的代码

**优先级排序**：
1. **文件处理服务**（高优先级）
   - 复用 `apps/common/handle/` 中的文件处理逻辑
   - 适配到 FastAPI 架构

2. **LLM 服务**（高优先级）
   - 复用 `apps/setting/models_provider/` 中的模型提供商架构
   - 统一 LLM 调用接口

3. **文本分割服务**（中优先级）
   - 复用 `apps/common/util/split_model.py` 中的分割逻辑

4. **统一响应格式**（中优先级）
   - 复用 `apps/common/response/result.py`

**关键代码示例**：

```python
# app/core/file_handlers/base.py（参考 apps/common/handle/base_split_handle.py）
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseFileHandler(ABC):
    """文件处理器基类（参考 apps 中的 BaseSplitHandle）"""
    
    @abstractmethod
    def support(self, file_type: str) -> bool:
        """判断是否支持该文件类型"""
        pass
    
    @abstractmethod
    async def handle(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """处理文件"""
        pass
    
    @abstractmethod
    async def get_content(self, file_path: str) -> str:
        """提取文件内容"""
        pass
```

```python
# app/core/file_handlers/pdf_handler.py（参考 apps/common/handle/impl/pdf_split_handle.py）
import fitz  # PyMuPDF
from app.core.file_handlers.base import BaseFileHandler

class PDFHandler(BaseFileHandler):
    def support(self, file_type: str) -> bool:
        return file_type.lower() == 'pdf'
    
    async def handle(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        # 复用 apps 中的 PDF 处理逻辑
        pdf_document = fitz.open(file_path)
        try:
            # 处理目录
            result = self.handle_toc(pdf_document, options.get('limit', 1000))
            if result:
                return {'name': file_path, 'content': result}
            
            # 处理内容
            content = self.handle_pdf_content(pdf_document)
            return {'name': file_path, 'content': content}
        finally:
            pdf_document.close()
```

```python
# app/core/llm_providers/base.py（参考 apps/setting/models_provider/base_model_provider.py）
from abc import ABC, abstractmethod
from typing import List, Dict, AsyncIterator

class BaseLLMProvider(ABC):
    """LLM 提供商基类（参考 apps 中的 IModelProvider）"""
    
    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> Dict:
        """普通对话"""
        pass
    
    @abstractmethod
    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncIterator[str]:
        """流式对话"""
        pass
    
    @abstractmethod
    def is_valid_credential(self, credential: Dict) -> bool:
        """验证凭证"""
        pass
```

```python
# app/core/llm_providers/openai_provider.py（参考 apps/setting/models_provider/impl/openai_model_provider/）
from openai import AsyncOpenAI
from app.core.llm_providers.base import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, endpoint: str, api_key: str, model: str):
        self.client = AsyncOpenAI(
            base_url=endpoint,
            api_key=api_key
        )
        self.model = model
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 8192)
        )
        return {
            'text': response.choices[0].message.content,
            'usage': response.usage.dict() if response.usage else None
        }
    
    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

### 阶段 3：API 路由迁移（3-4周）

**目标**：逐个迁移 API 端点

**迁移顺序**：
1. 项目管理 API（`/api/projects`）
2. 文件上传 API（`/api/projects/{id}/files`）
3. 文本分割 API（`/api/projects/{id}/split`）
4. 问题生成 API（`/api/projects/{id}/questions`）
5. 数据集生成 API（`/api/projects/{id}/datasets`）
6. 其他 API...

**关键代码示例**：

```python
# app/api/projects.py（对应 app/api/projects/route.js）
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService
from app.utils.response import success, error

router = APIRouter()

@router.post("", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    """创建项目（对应 Node.js 的 POST /api/projects）"""
    try:
        service = ProjectService(db)
        project = await service.create_project(project_data)
        return success(project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[ProjectResponse])
async def get_projects(db: Session = Depends(get_db)):
    """获取项目列表（对应 Node.js 的 GET /api/projects）"""
    try:
        service = ProjectService(db)
        projects = await service.get_all_projects()
        return success(projects)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

```python
# app/api/datasets.py（对应 app/api/projects/[projectId]/datasets/route.js）
from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.services.dataset_service import DatasetService
from app.utils.response import success

router = APIRouter()

@router.post("")
async def generate_dataset(
    project_id: str = Path(..., description="项目ID"),
    question_id: str = Body(...),
    model: dict = Body(...),
    language: str = Body("中文"),
    db: Session = Depends(get_db)
):
    """生成数据集（对应 Node.js 的 POST /api/projects/{projectId}/datasets）"""
    try:
        service = DatasetService(db)
        result = await service.generate_dataset_for_question(
            project_id, question_id, model, language
        )
        return success(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 阶段 4：任务系统迁移（1-2周）

**目标**：迁移异步任务处理系统

**关键代码示例**：

```python
# app/services/task_service.py（对应 lib/services/tasks/）
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "easy_dataset",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

@celery_app.task(name="process_question_generation")
async def process_question_generation_task(task_id: str):
    """处理问题生成任务（对应 lib/services/tasks/question-generation.js）"""
    from app.db import get_db
    from app.services.question_service import QuestionService
    
    db = next(get_db())
    try:
        # 获取任务信息
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        
        # 解析模型信息
        model_info = json.loads(task.model_info)
        
        # 查询未生成问题的文本块
        chunks = db.query(Chunk).filter(
            Chunk.project_id == task.project_id,
            ~Chunk.name.in_(['Image Chunk', 'Distilled Content'])
        ).all()
        
        chunks_without_questions = [
            chunk for chunk in chunks 
            if len(chunk.questions) == 0
        ]
        
        if not chunks_without_questions:
            task.status = 1
            task.note = '没有需要生成问题的文本块'
            db.commit()
            return
        
        # 批量处理
        service = QuestionService(db)
        for chunk in chunks_without_questions:
            await service.generate_questions_for_chunk(
                task.project_id,
                chunk.id,
                model_info,
                task.language
            )
            task.completed_count += 1
            db.commit()
        
        task.status = 1
        db.commit()
    finally:
        db.close()
```

### 阶段 5：测试和优化（1-2周）

**目标**：确保功能完整性和性能

**任务清单**：
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] API 兼容性测试
- [ ] 性能测试和优化
- [ ] 文档完善

## 📝 代码映射关系

### API 路由映射

| Node.js 路径 | Python 路径 | 说明 |
|-------------|------------|------|
| `app/api/projects/route.js` | `app/api/projects.py` | 项目管理 |
| `app/api/projects/[projectId]/files/route.js` | `app/api/files.py` | 文件管理 |
| `app/api/projects/[projectId]/split/route.js` | `app/api/chunks.py` | 文本分割 |
| `app/api/projects/[projectId]/questions/route.js` | `app/api/questions.py` | 问题管理 |
| `app/api/projects/[projectId]/datasets/route.js` | `app/api/datasets.py` | 数据集管理 |
| `app/api/llm/model/route.js` | `app/api/llm.py` | LLM 相关 |

### 服务层映射

| Node.js 路径 | Python 路径 | 参考代码 |
|-------------|------------|---------|
| `lib/services/questions/index.js` | `app/services/question_service.py` | - |
| `lib/services/datasets/index.js` | `app/services/dataset_service.py` | - |
| `lib/file/text-splitter.js` | `app/core/text_splitter.py` | `apps/common/util/split_model.py` |
| `lib/llm/core/index.js` | `app/core/llm_providers/` | `apps/setting/models_provider/` |
| `lib/file/file-process/` | `app/core/file_handlers/` | `apps/common/handle/` |

### 数据库层映射

| Node.js (Prisma) | Python (SQLAlchemy) |
|-----------------|---------------------|
| `prisma.schema` | `app/models/*.py` |
| `lib/db/projects.js` | `app/db/projects.py` |
| `lib/db/datasets.js` | `app/db/datasets.py` |

## 🔧 实施细节

### 1. 数据库迁移

**从 Prisma Schema 到 SQLAlchemy Models**：

```python
# app/models/project.py（对应 prisma/schema.prisma 中的 Projects）
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.base import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    global_prompt = Column(Text, default="")
    question_prompt = Column(Text, default="")
    answer_prompt = Column(Text, default="")
    create_at = Column(DateTime, default=datetime.utcnow)
    update_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    questions = relationship("Question", back_populates="project")
    datasets = relationship("Dataset", back_populates="project")
```

### 2. 统一响应格式

```python
# app/utils/response.py（参考 apps/common/response/result.py）
from fastapi.responses import JSONResponse
from typing import Any, List, Optional

class Result:
    @staticmethod
    def success(data: Any = None, message: str = "Success") -> JSONResponse:
        """成功响应"""
        return JSONResponse({
            "code": 200,
            "message": message,
            "data": data
        })
    
    @staticmethod
    def error(message: str = "Error", code: int = 500) -> JSONResponse:
        """错误响应"""
        return JSONResponse({
            "code": code,
            "message": message,
            "data": None
        }, status_code=code)
    
    @staticmethod
    def page(total: int, records: List, current: int, size: int) -> dict:
        """分页响应"""
        return {
            "total": total,
            "records": records,
            "current": current,
            "size": size
        }
```

### 3. 文件处理服务集成

```python
# app/services/file_processing_service.py
from app.core.file_handlers.pdf_handler import PDFHandler
from app.core.file_handlers.docx_handler import DOCXHandler
from app.core.file_handlers.markdown_handler import MarkdownHandler

class FileProcessingService:
    def __init__(self):
        self.handlers = {
            'pdf': PDFHandler(),
            'docx': DOCXHandler(),
            'md': MarkdownHandler(),
        }
    
    async def process_file(self, file_path: str, file_type: str, options: dict):
        """处理文件（复用 apps 中的逻辑）"""
        handler = self.handlers.get(file_type.lower())
        if not handler:
            raise ValueError(f"不支持的文件类型: {file_type}")
        
        return await handler.handle(file_path, options)
```

## 🚀 迁移步骤

### 第一步：环境准备

```bash
# 1. 创建 Python 虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install fastapi uvicorn sqlalchemy alembic pydantic
pip install openai langchain pypdf python-docx
pip install celery redis  # 可选：任务队列

# 3. 创建项目结构
mkdir -p app/{api,models,schemas,services,db,core,utils}
```

### 第二步：数据库迁移

```bash
# 1. 初始化 Alembic
alembic init alembic

# 2. 从 Prisma Schema 生成 SQLAlchemy Models
# （手动转换或使用工具）

# 3. 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 4. 执行迁移
alembic upgrade head
```

### 第三步：核心服务迁移

1. **复用 apps 中的文件处理代码**
   - 复制 `apps/common/handle/` 到 `app/core/file_handlers/`
   - 适配为 FastAPI 服务

2. **复用 apps 中的 LLM 提供商代码**
   - 复制 `apps/setting/models_provider/` 到 `app/core/llm_providers/`
   - 适配为统一接口

3. **复用 apps 中的工具函数**
   - 复制 `apps/common/util/` 到 `app/utils/`
   - 适配响应格式

### 第四步：API 路由迁移

按照优先级逐个迁移 API 端点，保持接口兼容性。

### 第五步：测试验证

```bash
# 运行测试
pytest tests/

# 启动服务
uvicorn app.main:app --reload --port 1717
```

## 📊 迁移检查清单

### 功能完整性
- [ ] 所有 73+ 个 API 端点已迁移
- [ ] 文件上传和处理功能正常
- [ ] 文本分割功能正常
- [ ] 问题生成功能正常
- [ ] 数据集生成功能正常
- [ ] LLM 调用功能正常
- [ ] 任务系统功能正常

### 代码质量
- [ ] 代码符合 PEP 8 规范
- [ ] 类型注解完整
- [ ] 错误处理完善
- [ ] 日志记录完善
- [ ] 单元测试覆盖率达到 80%+

### 性能指标
- [ ] API 响应时间 < 500ms（简单请求）
- [ ] 文件处理性能不低于 Node.js 版本
- [ ] 并发处理能力正常

## 🎯 迁移时间表

| 阶段 | 时间 | 负责人 | 状态 |
|------|------|--------|------|
| 阶段1：基础架构 | 1-2周 | - | 待开始 |
| 阶段2：核心服务 | 2-3周 | - | 待开始 |
| 阶段3：API路由 | 3-4周 | - | 待开始 |
| 阶段4：任务系统 | 1-2周 | - | 待开始 |
| 阶段5：测试优化 | 1-2周 | - | 待开始 |
| **总计** | **8-13周** | - | - |

## 💡 最佳实践

1. **渐进式迁移**：先迁移核心功能，再迁移辅助功能
2. **代码复用**：最大化利用 apps 中的现有代码
3. **接口兼容**：保持 API 接口不变，前端无需修改
4. **测试驱动**：每个功能迁移后立即测试
5. **文档同步**：及时更新 API 文档

## 🔍 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 性能下降 | 高 | 使用异步处理，优化数据库查询 |
| 功能缺失 | 高 | 详细的功能对比测试 |
| 数据迁移问题 | 中 | 使用 Alembic 进行数据库迁移 |
| 学习曲线 | 低 | 团队培训，代码审查 |

## 📚 参考资源

- FastAPI 文档：https://fastapi.tiangolo.com/
- SQLAlchemy 文档：https://docs.sqlalchemy.org/
- apps 参考代码：`apps/` 文件夹
- Node.js 原代码：`lib/` 和 `app/api/` 文件夹

---

**最后更新**：2025年1月
**维护者**：开发团队

