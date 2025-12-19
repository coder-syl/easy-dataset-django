import http from './http';

// 为单个文本块生成问题
export function generateQuestionsForChunk(projectId, chunkId, payload) {
  return http.post(`/projects/${projectId}/chunks/${chunkId}/questions/`, payload, {
    timeout: 300000, // 生成问题可能较慢
  });
}

// 清洗单个文本块
export function cleanChunk(projectId, chunkId, payload) {
  return http.post(`/projects/${projectId}/chunks/${chunkId}/clean/`, payload, {
    timeout: 300000, // 清洗可能较慢
  });
}


