# 流式响应功能实现说明

## ✅ 已完成

### 1. LLM流式服务 (`common/services/llm_streaming.py`)
- ✅ 创建了专门的流式响应服务类 `LLMStreamingService`
- ✅ 支持Server-Sent Events (SSE)格式
- ✅ 支持OpenAI兼容格式的流式响应
- ✅ 支持Ollama格式的流式响应
- ✅ 处理思维链（COT）的流式输出
- ✅ 错误处理和重试机制

### 2. Playground流式聊天 (`llm/playground_views.py`)
- ✅ 实现了`playground_chat_stream`视图
- ✅ 集成流式服务
- ✅ 返回SSE格式的流式响应
- ✅ 支持多种模型提供商

### 3. LLM服务流式方法 (`common/services/llm_service.py`)
- ✅ 实现了`stream_chat`方法
- ✅ 支持LangChain模型实例的流式调用
- ✅ 支持HTTP API的流式调用
- ✅ 处理思维链和正文内容的分离

### 4. 流式响应工具函数 (`common/services/llm_streaming.py`)
- ✅ `create_streaming_response` - 创建Django流式HTTP响应
- ✅ 配置正确的HTTP头（Cache-Control, Connection等）

## 📝 使用说明

### Playground流式聊天

**API端点**: `POST /api/projects/{projectId}/playground/chat/stream/`

**请求体**:
```json
{
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "model": {
    "providerId": "openai",
    "endpoint": "https://api.openai.com/v1",
    "apiKey": "sk-...",
    "modelId": "gpt-3.5-turbo"
  },
  "temperature": 0.7,
  "maxTokens": 8192
}
```

**响应格式**: Server-Sent Events (SSE)
```
data: {"type": "content", "content": "你好"}

data: {"type": "content", "content": "！"}

data: {"type": "reasoning", "content": "<think>"}

data: {"type": "reasoning", "content": "用户问候"}

data: [DONE]
```

### 前端使用示例

```javascript
const eventSource = new EventSource('/api/projects/xxx/playground/chat/stream/', {
  method: 'POST',
  body: JSON.stringify({
    messages: [{ role: 'user', content: '你好' }],
    model: { ... }
  })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'content') {
    // 追加正文内容
    appendContent(data.content);
  } else if (data.type === 'reasoning') {
    // 处理思维链
    if (data.content === '<think>') {
      startReasoning();
    } else if (data.content === '</think>') {
      endReasoning();
    } else {
      appendReasoning(data.content);
    }
  } else if (event.data === '[DONE]') {
    eventSource.close();
  }
};
```

## 🔧 技术细节

### SSE格式
- 每行以`data: `开头
- 数据为JSON格式
- 流结束标记为`data: [DONE]`
- 空行分隔不同事件

### 思维链处理
- 使用`<think>`和`</think>`标签包裹思维链内容
- 思维链和正文内容分别发送
- 前端可以根据类型分别处理

### 错误处理
- 流式过程中发生错误，会发送错误信息
- 格式：`data: {"error": "错误信息"}`
- 然后发送`data: [DONE]`结束流

## ⚙️ 配置说明

### HTTP头配置
- `Content-Type: text/event-stream` - SSE格式
- `Cache-Control: no-cache` - 禁用缓存
- `Connection: keep-alive` - 保持连接
- `X-Accel-Buffering: no` - 禁用Nginx缓冲

### 超时设置
- 默认超时：60秒
- 可在请求中通过`timeout`参数自定义

## 🚀 后续优化

- [ ] 支持更多模型提供商的流式格式
- [ ] 添加流式响应的压缩支持
- [ ] 实现流式响应的断点续传
- [ ] 添加流式响应的监控和统计
- [ ] 优化大模型的流式性能

