import http from './http';

// 发送聊天消息（普通模式）
export function sendChatMessage(projectId, payload) {
  if (projectId) {
    return http.post(`/projects/${projectId}/playground/chat/`, payload);
  }
  // 全局不绑定项目的接口
  return http.post('/llm/playground/chat/', payload);
}

// 发送聊天消息（流式模式）
export async function sendChatMessageStream(projectId, payload, onChunk) {
  // 使用与 http 实例相同的 baseURL 配置
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api';
  // 确保 baseURL 不以斜杠结尾，路径以斜杠开头
  const cleanBaseURL = baseURL.endsWith('/') ? baseURL.slice(0, -1) : baseURL;
  const url = projectId
    ? `${cleanBaseURL}/projects/${projectId}/playground/chat/stream/`
    : `${cleanBaseURL}/llm/playground/chat/stream/`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
  }

  if (!response.body) {
    throw new Error('Response body is null');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      if (onChunk && chunk) {
        onChunk(chunk);
      }
    }
  } finally {
    reader.releaseLock();
  }
}

