import http from './http';

// 图片列表 & 导入 & 删除
export function fetchImages(projectId, params = {}) {
  return http.get(`/projects/${projectId}/images/`, { params });
}

export function importImagesFromDirectories(projectId, directories) {
  return http.post(`/projects/${projectId}/images/`, { directories });
}

// ZIP 导入（表单上传）
// 注意：不要手动设置 Content-Type，让浏览器自动设置 multipart/form-data 和 boundary
export function importImagesFromZip(projectId, formData) {
  return http.post(`/projects/${projectId}/images/zip-import/`, formData, {
    // 不设置 Content-Type，让 axios 自动处理 FormData
    // axios 会自动设置正确的 Content-Type: multipart/form-data; boundary=...
  });
}

// PDF 转图片（表单上传）
// 注意：不要手动设置 Content-Type，让浏览器自动设置 multipart/form-data 和 boundary
export function importImagesFromPdf(projectId, formData) {
  return http.post(`/projects/${projectId}/images/pdf-convert/`, formData, {
    // 不设置 Content-Type，让 axios 自动处理 FormData
    // axios 会自动设置正确的 Content-Type: multipart/form-data; boundary=...
  });
}

// 单图上传（原始二进制，携带 x-file-name 头）
export function uploadSingleImage(projectId, file, fileName) {
  return http.post(`/projects/${projectId}/images/upload/`, file, {
    headers: {
      'Content-Type': 'application/octet-stream',
      'x-file-name': fileName || file.name,
    },
  });
}

// 获取图片详情（包含已回答 / 未回答问题等）
export function fetchImageDetail(projectId, imageId) {
  return http.get(`/projects/${projectId}/images/${imageId}/`);
}

// 获取下一个有未回答问题的图片
export function fetchNextUnansweredImage(projectId) {
  return http.get(`/projects/${projectId}/images/next-unanswered/`);
}

// 生成图像问题
export function generateImageQuestions(projectId, payload) {
  return http.post(`/projects/${projectId}/images/questions/`, payload);
}

// 生成图像数据集
export function generateImageDataset(projectId, payload) {
  return http.post(`/projects/${projectId}/images/datasets/`, payload);
}

// 保存图像标注（当前 Django 版本的实现是写入 Image.note）
export function saveImageAnnotation(projectId, payload) {
  return http.post(`/projects/${projectId}/images/annotations/`, payload);
}

// 更新图像元信息
export function updateImage(projectId, imageId, payload) {
  return http.put(`/projects/${projectId}/images/${imageId}/update/`, payload);
}

// 删除图片
export function deleteImage(projectId, imageId) {
  return http.delete(`/projects/${projectId}/images/`, {
    params: { imageId },
  });
}


