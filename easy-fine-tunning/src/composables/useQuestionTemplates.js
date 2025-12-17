import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import http from '@/api/http';

/**
 * 问题模板管理 Composable
 */
export function useQuestionTemplates(projectId, templateType = null) {
  const templates = ref([]);
  const templatesLoading = ref(false);

  // 获取模板列表
  const fetchTemplates = async () => {
    try {
      templatesLoading.value = true;
      const params = templateType ? { type: templateType } : {};
      const response = await http.get(`/projects/${projectId}/questions/templates/`, { params });
      const data = response?.data || response || [];
      // 确保返回的是数组
      templates.value = Array.isArray(data) ? data : Array.isArray(data?.data) ? data.data : [];
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
    try {
      await http.post(`/projects/${projectId}/questions/templates/`, data);
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
    try {
      await http.put(`/projects/${projectId}/questions/templates/${templateId}/`, data);
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
    try {
      await http.delete(`/projects/${projectId}/questions/templates/${templateId}/`);
      await fetchTemplates();
      ElMessage.success('删除模板成功');
    } catch (error) {
      console.error('删除模板失败:', error);
      ElMessage.error('删除模板失败');
      throw error;
    }
  };

  onMounted(() => {
    fetchTemplates();
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

