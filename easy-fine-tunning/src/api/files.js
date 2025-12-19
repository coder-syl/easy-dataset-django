import http from './http';

// 获取文件列表
export function fetchFiles(projectId, params = {}) {
  return http.get(`/projects/${projectId}/files/`, { params });
}

// 删除文件（附带领域树处理策略）
export function deleteFile(projectId, fileId, domainTreeAction = 'keep') {
  return http.delete(`/projects/${projectId}/files/`, {
    params: { fileId, domainTreeAction },
  });
}

// 上传文件（使用原生 fetch 发送二进制，兼容 Django 的 request.body 读取）
export async function uploadFile(projectId, file) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api';
  const url = `${baseURL}/projects/${projectId}/files/`;

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/octet-stream',
      'x-file-name': encodeURIComponent(file.name),
    },
    body: file,
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok || (data && typeof data.code !== 'undefined' && data.code !== 0)) {
    const msg =
      data?.message ||
      data?.error ||
      (Array.isArray(data?.errors) ? data.errors.join(', ') : '') ||
      'File upload failed';
    throw new Error(msg);
  }

  // HTTP 拦截器不会处理这里的 fetch 结果，因此直接返回 data.data 或 data
  return data?.data || data;
}


