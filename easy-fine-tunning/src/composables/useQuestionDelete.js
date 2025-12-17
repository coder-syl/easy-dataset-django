import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage, ElMessageBox } from 'element-plus';
import { deleteQuestion, batchDeleteQuestions } from '@/api/question';

/**
 * 问题删除 Composable
 */
export function useQuestionDelete(projectId, onDeleteSuccess) {
  const { t } = useI18n();

  // 确认对话框状态
  const confirmDialog = ref({
    open: false,
    title: '',
    content: '',
    confirmAction: null
  });

  // 执行单个问题删除
  const executeDeleteQuestion = async (questionId, selectedQuestions, setSelectedQuestions) => {
    try {
      await deleteQuestion(projectId, questionId);
      // 更新选中状态
      if (setSelectedQuestions) {
        setSelectedQuestions((prev) => (prev.includes(questionId) ? prev.filter((id) => id !== questionId) : prev));
      }
      // 调用成功回调
      if (onDeleteSuccess) {
        onDeleteSuccess();
      }
      ElMessage.success(t('common.deleteSuccess') || '删除成功');
    } catch (error) {
      console.error('删除失败:', error);
      ElMessage.error(error.message || '删除失败');
    }
  };

  // 确认删除单个问题
  const confirmDeleteQuestion = (questionId, selectedQuestions, setSelectedQuestions) => {
    confirmDialog.value = {
      open: true,
      title: t('common.confirmDelete') || '确认删除',
      content: t('common.confirmDeleteQuestion') || '确定要删除这个问题吗？',
      confirmAction: () => executeDeleteQuestion(questionId, selectedQuestions, setSelectedQuestions)
    };
  };

  // 处理删除单个问题的入口函数
  const handleDeleteQuestion = (questionId, selectedQuestions, setSelectedQuestions) => {
    confirmDeleteQuestion(questionId, selectedQuestions, setSelectedQuestions);
  };

  // 执行批量删除问题
  const executeBatchDeleteQuestions = async (selectedQuestions, setSelectedQuestions) => {
    try {
      await batchDeleteQuestions(projectId, selectedQuestions);
      // 调用成功回调
      if (onDeleteSuccess) {
        onDeleteSuccess();
      }
      // 清空选中状态
      if (setSelectedQuestions) {
        setSelectedQuestions([]);
      }
      ElMessage.success(`成功删除 ${selectedQuestions.length} 个问题`);
    } catch (error) {
      console.error('批量删除失败:', error);
      ElMessage.error(error.message || '批量删除问题失败');
    }
  };

  // 确认批量删除问题
  const confirmBatchDeleteQuestions = (selectedQuestions, setSelectedQuestions) => {
    if (selectedQuestions.length === 0) {
      ElMessage.warning('请先选择问题');
      return;
    }

    confirmDialog.value = {
      open: true,
      title: '确认批量删除问题',
      content: `您确定要删除选中的 ${selectedQuestions.length} 个问题吗？此操作不可恢复。`,
      confirmAction: () => executeBatchDeleteQuestions(selectedQuestions, setSelectedQuestions)
    };
  };

  // 处理批量删除问题的入口函数
  const handleBatchDeleteQuestions = (selectedQuestions, setSelectedQuestions) => {
    confirmBatchDeleteQuestions(selectedQuestions, setSelectedQuestions);
  };

  // 关闭确认对话框
  const closeConfirmDialog = () => {
    confirmDialog.value = {
      open: false,
      title: '',
      content: '',
      confirmAction: null
    };
  };

  // 确认对话框的确认操作
  const handleConfirmAction = () => {
    if (confirmDialog.value.confirmAction) {
      confirmDialog.value.confirmAction();
    }
    closeConfirmDialog();
  };

  return {
    // 状态
    confirmDialog,

    // 方法
    handleDeleteQuestion,
    handleBatchDeleteQuestions,
    closeConfirmDialog,
    handleConfirmAction
  };
}

