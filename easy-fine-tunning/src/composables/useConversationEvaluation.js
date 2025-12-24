import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useI18n } from 'vue-i18n';
import { evaluateConversation, batchEvaluateConversations } from '@/api/conversation';
import { useModelStore } from '@/stores/model';

export function useConversationEvaluation(projectIdRef, onComplete) {
  const { t } = useI18n();
  const modelStore = useModelStore();
  const evaluatingIds = ref([]);
  const batchEvaluating = ref(false);

  const checkModelConfiguration = () => {
    const selectedModel = modelStore.selectedModelInfo;
    if (!selectedModel || !selectedModel.modelName) {
      ElMessage.error(t('datasets.selectModelFirst', '请先选择模型'));
      return false;
    }
    return true;
  };

  const handleEvaluateConversation = async (conversation) => {
    if (!checkModelConfiguration()) return;
    try {
      evaluatingIds.value.push(conversation.id);
      const model = {
        modelName: modelStore.selectedModelInfo.modelName,
        ...modelStore.selectedModelInfo
      };
      const projectId = typeof projectIdRef === 'string' ? projectIdRef : projectIdRef.value;
      const result = await evaluateConversation(projectId, conversation.id, { model, language: 'zh-CN' });
      if (result?.success || result?.data) {
        const data = result.data || result;
        ElMessage.success(`${t('datasets.evaluateSuccess', '评估完成！评分')}：${data.score || 0}/5`);
        if (onComplete) onComplete(true);
      } else {
        ElMessage.error(result?.message || t('datasets.evaluateFailed', '评估失败'));
      }
    } catch (error) {
      console.error('评估失败', error);
      ElMessage.error(error.message || t('datasets.evaluateError', '评估失败'));
    } finally {
      evaluatingIds.value = evaluatingIds.value.filter((id) => id !== conversation.id);
    }
  };

  const handleBatchEvaluate = async (conversationIds = []) => {
    if (!checkModelConfiguration()) return;
    try {
      batchEvaluating.value = true;
      const model = {
        modelName: modelStore.selectedModelInfo.modelName,
        ...modelStore.selectedModelInfo
      };
      const projectId = typeof projectIdRef === 'string' ? projectIdRef : projectIdRef.value;
      const resp = await batchEvaluateConversations(projectId, { conversationIds, model, language: 'zh-CN' });
      if (resp?.success || resp?.data) {
        ElMessage.success(t('datasets.batchEvaluateStarted', '批量评估任务已启动，将在后台进行处理'));
      } else {
        ElMessage.error(resp?.message || t('datasets.batchEvaluateFailed', '批量评估失败'));
      }
    } catch (error) {
      console.error('批量评估失败', error);
      ElMessage.error(error.message || t('datasets.batchEvaluateFailed', '批量评估失败'));
    } finally {
      batchEvaluating.value = false;
    }
  };

  return {
    evaluatingIds,
    batchEvaluating,
    handleEvaluateConversation,
    handleBatchEvaluate
  };
}


