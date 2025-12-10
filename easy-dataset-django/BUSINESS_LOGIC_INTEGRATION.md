# 业务逻辑集成文档

## 已集成的服务模块

### 1. 文本分割服务 (`common/services/text_splitter.py`)

**功能**：
- Markdown文本智能分割
- 字符分块
- 自定义分隔符分块
- 目录结构提取

**使用方法**：
```python
from common.services.text_splitter import split_text_by_type

result = split_text_by_type(
    text=file_content,
    split_type='markdown',  # markdown, text, custom
    chunk_size=1500,
    chunk_overlap=200
)
```

### 2. LLM服务 (`common/services/llm_service.py`)

**功能**：
- 统一LLM调用接口
- 支持多种模型提供商（OpenAI、Ollama、智谱AI等）
- 思维链提取
- HTTP API回退机制

**使用方法**：
```python
from common.services.llm_service import LLMService

llm_service = LLMService({
    'provider_id': 'openai',
    'endpoint': 'https://api.openai.com/v1/',
    'api_key': 'your-api-key',
    'model_id': 'gpt-4',
    'temperature': 0.7,
    'max_tokens': 8192
})

# 生成响应
response = llm_service.chat([
    {'role': 'user', 'content': 'Hello'}
])

# 带思维链的响应
response = llm_service.get_response_with_cot('你的提示词')
```

### 3. 文本块服务 (`chunks/services.py`)

**功能**：
- 文件分割处理
- 文本块保存
- 目录结构提取
- 文件统计

**已集成到视图**：
- `chunk_split` - 文本分割
- `chunk_list` - 获取文本块列表

### 4. 数据集生成服务 (`datasets/services.py`)

**功能**：
- 单问题答案生成
- 提示词构建
- 数据集保存
- 问题状态更新

**已集成到视图**：
- `dataset_generate` - 生成数据集

### 5. 多轮对话服务 (`conversations/services.py`)

**功能**：
- 多轮对话生成
- 对话历史管理
- 下一轮问题生成
- 角色设定

**已集成到视图**：
- `conversation_list_create` - 创建多轮对话

### 6. 问题蒸馏服务 (`distill/views.py`)

**功能**：
- 问题生成
- 问题解析
- 问题保存
- 标签关联

**已集成到视图**：
- `distill_questions` - 蒸馏问题

## 集成状态

### ✅ 已完成
- [x] 文本分割服务
- [x] LLM服务（HTTP API方式）
- [x] 数据集生成服务
- [x] 多轮对话服务
- [x] 问题蒸馏服务
- [x] Playground聊天服务

### ⏳ 待完善
- [ ] LLM服务（集成apps中的模型提供商，需要安装langchain等依赖）
- [ ] 文件处理（PDF、DOCX等格式）
- [ ] 图像处理逻辑
- [ ] 批量生成GA对逻辑
- [ ] 流式响应支持

## 依赖说明

### 必需依赖
- `requests` - HTTP API调用
- `nanoid` - ID生成
- `jieba` - 中文分词（文本分割）

### 可选依赖（用于完整功能）
- `langchain` - LLM模型调用（如果使用apps中的模型提供商）
- `langchain-openai` - OpenAI集成
- `langchain-community` - 社区模型集成

## 使用示例

### 文本分割
```python
from chunks.services import split_project_file

result = split_project_file(project_id='xxx', file_name='test.md')
# 返回: {'chunks': [...], 'totalChunks': 10, 'toc': '...'}
```

### 数据集生成
```python
from datasets.services import generate_dataset_for_question

dataset = generate_dataset_for_question(
    project_id='xxx',
    question_id='yyy',
    options={
        'model': {'provider_id': 'openai', 'model_id': 'gpt-4', ...},
        'language': '中文'
    }
)
```

### 多轮对话生成
```python
from conversations.services import generate_multi_turn_conversation

result = generate_multi_turn_conversation(
    project_id='xxx',
    question_id='yyy',
    config={
        'systemPrompt': '...',
        'rounds': 3,
        'model': {...},
        'language': '中文'
    }
)
```

## 注意事项

1. **异步调用**：当前LLM服务使用同步HTTP调用，如需异步支持，可以使用Django的异步视图或Celery任务。

2. **错误处理**：所有服务都包含错误处理，会抛出异常，需要在视图中捕获。

3. **apps路径**：LLM服务会尝试导入apps中的模型提供商，如果导入失败，会回退到HTTP API方式。

4. **模型配置**：模型配置需要包含完整的提供商信息（provider_id, endpoint, api_key, model_id等）。

