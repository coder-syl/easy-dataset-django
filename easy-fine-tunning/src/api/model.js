import http from './http';

// 全局模型列表（对应 Django /api/llm/model/）
export function fetchGlobalModels(params = {}) {
  return http.get('/llm/model/', { params });
}

// 同步模型列表到数据库
export function syncModels(payload) {
  return http.post('/llm/model/', payload);
}

// 全局模型配置接口（不再传 projectId）
export function fetchModelConfigs() {
  return http.get('/llm/model-config/');
}

export function saveModelConfig(payload) {
  return http.post('/llm/model-config/', payload);
}

export function updateModelConfig(modelConfigId, payload) {
  return http.put(`/llm/model-config/${modelConfigId}/`, payload);
}

export function deleteModelConfig(modelConfigId) {
  return http.delete(`/llm/model-config/${modelConfigId}/`);
}

export function fetchModelConfigDetail(modelConfigId) {
  return http.get(`/llm/model-config/${modelConfigId}/`);
}

// 兼容旧接口（短期保留）
export function fetchProjectModelConfigs(/* projectId */) {
  return fetchModelConfigs();
}

export function saveProjectModelConfig(/* projectId, */ payload) {
  return saveModelConfig(payload);
}

export function updateProjectModelConfig(/* projectId, */ modelConfigId, payload) {
  return updateModelConfig(modelConfigId, payload);
}

export function deleteProjectModelConfig(/* projectId, */ modelConfigId) {
  return deleteModelConfig(modelConfigId);
}

// 获取 LLM 提供商列表
export function fetchProviders() {
  return http.get('/llm/providers/');
}

// 获取 Ollama 模型列表
export function fetchOllamaModels(endpoint = 'http://127.0.0.1:11434') {
  return http.get('/llm/ollama/models/', { params: { endpoint } });
}

// 从提供商获取最新模型列表（需要后端代理）
export function fetchModelsFromProvider(payload) {
  return http.post('/llm/fetch-models/', payload);
}


