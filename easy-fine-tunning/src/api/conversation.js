import http from './http';

/**
 * 多轮对话数据集 API（兼容 Django 后端）
 */

// 获取多轮对话列表
export function fetchConversations(projectId, params = {}) {
  return http.get(`/projects/${projectId}/dataset-conversations/`, { params });
}

// 获取所有对话 ID（用于全选）
export function fetchAllConversationIds(projectId, params = {}) {
  return http.get(`/projects/${projectId}/dataset-conversations/`, {
    params: { ...params, getAllIds: 'true' }
  });
}

// 获取对话详情
export function fetchConversationDetail(projectId, conversationId, config = {}) {
  return http.get(`/projects/${projectId}/dataset-conversations/${conversationId}/`, config);
}

// 创建多轮对话（可能需要较长时间，使用 5 分钟超时）
export function createConversation(projectId, payload) {
  return http.post(`/projects/${projectId}/dataset-conversations/`, payload, {
    timeout: 300000 // 5分钟
  });
}

// 更新对话
export function updateConversation(projectId, conversationId, payload) {
  return http.put(`/projects/${projectId}/dataset-conversations/${conversationId}/`, payload);
}

// 删除对话
export function deleteConversation(projectId, conversationId) {
  return http.delete(`/projects/${projectId}/dataset-conversations/${conversationId}/`);
}

// 导出多轮对话
export function exportConversations(projectId, payload = {}) {
  return http.post(`/projects/${projectId}/dataset-conversations/export/`, payload);
}

// Evaluation endpoints
export function evaluateConversation(projectId, conversationId, payload = {}) {
  return http.post(`/projects/${projectId}/dataset-conversations/${conversationId}/evaluate/`, payload);
}

export function batchEvaluateConversations(projectId, payload = {}) {
  return http.post(`/projects/${projectId}/dataset-conversations/batch-evaluate/`, payload);
}
