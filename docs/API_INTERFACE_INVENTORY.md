# Easy Dataset API 接口清单

## 📋 接口统计

- **总接口数**: 79+ 个
- **主要模块**: 8 个
- **HTTP方法**: GET, POST, PUT, DELETE

## 🔍 接口分类

### 1. 项目管理模块 (Projects)

#### `/api/projects`
- `POST /api/projects` - 创建项目
- `GET /api/projects` - 获取项目列表
- `GET /api/projects/unmigrated` - 获取未迁移项目
- `POST /api/projects/migrate` - 迁移项目
- `GET /api/projects/open-directory` - 打开目录
- `POST /api/projects/delete-directory` - 删除目录

#### `/api/projects/{projectId}`
- `GET /api/projects/{projectId}` - 获取项目详情
- `PUT /api/projects/{projectId}` - 更新项目
- `DELETE /api/projects/{projectId}` - 删除项目

#### `/api/projects/{projectId}/config`
- `GET /api/projects/{projectId}/config` - 获取项目配置
- `PUT /api/projects/{projectId}/config` - 更新项目配置

### 2. 文件管理模块 (Files)

#### `/api/projects/{projectId}/files`
- `GET /api/projects/{projectId}/files` - 获取文件列表
- `POST /api/projects/{projectId}/files` - 上传文件
- `DELETE /api/projects/{projectId}/files` - 删除文件

#### `/api/projects/{projectId}/files/{fileId}/ga-pairs`
- `POST /api/projects/{projectId}/files/{fileId}/ga-pairs` - 生成GA对

#### `/api/projects/{projectId}/preview/{fileId}`
- `GET /api/projects/{projectId}/preview/{fileId}` - 预览文件

### 3. 文本分割模块 (Split/Chunks)

#### `/api/projects/{projectId}/split`
- `POST /api/projects/{projectId}/split` - 分割文本
- `GET /api/projects/{projectId}/split` - 获取分割结果

#### `/api/projects/{projectId}/custom-split`
- `POST /api/projects/{projectId}/custom-split` - 自定义分割

#### `/api/projects/{projectId}/chunks`
- `GET /api/projects/{projectId}/chunks` - 获取文本块列表
- `POST /api/projects/{projectId}/chunks` - 创建文本块
- `PUT /api/projects/{projectId}/chunks/batch-edit` - 批量编辑文本块
- `POST /api/projects/{projectId}/chunks/batch-content` - 批量更新内容

#### `/api/projects/{projectId}/chunks/{chunkId}`
- `GET /api/projects/{projectId}/chunks/{chunkId}` - 获取文本块详情
- `PUT /api/projects/{projectId}/chunks/{chunkId}` - 更新文本块
- `DELETE /api/projects/{projectId}/chunks/{chunkId}` - 删除文本块
- `POST /api/projects/{projectId}/chunks/{chunkId}/clean` - 清洗文本块
- `GET /api/projects/{projectId}/chunks/{chunkId}/questions` - 获取文本块的问题

#### `/api/projects/{projectId}/chunks/name`
- `PUT /api/projects/{projectId}/chunks/name` - 更新文本块名称

### 4. 问题管理模块 (Questions)

#### `/api/projects/{projectId}/questions`
- `GET /api/projects/{projectId}/questions` - 获取问题列表（支持分页、筛选）
- `POST /api/projects/{projectId}/questions` - 创建问题
- `POST /api/projects/{projectId}/questions/batch-delete` - 批量删除问题

#### `/api/projects/{projectId}/questions/{questionId}`
- `GET /api/projects/{projectId}/questions/{questionId}` - 获取问题详情
- `PUT /api/projects/{projectId}/questions/{questionId}` - 更新问题
- `DELETE /api/projects/{projectId}/questions/{questionId}` - 删除问题

#### `/api/projects/{projectId}/questions/tree`
- `GET /api/projects/{projectId}/questions/tree` - 获取问题树

#### `/api/projects/{projectId}/questions/templates`
- `GET /api/projects/{projectId}/questions/templates` - 获取问题模板列表
- `POST /api/projects/{projectId}/questions/templates` - 创建问题模板
- `GET /api/projects/{projectId}/questions/templates/{templateId}` - 获取模板详情
- `PUT /api/projects/{projectId}/questions/templates/{templateId}` - 更新模板
- `DELETE /api/projects/{projectId}/questions/templates/{templateId}` - 删除模板

#### `/api/projects/{projectId}/generate-questions`
- `POST /api/projects/{projectId}/generate-questions` - 生成问题

### 5. 数据集模块 (Datasets)

#### `/api/projects/{projectId}/datasets`
- `GET /api/projects/{projectId}/datasets` - 获取数据集列表（支持分页、筛选）
- `POST /api/projects/{projectId}/datasets` - 生成数据集
- `POST /api/projects/{projectId}/datasets/import` - 导入数据集
- `POST /api/projects/{projectId}/datasets/export` - 导出数据集
- `POST /api/projects/{projectId}/datasets/batch-evaluate` - 批量评估数据集
- `POST /api/projects/{projectId}/datasets/optimize` - 优化数据集

#### `/api/projects/{projectId}/datasets/{datasetId}`
- `GET /api/projects/{projectId}/datasets/{datasetId}` - 获取数据集详情
- `PUT /api/projects/{projectId}/datasets/{datasetId}` - 更新数据集
- `DELETE /api/projects/{projectId}/datasets/{datasetId}` - 删除数据集
- `POST /api/projects/{projectId}/datasets/{datasetId}/evaluate` - 评估数据集
- `GET /api/projects/{projectId}/datasets/{datasetId}/token-count` - 获取Token数量

#### `/api/projects/{projectId}/datasets/tags`
- `GET /api/projects/{projectId}/datasets/tags` - 获取数据集标签

### 6. 多轮对话模块 (Dataset Conversations)

#### `/api/projects/{projectId}/dataset-conversations`
- `GET /api/projects/{projectId}/dataset-conversations` - 获取对话列表（支持分页、筛选）
- `POST /api/projects/{projectId}/dataset-conversations` - 创建对话
- `POST /api/projects/{projectId}/dataset-conversations/export` - 导出对话

#### `/api/projects/{projectId}/dataset-conversations/{conversationId}`
- `GET /api/projects/{projectId}/dataset-conversations/{conversationId}` - 获取对话详情
- `PUT /api/projects/{projectId}/dataset-conversations/{conversationId}` - 更新对话
- `DELETE /api/projects/{projectId}/dataset-conversations/{conversationId}` - 删除对话

#### `/api/projects/{projectId}/dataset-conversations/tags`
- `GET /api/projects/{projectId}/dataset-conversations/tags` - 获取对话标签

### 7. 图像数据集模块 (Image Datasets)

#### `/api/projects/{projectId}/images`
- `GET /api/projects/{projectId}/images` - 获取图像列表
- `POST /api/projects/{projectId}/images` - 上传图像
- `POST /api/projects/{projectId}/images/zip-import` - 批量导入图像
- `POST /api/projects/{projectId}/images/pdf-convert` - PDF转图像
- `GET /api/projects/{projectId}/images/next-unanswered` - 获取下一个未回答的图像
- `POST /api/projects/{projectId}/images/annotations` - 创建标注
- `POST /api/projects/{projectId}/images/questions` - 生成图像问题
- `POST /api/projects/{projectId}/images/datasets` - 生成图像数据集

#### `/api/projects/{projectId}/images/{imageId}`
- `GET /api/projects/{projectId}/images/{imageId}` - 获取图像详情
- `PUT /api/projects/{projectId}/images/{imageId}` - 更新图像
- `DELETE /api/projects/{projectId}/images/{imageId}` - 删除图像

#### `/api/projects/{projectId}/image-datasets`
- `GET /api/projects/{projectId}/image-datasets` - 获取图像数据集列表
- `POST /api/projects/{projectId}/image-datasets` - 创建图像数据集
- `POST /api/projects/{projectId}/image-datasets/export` - 导出图像数据集
- `POST /api/projects/{projectId}/image-datasets/export-zip` - 导出为ZIP

#### `/api/projects/{projectId}/image-datasets/{datasetId}`
- `GET /api/projects/{projectId}/image-datasets/{datasetId}` - 获取图像数据集详情
- `PUT /api/projects/{projectId}/image-datasets/{datasetId}` - 更新图像数据集
- `DELETE /api/projects/{projectId}/image-datasets/{datasetId}` - 删除图像数据集

#### `/api/projects/{projectId}/image-datasets/tags`
- `GET /api/projects/{projectId}/image-datasets/tags` - 获取图像数据集标签

### 8. LLM 相关模块

#### `/api/llm/providers`
- `GET /api/llm/providers` - 获取LLM提供商列表

#### `/api/llm/model`
- `GET /api/llm/model` - 获取模型列表
- `POST /api/llm/model` - 同步模型列表

#### `/api/llm/fetch-models`
- `POST /api/llm/fetch-models` - 从提供商获取模型列表

#### `/api/llm/ollama/models`
- `GET /api/llm/ollama/models` - 获取Ollama模型列表

#### `/api/projects/{projectId}/models`
- `GET /api/projects/{projectId}/models` - 获取项目模型列表
- `PUT /api/projects/{projectId}/models` - 更新模型列表

#### `/api/projects/{projectId}/models/{modelId}`
- `GET /api/projects/{projectId}/models/{modelId}` - 获取模型详情
- `PUT /api/projects/{projectId}/models/{modelId}` - 更新模型

#### `/api/projects/{projectId}/model-config`
- `GET /api/projects/{projectId}/model-config` - 获取模型配置列表
- `POST /api/projects/{projectId}/model-config` - 保存模型配置

#### `/api/projects/{projectId}/model-config/{modelConfigId}`
- `GET /api/projects/{projectId}/model-config/{modelConfigId}` - 获取模型配置详情
- `PUT /api/projects/{projectId}/model-config/{modelConfigId}` - 更新模型配置
- `DELETE /api/projects/{projectId}/model-config/{modelConfigId}` - 删除模型配置

#### `/api/projects/{projectId}/playground/chat`
- `POST /api/projects/{projectId}/playground/chat` - 测试对话
- `POST /api/projects/{projectId}/playground/chat/stream` - 流式测试对话

### 9. 提示词模块 (Prompts)

#### `/api/projects/{projectId}/default-prompts`
- `GET /api/projects/{projectId}/default-prompts` - 获取默认提示词

#### `/api/projects/{projectId}/custom-prompts`
- `GET /api/projects/{projectId}/custom-prompts` - 获取自定义提示词
- `POST /api/projects/{projectId}/custom-prompts` - 保存自定义提示词
- `PUT /api/projects/{projectId}/custom-prompts` - 批量保存自定义提示词
- `DELETE /api/projects/{projectId}/custom-prompts` - 删除自定义提示词

### 10. 标签模块 (Tags)

#### `/api/projects/{projectId}/tags`
- `GET /api/projects/{projectId}/tags` - 获取标签树
- `POST /api/projects/{projectId}/tags` - 创建标签
- `PUT /api/projects/{projectId}/tags` - 更新标签
- `DELETE /api/projects/{projectId}/tags` - 删除标签

### 11. 数据蒸馏模块 (Distill)

#### `/api/projects/{projectId}/distill/questions`
- `POST /api/projects/{projectId}/distill/questions` - 蒸馏问题
- `POST /api/projects/{projectId}/distill/questions/by-tag` - 按标签蒸馏问题

#### `/api/projects/{projectId}/distill/tags`
- `GET /api/projects/{projectId}/distill/tags` - 获取可蒸馏标签
- `POST /api/projects/{projectId}/distill/tags` - 蒸馏标签
- `POST /api/projects/{projectId}/distill/tags/all` - 蒸馏所有标签
- `POST /api/projects/{projectId}/distill/tags/{tagId}` - 蒸馏指定标签

### 12. 任务管理模块 (Tasks)

#### `/api/projects/{projectId}/tasks`
- `GET /api/projects/{projectId}/tasks` - 获取任务列表
- `POST /api/projects/{projectId}/tasks` - 创建任务
- `PUT /api/projects/{projectId}/tasks` - 更新任务配置

#### `/api/projects/{projectId}/tasks/list`
- `GET /api/projects/{projectId}/tasks/list` - 获取任务列表（分页）

#### `/api/projects/{projectId}/tasks/{taskId}`
- `GET /api/projects/{projectId}/tasks/{taskId}` - 获取任务详情
- `PUT /api/projects/{projectId}/tasks/{taskId}` - 更新任务
- `DELETE /api/projects/{projectId}/tasks/{taskId}` - 删除任务

### 13. 其他模块

#### `/api/projects/{projectId}/batch-generateGA`
- `POST /api/projects/{projectId}/batch-generateGA` - 批量生成GA对

#### `/api/projects/{projectId}/huggingface/upload`
- `POST /api/projects/{projectId}/huggingface/upload` - 上传到HuggingFace

#### `/api/projects/{projectId}/llamaFactory/checkConfig`
- `POST /api/projects/{projectId}/llamaFactory/checkConfig` - 检查LLaMA Factory配置

#### `/api/projects/{projectId}/llamaFactory/generate`
- `POST /api/projects/{projectId}/llamaFactory/generate` - 生成LLaMA Factory配置

#### `/api/check-update`
- `GET /api/check-update` - 检查更新

#### `/api/update`
- `GET /api/update` - 获取更新信息

## 📊 接口统计汇总

| 模块 | 接口数量 | 主要功能 |
|------|---------|---------|
| 项目管理 | 8 | CRUD操作、迁移 |
| 文件管理 | 4 | 上传、删除、预览、GA对 |
| 文本分割 | 10 | 分割、文本块管理 |
| 问题管理 | 9 | 问题CRUD、模板、生成 |
| 数据集 | 10 | 数据集CRUD、导入导出、评估 |
| 多轮对话 | 4 | 对话管理、导出 |
| 图像数据集 | 12 | 图像管理、标注、数据集 |
| LLM相关 | 9 | 模型管理、配置、测试 |
| 提示词 | 3 | 默认提示词、自定义提示词 |
| 标签 | 4 | 标签树管理 |
| 数据蒸馏 | 5 | 问题蒸馏、标签蒸馏 |
| 任务管理 | 5 | 任务CRUD、列表 |
| 其他 | 6 | GA生成、HuggingFace、LLaMA Factory |
| **总计** | **89** | - |

## 🔑 关键接口优先级

### 高优先级（核心功能）
1. 项目管理（创建、列表、详情）
2. 文件上传和处理
3. 文本分割
4. 问题生成
5. 数据集生成
6. LLM模型配置和调用

### 中优先级（重要功能）
1. 多轮对话生成
2. 图像数据集
3. 数据蒸馏
4. 任务管理

### 低优先级（辅助功能）
1. 标签管理
2. 提示词管理
3. 导出功能
4. 第三方集成（HuggingFace、LLaMA Factory）

