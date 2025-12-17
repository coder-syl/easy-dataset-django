import http from './http';

// 获取任务配置
export function fetchTaskSettings(projectId) {
  return http.get(`/projects/${projectId}/tasks/`);
}

// 更新任务配置
export function updateTaskSettings(projectId, payload) {
  return http.put(`/projects/${projectId}/tasks/`, payload);
}

// 创建任务
export function createTask(projectId, payload) {
  return http.post(`/projects/${projectId}/tasks/`, payload);
}

// 获取任务列表
export function fetchTaskList(projectId, params = {}) {
  return http.get(`/projects/${projectId}/tasks/list/`, { params });
}

// 获取任务详情
export function fetchTaskDetail(projectId, taskId) {
  return http.get(`/projects/${projectId}/tasks/${taskId}/`);
}

// 更新任务
export function updateTask(projectId, taskId, payload) {
  return http.put(`/projects/${projectId}/tasks/${taskId}/`, payload);
}

// 删除任务
export function deleteTask(projectId, taskId) {
  return http.delete(`/projects/${projectId}/tasks/${taskId}/`);
}

