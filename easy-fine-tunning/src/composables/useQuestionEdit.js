import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { createQuestion, updateQuestion } from '@/api/question';

/**
 * 问题编辑 Composable
 */
export function useQuestionEdit(projectId, onSuccess) {
  const { t } = useI18n();
  const editDialogOpen = ref(false);
  const editMode = ref('create');
  const editingQuestion = ref(null);

  const handleOpenCreateDialog = () => {
    editMode.value = 'create';
    editingQuestion.value = null;
    editDialogOpen.value = true;
  };

  const handleOpenEditDialog = (question) => {
    editMode.value = 'edit';
    editingQuestion.value = question;
    editDialogOpen.value = true;
  };

  const handleCloseDialog = () => {
    editDialogOpen.value = false;
    editingQuestion.value = null;
  };

  const handleSubmitQuestion = async (formData) => {
    try {
      const isCreate = editMode.value === 'create';

      // 构建请求数据，只包含有效值
      const payload = {
        question: formData.question,
        label: formData.label || ''
      };

      // 根据数据源类型添加相应的字段
      if (formData.sourceType === 'text') {
        if (!formData.chunkId) {
          throw new Error(t('questions.chunkIdRequired') || '文本块ID不能为空');
        }
        payload.chunk_id = formData.chunkId;
      } else if (formData.sourceType === 'image') {
        if (!formData.imageId) {
          throw new Error(t('questions.imageIdRequired') || '图片ID不能为空');
        }
        payload.image_id = formData.imageId;
        if (formData.imageName) {
          payload.image_name = formData.imageName;
        }
      }

      // 可选字段
      if (formData.gaPairId) {
        payload.ga_pair_id = formData.gaPairId;
      }
      if (formData.templateId) {
        payload.template_id = formData.templateId;
      }

      let updatedQuestion;
      if (isCreate) {
        updatedQuestion = await createQuestion(projectId, payload);
      } else {
        updatedQuestion = await updateQuestion(projectId, formData.id, payload);
      }

      // 处理响应数据
      const data = updatedQuestion?.data || updatedQuestion;

      if (onSuccess) {
        onSuccess(data);
      }
      handleCloseDialog();
      ElMessage.success(t('questions.operationSuccess') || '操作成功');
    } catch (error) {
      console.error('操作失败:', error);
      const errorMessage = error.message || t('questions.operationFailed') || '操作失败';
      ElMessage.error(errorMessage);
      throw error;
    }
  };

  return {
    editDialogOpen,
    editMode,
    editingQuestion,
    handleOpenCreateDialog,
    handleOpenEditDialog,
    handleCloseDialog,
    handleSubmitQuestion
  };
}

