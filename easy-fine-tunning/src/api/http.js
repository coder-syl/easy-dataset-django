import axios from 'axios';
import { ElMessage } from 'element-plus';

const http = axios.create({
  // 通过 VITE_API_BASE_URL 指向 Django，例如 http://localhost:8000/api
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  // 增加超时时间到 2 分钟（120000ms），因为数据集生成、评估等操作可能需要较长时间
  timeout: 120000,
  withCredentials: false,
});

http.interceptors.request.use(
  (config) => {
    // TODO: 如有登录鉴权，这里注入 token/cookie 等
    
    // 如果数据是 FormData，确保不手动设置 Content-Type
    // 让浏览器自动设置 multipart/form-data 和 boundary
    if (config.data instanceof FormData) {
      // 删除手动设置的 Content-Type，让 axios 自动处理
      if (config.headers) {
        delete config.headers['Content-Type'];
        delete config.headers['content-type'];
      }
    }
    
    return config;
  },
  (error) => Promise.reject(error),
);

http.interceptors.response.use(
  (response) => {
    const res = response.data;
    // 兼容 Django 的统一返回结构 { code, message, data }
    if (res && typeof res.code !== 'undefined') {
      if (res.code !== 0) {
        ElMessage.error(res.message || 'Request error');
        return Promise.reject(new Error(res.message || 'Request error'));
      }
      return res.data;
    }
    return res;
  },
  (error) => {
    // 对于 404/500 等错误，从响应体中提取消息，但不自动显示错误提示
    // 让调用方自己决定如何处理错误
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.error ||
      error.message ||
      'Request error';
    
    // 只有非业务错误（网络错误等）才自动显示提示
    // 业务错误（如数据集不存在）由调用方处理
    if (!error?.response) {
      ElMessage.error(message);
    }
    
    return Promise.reject(error);
  },
);

export default http;

