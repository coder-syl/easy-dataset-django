import { ref, onMounted, unref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import http from '@/api/http';

/**
 * 问题模板管理 Composable
 */
export function useQuestionTemplates(projectId, templateType = null) {
  const templates = ref([]);
  const templatesLoading = ref(false);

  // 确保 projectId 是响应式的，并获取实际值
  const projectIdValue = computed(() => {
    const value = unref(projectId);
    return typeof value === 'string' || typeof value === 'number' ? String(value) : null;
  });

  // 获取模板列表
  const fetchTemplates = async () => {
    const pid = projectIdValue.value;
    if (!pid) {
      console.warn('projectId is not available');
      return;
    }

    try {
      templatesLoading.value = true;
      const params = templateType ? { type: templateType } : {};
      const response = await http.get(`/projects/${pid}/questions/templates/`, { params });
      // Django 返回格式为 { success: true, templates: [...] }
      // 也兼容 Node.js 可能返回的直接数组或 { data: [...] } 格式
      const data = response?.templates || response?.data || response || [];
      templates.value = Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('获取模板列表失败:', error);
      ElMessage.error('获取模板列表失败');
      templates.value = [];
    } finally {
      templatesLoading.value = false;
    }
  };

  // 创建模板
  const createTemplate = async (data) => {
    const pid = projectIdValue.value;
    if (!pid) {
      throw new Error('projectId is not available');
    }
    try {
      await http.post(`/projects/${pid}/questions/templates/`, data);
      await fetchTemplates();
      ElMessage.success('创建模板成功');
    } catch (error) {
      console.error('创建模板失败:', error);
      ElMessage.error('创建模板失败');
      throw error;
    }
  };

  // 更新模板
  const updateTemplate = async (templateId, data) => {
    const pid = projectIdValue.value;
    if (!pid) {
      throw new Error('projectId is not available');
    }
    try {
      await http.put(`/projects/${pid}/questions/templates/${templateId}/`, data);
      await fetchTemplates();
      ElMessage.success('更新模板成功');
    } catch (error) {
      console.error('更新模板失败:', error);
      ElMessage.error('更新模板失败');
      throw error;
    }
  };

  // 删除模板
  const deleteTemplate = async (templateId) => {
    const pid = projectIdValue.value;
    if (!pid) {
      throw new Error('projectId is not available');
    }
    try {
      await http.delete(`/projects/${pid}/questions/templates/${templateId}/`);
      await fetchTemplates();
      ElMessage.success('删除模板成功');
    } catch (error) {
      console.error('删除模板失败:', error);
      ElMessage.error('删除模板失败');
      throw error;
    }
  };

  onMounted(() => {
    if (projectIdValue.value) {
      fetchTemplates();
    }
  });

  return {
    templates,
    templatesLoading,
    fetchTemplates,
    createTemplate,
    updateTemplate,
    deleteTemplate
  };
}

