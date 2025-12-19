import http from './http';

/**
 * 标签/领域树 API
 * 兼容 Django 后端的数据格式和返回结果
 */

// 获取标签树
export function fetchTags(projectId) {
  return http.get(`/projects/${projectId}/tags/`);
}

// 创建或更新标签
// 如果 tags.id 为 null 或空，则创建新标签；否则更新标签
export function saveTag(projectId, tagData) {
  return http.put(`/projects/${projectId}/tags/`, { tags: tagData });
}

// 删除标签
export function deleteTag(projectId, tagId) {
  return http.delete(`/projects/${projectId}/tags/`, {
    params: { id: tagId },
  });
}

// 根据标签名获取问题列表
export function getQuestionsByTagName(projectId, tagName) {
  return http.post(`/projects/${projectId}/tags/`, { tagName });
}

