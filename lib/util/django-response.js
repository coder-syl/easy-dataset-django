/**
 * Django 响应格式处理工具
 * Django 返回格式: {code, message, data}
 * 此工具函数用于提取 data 字段，兼容不同的响应格式
 */

/**
 * 从 Django 响应中提取数据
 * @param {Object|Array} response - Django 响应对象或直接的数据
 * @returns {*} 提取的数据
 */
export function extractDjangoData(response) {
  // 如果 response 是数组，直接返回
  if (Array.isArray(response)) {
    return response;
  }
  
  // 如果 response 有 data 字段，返回 data
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data;
  }
  
  // 否则返回原响应
  return response;
}

/**
 * 从 Django 响应中提取数组数据，确保返回数组
 * @param {Object|Array} response - Django 响应对象或直接的数据
 * @returns {Array} 数组数据
 */
export function extractDjangoArray(response) {
  const data = extractDjangoData(response);
  return Array.isArray(data) ? data : [];
}

/**
 * 检查 Django 响应是否成功
 * @param {Object} response - Django 响应对象
 * @returns {boolean} 是否成功
 */
export function isDjangoSuccess(response) {
  if (Array.isArray(response)) return true;
  if (response && typeof response === 'object') {
    return response.code === 0 || response.code === 200 || response.code === 201;
  }
  return false;
}

