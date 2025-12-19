import http from './http';

// 获取文本块列表
export function fetchChunks(projectId, params = {}) {
  return http.get(`/projects/${projectId}/split/`, { params });
}

// 分割文件（传入已上传的文件名列表）
export function splitFiles(projectId, payload) {
  return http.post(`/projects/${projectId}/split/`, payload, {
    timeout: 300000, // 分割可能耗时较长
  });
}

// 删除单个文本块
export function deleteChunk(projectId, chunkId) {
  return http.delete(`/projects/${projectId}/chunks/${chunkId}/`);
}


