import http from './http';

// 图像数据集列表
export function fetchImageDatasets(projectId, params = {}) {
  return http.get(`/projects/${projectId}/image-datasets/`, { params });
}

// 图像数据集详情
export function fetchImageDatasetDetail(projectId, datasetId) {
  return http.get(`/projects/${projectId}/image-datasets/${datasetId}/`);
}

// 更新图像数据集
export function updateImageDataset(projectId, datasetId, payload) {
  return http.put(`/projects/${projectId}/image-datasets/${datasetId}/`, payload);
}

// 删除图像数据集
export function deleteImageDataset(projectId, datasetId) {
  return http.delete(`/projects/${projectId}/image-datasets/${datasetId}/`);
}

// 导出图像数据集（文本内容）
export function exportImageDatasets(projectId, payload) {
  return http.post(`/projects/${projectId}/image-datasets/export/`, payload);
}

// 获取图像数据集标签统计
export function fetchImageDatasetTags(projectId) {
  return http.get(`/projects/${projectId}/image-datasets/tags/`);
}

// 评估图像数据集（可能需要较长时间，使用 3 分钟超时）
export function evaluateImageDataset(projectId, datasetId, payload) {
  return http.post(`/projects/${projectId}/image-datasets/${datasetId}/evaluate/`, payload, {
    timeout: 180000 // 3分钟
  });
}

// 批量评估图像数据集（可能需要较长时间，使用 5 分钟超时）
export function batchEvaluateImageDatasets(projectId, payload) {
  return http.post(`/projects/${projectId}/image-datasets/batch-evaluate/`, payload, {
    timeout: 300000 // 5分钟
  });
}

