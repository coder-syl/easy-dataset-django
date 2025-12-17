import http from './http';

/**
 * 问题管理 API
 * 兼容 Django 后端的数据格式和返回结果
 */

// 获取问题列表
export function fetchQuestions(projectId, params = {}) {
  return http.get(`/projects/${projectId}/questions/`, { params });
}

// 获取问题详情
export function fetchQuestionDetail(projectId, questionId) {
  return http.get(`/projects/${projectId}/questions/${questionId}/`);
}

// 创建问题
export function createQuestion(projectId, payload) {
  return http.post(`/projects/${projectId}/questions/`, payload);
}

// 更新问题
export function updateQuestion(projectId, questionId, payload) {
  return http.patch(`/projects/${projectId}/questions/${questionId}/`, payload);
}

// 删除问题
export function deleteQuestion(projectId, questionId) {
  return http.delete(`/projects/${projectId}/questions/${questionId}/`);
}

// 批量删除问题
export function batchDeleteQuestions(projectId, questionIds) {
  return http.delete(`/projects/${projectId}/questions/batch-delete/`, {
    data: { questionIds }
  });
}

// 获取问题树
export function fetchQuestionTree(projectId) {
  return http.get(`/projects/${projectId}/questions/tree/`);
}

// 获取标签列表
export function fetchTags(projectId) {
  return http.get(`/projects/${projectId}/tags/`);
}

