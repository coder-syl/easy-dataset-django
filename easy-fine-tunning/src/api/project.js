import http from './http';

// 创建项目，支持复用已有项目的模型配置
export function createProject(payload) {
  return http.post('/projects/', payload);
}

// 获取项目列表
export function fetchProjects(params = {}) {
  return http.get('/projects/', { params });
}

// 获取项目详情
export function fetchProjectDetail(projectId) {
  return http.get(`/projects/${projectId}/`);
}

// 更新项目
export function updateProject(projectId, payload) {
  return http.put(`/projects/${projectId}/`, payload);
}

// 删除项目
export function deleteProject(projectId) {
  return http.delete(`/projects/${projectId}/`);
}

