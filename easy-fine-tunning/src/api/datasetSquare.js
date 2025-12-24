import http from './http';

// 获取站点列表，支持 params: { page, page_size, q, category }
export function fetchSites(params = {}) {
  return http.get('/dataset_square/sites/', { params });
}

// 获取单个站点详情
export function fetchSiteDetail(id) {
  return http.get(`/dataset_square/sites/${id}/`);
}


