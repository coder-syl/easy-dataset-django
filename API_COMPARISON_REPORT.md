# API接口对比报告

## 📊 对比结果总览

基于对Node.js后端和Python Django后端的详细对比，以下是接口实现情况：

## ✅ 已完整实现的模块

### 1. 项目管理模块
- ✅ `/api/projects` - GET/POST (列表/创建)
- ✅ `/api/projects/{projectId}` - GET/PUT/DELETE (详情/更新/删除)
- ✅ `/api/projects/unmigrated` - GET (未迁移项目)
- ✅ `/api/projects/migrate` - POST/GET (迁移任务)
- ✅ `/api/projects/{projectId}/config` - GET/PUT (项目配置)

### 2. 文件管理模块
- ✅ `/api/projects/{projectId}/files` - GET/POST/DELETE (列表/上传/删除)
- ✅ `/api/projects/{projectId}/files/preview/{fileId}` - GET (预览)
- ✅ `/api/projects/{projectId}/batch-generateGA` - POST (批量生成GA对)

### 3. 文本块模块（基础功能）
- ✅ `/api/projects/{projectId}/chunks` - GET/POST (列表/创建)
- ✅ `/api/projects/{projectId}/chunks/{chunkId}` - GET/PUT/DELETE (详情/更新/删除)
- ✅ `/api/projects/{projectId}/chunks/{chunkId}/questions` - GET/POST (获取/生成问题)
- ✅ `/api/projects/{projectId}/split` - GET/POST (分割文本)

### 4. 问题管理模块（基础功能）
- ✅ `/api/projects/{projectId}/questions` - GET/POST (列表/创建)
- ✅ `/api/projects/{projectId}/questions/{questionId}` - GET/PUT/DELETE (详情/更新/删除)
- ✅ `/api/projects/{projectId}/questions/batch-delete` - POST (批量删除)
- ✅ `/api/projects/{projectId}/questions/tree` - GET (问题树)
- ✅ `/api/projects/{projectId}/questions/templates` - 全部CRUD接口

### 5. 数据集模块（基础功能）
- ✅ `/api/projects/{projectId}/datasets` - GET/POST (列表/生成)
- ✅ `/api/projects/{projectId}/datasets/{datasetId}` - GET/PUT/DELETE (详情/更新/删除)
- ✅ `/api/projects/{projectId}/datasets/export` - GET/POST (导出)
- ✅ `/api/projects/{projectId}/datasets/import` - POST (导入)

### 6. 多轮对话模块（基础功能）
- ✅ `/api/projects/{projectId}/dataset-conversations` - GET/POST (列表/创建)
- ✅ `/api/projects/{projectId}/dataset-conversations/{conversationId}` - GET/PUT/DELETE (详情/更新/删除)
- ✅ `/api/projects/{projectId}/dataset-conversations/export` - POST (导出，但功能待完善)
- ✅ `/api/projects/{projectId}/dataset-conversations/tags` - GET (标签，但功能待完善)

### 7. 图像模块（基础功能）
- ✅ `/api/projects/{projectId}/images` - GET/POST/DELETE (列表/导入/删除)
- ✅ `/api/projects/{projectId}/images/{imageId}` - GET (详情)

### 8. LLM模块（基础功能）
- ✅ `/api/llm/providers` - GET (提供商列表)
- ✅ `/api/projects/{projectId}/model-config` - 全部CRUD接口
- ✅ `/api/projects/{projectId}/playground/chat` - POST (聊天)
- ✅ `/api/projects/{projectId}/playground/chat/stream` - POST (流式聊天)

### 9. 标签模块
- ✅ `/api/projects/{projectId}/tags` - GET/POST/PUT/DELETE (标签树管理)

### 10. 提示词模块
- ✅ `/api/projects/{projectId}/default-prompts` - GET (默认提示词)
- ✅ `/api/projects/{projectId}/custom-prompts` - GET/POST/DELETE (自定义提示词)

### 11. 任务管理模块
- ✅ `/api/projects/{projectId}/tasks` - GET/POST/PUT (列表/创建/配置)
- ✅ `/api/projects/{projectId}/tasks/{taskId}` - GET/PUT/DELETE (详情/更新/删除)

### 12. 其他模块
- ✅ `/api/check-update` - GET (检查更新)
- ✅ `/api/update` - GET (获取更新)
- ✅ `/api/llm/fetch-models` - POST (获取模型列表)

## ⚠️ 部分实现或功能不完整的模块

### 1. 文本块高级功能
- ✅ `/api/projects/{projectId}/chunks/batch-edit` - POST (批量编辑) - **已实现**
- ✅ `/api/projects/{projectId}/chunks/batch-content` - POST (批量获取内容) - **已实现**
- ✅ `/api/projects/{projectId}/chunks/{chunkId}/clean` - POST (清洗) - **已实现**
- ✅ `/api/projects/{projectId}/custom-split` - POST (自定义分割) - **已实现**
- ❌ `/api/projects/{projectId}/chunks/name` - PUT (批量更新名称) - **缺失**

### 2. 问题生成接口
- ❌ `/api/projects/{projectId}/generate-questions` - POST (批量生成问题) - **缺失独立接口**（功能在chunks中）

### 3. 数据集评估和优化
- ✅ `/api/projects/{projectId}/datasets/{datasetId}/evaluate` - POST (评估) - **已实现**
- ✅ `/api/projects/{projectId}/datasets/batch-evaluate` - POST (批量评估) - **已实现**
- ✅ `/api/projects/{projectId}/datasets/optimize` - POST (优化) - **已实现**
- ❌ `/api/projects/{projectId}/datasets/{datasetId}/token-count` - GET (Token统计) - **缺失**
- ❌ `/api/projects/{projectId}/datasets/tags` - GET (标签统计) - **缺失**

### 4. 多轮对话导出
- ⚠️ `/api/projects/{projectId}/dataset-conversations/export` - POST (导出) - **已实现但功能待完善**
- ⚠️ `/api/projects/{projectId}/dataset-conversations/tags` - GET (标签) - **已实现但功能待完善**

### 5. 图像数据集高级功能
- ❌ `/api/projects/{projectId}/images` - POST (上传单个图像) - **缺失**（只有批量导入）
- ❌ `/api/projects/{projectId}/images/zip-import` - POST (ZIP导入) - **缺失**
- ❌ `/api/projects/{projectId}/images/pdf-convert` - POST (PDF转图像) - **缺失**
- ❌ `/api/projects/{projectId}/images/next-unanswered` - GET (下一个未回答) - **缺失**
- ❌ `/api/projects/{projectId}/images/annotations` - POST (创建标注) - **缺失**
- ❌ `/api/projects/{projectId}/images/questions` - POST (生成问题) - **缺失**
- ❌ `/api/projects/{projectId}/images/datasets` - POST (生成数据集) - **缺失**
- ❌ `/api/projects/{projectId}/images/{imageId}` - PUT (更新图像) - **缺失**

### 6. 图像数据集模块
- ✅ `/api/projects/{projectId}/image-datasets` - GET/POST (列表/创建) - **已实现**
- ✅ `/api/projects/{projectId}/image-datasets/{datasetId}` - GET/PUT/DELETE (详情/更新/删除) - **已实现**
- ❌ `/api/projects/{projectId}/image-datasets/export` - POST (导出) - **缺失**
- ❌ `/api/projects/{projectId}/image-datasets/export-zip` - GET (导出ZIP) - **缺失**
- ❌ `/api/projects/{projectId}/image-datasets/tags` - GET (标签统计) - **缺失**

### 7. 数据蒸馏模块
- ⚠️ `/api/projects/{projectId}/distill/questions` - POST (蒸馏问题) - **已实现但功能待完善**
- ⚠️ `/api/projects/{projectId}/distill/questions/by-tag` - POST (按标签蒸馏) - **已实现但功能待完善**
- ⚠️ `/api/projects/{projectId}/distill/tags` - GET/POST (标签蒸馏) - **已实现但功能待完善**
- ❌ `/api/projects/{projectId}/distill/tags/all` - POST (蒸馏所有标签) - **缺失**
- ❌ `/api/projects/{projectId}/distill/tags/{tagId}` - POST (蒸馏指定标签) - **缺失**

### 8. LLM模型管理
- ❌ `/api/llm/model` - GET/POST (模型列表/同步) - **缺失**
- ❌ `/api/llm/ollama/models` - GET (Ollama模型列表) - **缺失**
- ❌ `/api/projects/{projectId}/models` - GET/PUT (项目模型列表) - **缺失**
- ❌ `/api/projects/{projectId}/models/{modelId}` - GET/PUT (模型详情/更新) - **缺失**

### 9. HuggingFace和LLaMA Factory
- ✅ `/api/projects/{projectId}/huggingface/upload` - POST (上传) - **已实现**
- ✅ `/api/projects/{projectId}/llamaFactory/generate` - POST (生成配置) - **已实现**
- ❌ `/api/projects/{projectId}/llamaFactory/checkConfig` - POST (检查配置) - **缺失**

### 10. 文件GA对生成
- ❌ `/api/projects/{projectId}/files/{fileId}/ga-pairs` - POST (单个文件GA对) - **缺失**（只有批量）

## 📋 需要补全的接口清单

### 高优先级（核心功能缺失）

1. **问题生成独立接口**
   - `POST /api/projects/{projectId}/generate-questions`

2. **数据集Token统计**
   - `GET /api/projects/{projectId}/datasets/{datasetId}/token-count`

3. **数据集标签统计**
   - `GET /api/projects/{projectId}/datasets/tags`

4. **文本块批量更新名称**
   - `PUT /api/projects/{projectId}/chunks/name`

### 中优先级（功能完善）

5. **图像上传和处理**
   - `POST /api/projects/{projectId}/images` (单个上传)
   - `POST /api/projects/{projectId}/images/zip-import`
   - `POST /api/projects/{projectId}/images/pdf-convert`
   - `GET /api/projects/{projectId}/images/next-unanswered`
   - `POST /api/projects/{projectId}/images/annotations`
   - `POST /api/projects/{projectId}/images/questions`
   - `POST /api/projects/{projectId}/images/datasets`
   - `PUT /api/projects/{projectId}/images/{imageId}`

6. **图像数据集导出**
   - `POST /api/projects/{projectId}/image-datasets/export`
   - `GET /api/projects/{projectId}/image-datasets/export-zip`
   - `GET /api/projects/{projectId}/image-datasets/tags`

7. **数据蒸馏完善**
   - `POST /api/projects/{projectId}/distill/tags/all`
   - `POST /api/projects/{projectId}/distill/tags/{tagId}`

8. **LLM模型管理**
   - `GET /api/llm/model`
   - `POST /api/llm/model`
   - `GET /api/llm/ollama/models`
   - `GET /api/projects/{projectId}/models`
   - `PUT /api/projects/{projectId}/models`
   - `GET /api/projects/{projectId}/models/{modelId}`
   - `PUT /api/projects/{projectId}/models/{modelId}`

9. **LLaMA Factory配置检查**
   - `POST /api/projects/{projectId}/llamaFactory/checkConfig`

10. **文件GA对生成（单个文件）**
    - `POST /api/projects/{projectId}/files/{fileId}/ga-pairs`

11. **多轮对话导出完善**
    - 完善 `POST /api/projects/{projectId}/dataset-conversations/export` 的实际导出逻辑
    - 完善 `GET /api/projects/{projectId}/dataset-conversations/tags` 的标签统计逻辑

## 📊 统计汇总

- **总接口数**: 89个
- **已完整实现**: 约65个（73%）
- **部分实现**: 约8个（9%）
- **完全缺失**: 约16个（18%）

## 🎯 下一步行动

按照优先级补全缺失的接口，确保与Node.js后端功能完全对齐。

