import http from './http';

/**
 * GA对 API
 * 兼容 Django 后端的数据格式和返回结果
 */

// 获取单个文件的GA对
export function fetchGaPairs(projectId, fileId) {
  return http.get(`/projects/${projectId}/files/${fileId}/ga-pairs/`);
}

// 为单个文件生成GA对
export function generateGaPairsForFile(projectId, fileId, payload) {
  return http.post(`/projects/${projectId}/files/${fileId}/ga-pairs/`, payload, {
    timeout: 300000, // 生成GA对可能较慢
  });
}

// 批量生成GA对
export function batchGenerateGaPairs(projectId, payload) {
  return http.post(`/projects/${projectId}/files/batch-generateGA/`, payload, {
    timeout: 600000, // 批量生成可能更慢
  });
}

// 更新单个GA对的激活状态
export function toggleGaPairActive(projectId, fileId, pairId, isActive) {
  return http.patch(`/projects/${projectId}/files/${fileId}/ga-pairs/`, {
    pairId,
    isActive,
  });
}

// 保存/更新GA对（覆盖或追加）
export function saveGaPairs(projectId, fileId, gaPairs, appendMode = false) {
  return http.put(`/projects/${projectId}/files/${fileId}/ga-pairs/`, {
    gaPairs,
    appendMode,
  });
}

