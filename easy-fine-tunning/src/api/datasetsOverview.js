import http from './http';

export function fetchDatasetsOverview(projectId) {
  return http.get(`/projects/${projectId}/datasets-overview/`);
}

export function exportCombinedDatasets(projectId, payload = {}) {
  // payload: { types: ['single','multi','image'], format: 'jsonl', confirmed: true/false, selectedIds: {single:[],...} }
  return http.request({
    url: `/projects/${projectId}/datasets-export/`,
    method: 'POST',
    data: payload,
    responseType: 'blob',
  });
}

export function exportCombinedDatasetsJSON(projectId, payload = {}) {
  return http.request({
    url: `/projects/${projectId}/datasets-export/`,
    method: 'POST',
    data: payload,
    // no responseType so axios will parse JSON
  });
}


