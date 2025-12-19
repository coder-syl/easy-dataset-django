import http from './http';

// 获取蒸馏标签（全部树形标签，带统计信息）
export function fetchAllDistillTags(projectId) {
  return http.get(`/projects/${projectId}/distill/tags/all/`);
}

// 获取蒸馏标签（简单列表）
export function fetchDistillTags(projectId) {
  return http.get(`/projects/${projectId}/distill/tags/`);
}

// 为某个父标签生成子标签
export function generateDistillTags(projectId, payload) {
  return http.post(`/projects/${projectId}/distill/tags/`, payload, {
    timeout: 300000,
  });
}

// 为某个标签路径生成问题
export function generateDistillQuestions(projectId, payload) {
  return http.post(`/projects/${projectId}/distill/questions/`, payload, {
    timeout: 300000,
  });
}

// 根据标签 ID 获取已生成的问题列表
export function fetchDistillQuestionsByTag(projectId, tagId) {
  return http.get(`/projects/${projectId}/distill/questions/by-tag/`, {
    params: { tagId },
  });
}


