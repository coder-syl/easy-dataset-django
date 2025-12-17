import http from './http';

// 全局模型列表（对应 Django /api/llm/model/）
export function fetchGlobalModels(params = {}) {
  return http.get('/llm/model/', { params });
}

// 同步模型列表到数据库
export function syncModels(payload) {
  return http.post('/llm/model/', payload);
}

// 获取项目下的模型配置列表（/api/projects/<projectId>/model-config/）
export function fetchProjectModelConfigs(projectId) {
  return http.get(`/projects/${projectId}/model-config/`);
}

// 保存项目模型配置（新增/更新）
export function saveProjectModelConfig(projectId, payload) {
  return http.post(`/projects/${projectId}/model-config/`, payload);
}

// 更新项目模型配置
export function updateProjectModelConfig(projectId, modelConfigId, payload) {
  return http.put(`/projects/${projectId}/model-config/${modelConfigId}/`, payload);
}

// 删除项目模型配置
export function deleteProjectModelConfig(projectId, modelConfigId) {
  return http.delete(`/projects/${projectId}/model-config/${modelConfigId}/`);
}

// 获取模型配置详情
export function fetchModelConfigDetail(projectId, modelConfigId) {
  return http.get(`/projects/${projectId}/model-config/${modelConfigId}/`);
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


