import http from './http';

/**
 * 数据集 API
 * 兼容 Django 后端的数据格式和返回结果
 */

// 获取数据集列表
export function fetchDatasets(projectId, params = {}) {
  return http.get(`/projects/${projectId}/datasets/`, { params });
}

// 获取所有数据集 ID（用于全选）
export function fetchAllDatasetIds(projectId, params = {}) {
  return http.get(`/projects/${projectId}/datasets/`, {
    params: { ...params, getAllIds: 'true' }
  });
}

// 获取数据集详情
export function fetchDatasetDetail(projectId, datasetId, params = {}) {
  // axios 会自动处理URL编码，所以直接使用 datasetId 即可
  const id = String(datasetId);
  console.log('[fetchDatasetDetail] 请求参数:', { projectId, datasetId: id });
  return http.get(`/projects/${projectId}/datasets/${id}/`, { params });
}

// 创建数据集（生成答案）
// 数据集生成可能需要较长时间，使用更长的超时时间（5分钟）
export function generateDataset(projectId, payload) {
  return http.post(`/projects/${projectId}/datasets/`, payload, {
    timeout: 300000 // 5分钟
  });
}

// 更新数据集
export function updateDataset(projectId, datasetId, payload) {
  return http.patch(`/projects/${projectId}/datasets/${datasetId}/`, payload);
}

// 删除数据集
export function deleteDataset(projectId, datasetId) {
  return http.delete(`/projects/${projectId}/datasets/${datasetId}/`);
}

// 评估数据集（可能需要较长时间，使用 3 分钟超时）
export function evaluateDataset(projectId, datasetId, payload) {
  return http.post(`/projects/${projectId}/datasets/${datasetId}/evaluate/`, payload, {
    timeout: 180000 // 3分钟
  });
}

// 批量评估数据集（可能需要较长时间，使用 5 分钟超时）
export function batchEvaluateDatasets(projectId, payload) {
  return http.post(`/projects/${projectId}/datasets/batch-evaluate/`, payload, {
    timeout: 300000 // 5分钟
  });
}

// 优化数据集（可能需要较长时间，使用 3 分钟超时）
export function optimizeDataset(projectId, payload) {
  return http.post(`/projects/${projectId}/datasets/optimize/`, payload, {
    timeout: 180000 // 3分钟
  });
}

// 获取数据集 Token 统计
export function fetchDatasetTokenCount(projectId, datasetId) {
  return http.get(`/projects/${projectId}/datasets/${datasetId}/token-count/`);
}

// 导出数据集
export function exportDatasets(projectId, payload) {
  return http.post(`/projects/${projectId}/datasets/export/`, payload);
}

// 获取标签统计
export function fetchTagStatistics(projectId, params = {}) {
  return http.get(`/projects/${projectId}/datasets/export/`, { params });
}

// 导入数据集
export function importDatasets(projectId, payload) {
  return http.post(`/projects/${projectId}/datasets/import/`, payload);
}

// 获取数据集标签列表
export function fetchDatasetTags(projectId) {
  return http.get(`/projects/${projectId}/datasets/tags/`);
}

