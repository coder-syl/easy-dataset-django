import http from './http';

// 获取自定义提示词列表
export function fetchCustomPrompts(projectId, params = {}) {
  return http.get(`/projects/${projectId}/custom-prompts/`, { params });
}

// 保存自定义提示词
export function saveCustomPrompt(projectId, payload) {
  return http.post(`/projects/${projectId}/custom-prompts/`, payload);
}

// 删除自定义提示词（恢复默认）
export function deleteCustomPrompt(projectId, params = {}) {
  return http.delete(`/projects/${projectId}/custom-prompts/`, { params });
}

// 获取默认提示词
export function fetchDefaultPrompt(projectId, params = {}) {
  return http.get(`/projects/${projectId}/default-prompts/`, { params });
}

