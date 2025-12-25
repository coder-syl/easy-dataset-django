# Celery任务系统实现说明

## ✅ 已完成

### 1. Celery配置 (`easy_dataset/celery.py`)
- ✅ 配置Celery应用
- ✅ 自动发现任务
- ✅ 集成Django设置

### 2. Django设置 (`easy_dataset/settings.py`)
- ✅ Celery Broker配置（Redis）
- ✅ Celery Result Backend配置
- ✅ 任务序列化配置
- ✅ 时区配置
- ✅ 任务超时配置

### 3. Celery任务定义 (`tasks/celery_tasks.py`)
- ✅ `process_task_async` - 异步处理任务
- ✅ `recover_pending_tasks` - 恢复待处理任务
- ✅ 任务重试机制

### 4. 任务处理函数 (`tasks/task_handlers.py`)
- ✅ `process_question_generation_task` - 问题生成任务
- ✅ `process_answer_generation_task` - 答案生成任务
- ✅ 其他任务类型的占位符函数

### 5. 任务视图更新 (`tasks/views.py`)
- ✅ 创建任务时自动启动异步处理

### 6. 管理命令
- ✅ `start_celery_worker` - 启动Celery Worker
- ✅ `start_celery_beat` - 启动Celery Beat（定时任务）

### 7. 依赖更新 (`requirements.txt`)
- ✅ 添加 `celery>=5.3.0`
- ✅ 添加 `redis>=5.0.0`

## 📝 使用说明

### 1. 安装依赖
```bash
cd easy-dataset-django
pip install -r requirements.txt
```

### 2. 启动Redis（如果未运行）
```bash
# Windows (使用WSL或Docker)
# 或使用Redis for Windows

# Linux/Mac
redis-server
```

### 3. 启动Celery Worker
```bash
# 方式1: 使用管理命令
python manage.py start_celery_worker

# 方式2: 直接使用celery命令
celery -A easy_dataset worker --loglevel=info --concurrency=4
```

### 4. 启动Celery Beat（可选，用于定时任务）
```bash
# 方式1: 使用管理命令
python manage.py start_celery_beat

# 方式2: 直接使用celery命令
celery -A easy_dataset beat --loglevel=info
```

### 5. 创建任务
通过API创建任务，系统会自动异步处理：
```bash
POST /api/projects/{projectId}/tasks/
{
  "taskType": "question-generation",
  "modelInfo": {...},
  "language": "zh-CN"
}
```

## 🔧 任务类型

### 已实现
1. **question-generation** - 问题生成任务
   - 批量为文本块生成问题
   - 支持并发控制
   - 进度跟踪

2. **answer-generation** - 答案生成任务
   - 批量为问题生成答案
   - 自动标记问题为已回答
   - 进度跟踪

### 待实现（占位符）
3. **file-processing** - 文件处理任务
4. **data-cleaning** - 数据清洗任务
5. **dataset-evaluation** - 数据集评估任务
6. **multi-turn-generation** - 多轮对话生成任务
7. **data-distillation** - 数据蒸馏任务
8. **image-question-generation** - 图像问题生成任务
9. **image-dataset-generation** - 图像数据集生成任务

## 📊 任务状态

- `0` - 处理中
- `1` - 已完成
- `2` - 失败
- `3` - 已中断

## ⚙️ 配置说明

### Celery Broker URL
默认使用Redis: `redis://localhost:6379/0`

可以通过环境变量配置：
```bash
export CELERY_BROKER_URL=redis://localhost:6379/0
export CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 任务超时
- 硬超时: 30分钟
- 软超时: 25分钟

### 并发控制
- 默认并发数: 4
- 可通过项目配置文件的 `concurrencyLimit` 控制

## 🚀 后续优化

- [ ] 实现其他任务类型的处理逻辑
- [ ] 添加任务优先级支持
- [ ] 实现任务队列管理
- [ ] 添加任务监控和统计
- [ ] 实现任务结果持久化
- [ ] 添加任务通知机制

