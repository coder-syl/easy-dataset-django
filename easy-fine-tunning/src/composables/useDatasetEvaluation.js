import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { evaluateDataset, batchEvaluateDatasets } from '@/api/dataset';
import { useModelStore } from '@/stores/model';

/**
 * 数据集评估相关的 Composable
 * 封装单个评估和批量评估的逻辑
 */
export function useDatasetEvaluation(projectId, onEvaluationComplete) {
  const router = useRouter();
  const { t } = useI18n();
  const modelStore = useModelStore();

  // 评估状态管理
  const evaluatingIds = ref([]);
  const batchEvaluating = ref(false);

  /**
   * 检查模型是否已配置
   */
  const checkModelConfiguration = () => {
    const selectedModel = modelStore.selectedModelInfo;
    if (!selectedModel || !selectedModel.modelName) {
      ElMessage.error(t('datasets.selectModelFirst', '请先选择模型'));
      return false;
    }
    return true;
  };

  /**
   * 处理单个数据集评估
   */
  const handleEvaluateDataset = async (dataset) => {
    if (!checkModelConfiguration()) {
      return;
    }

    try {
      evaluatingIds.value.push(dataset.id);

      const model = {
        modelName: modelStore.selectedModelInfo.modelName,
        ...modelStore.selectedModelInfo
      };

      const result = await evaluateDataset(projectId, dataset.id, {
        model,
        language: 'zh-CN'
      });

      // Django 返回格式: {success: true, message: '...', data: {score: ..., aiEvaluation: ...}}
      if (result?.success || result?.data) {
        const data = result?.data || result;
        const score = data.score || 0;
        ElMessage.success(
          `${t('datasets.evaluateSuccess', '评估完成！评分')}：${score}/5`
        );

        if (onEvaluationComplete) {
          await new Promise((resolve) => setTimeout(resolve, 200));
          if (typeof onEvaluationComplete === 'function') {
            await onEvaluationComplete(true);
          } else {
            await onEvaluationComplete();
          }
        }
      } else {
        ElMessage.error(result?.message || t('datasets.evaluateFailed', '评估失败'));
      }
    } catch (error) {
      console.error('评估失败:', error);
      ElMessage.error(
        `${t('datasets.evaluateError', '评估失败')}: ${error.message || error}`
      );
    } finally {
      evaluatingIds.value = evaluatingIds.value.filter((id) => id !== dataset.id);
    }
  };

  /**
   * 处理批量评估
   */
  const handleBatchEvaluate = async () => {
    if (!checkModelConfiguration()) {
      return;
    }

    try {
      batchEvaluating.value = true;

      const model = {
        modelName: modelStore.selectedModelInfo.modelName,
        ...modelStore.selectedModelInfo
      };

      const result = await batchEvaluateDatasets(projectId, {
        model,
        language: 'zh-CN'
      });

      // Django 返回格式: {success: true, message: '...', data: {taskId: '...'}}
      if (result?.success || result?.data) {
        ElMessage.success(
          t('datasets.batchEvaluateStarted', '批量评估任务已启动，将在后台进行处理')
        );
        router.push(`/projects/${projectId}/tasks`);
      } else {
        ElMessage.error(
          result?.message || t('datasets.batchEvaluateStartFailed', '启动批量评估失败')
        );
      }
    } catch (error) {
      console.error('批量评估失败:', error);
      ElMessage.error(
        `${t('datasets.batchEvaluateFailed', '批量评估失败')}: ${error.message || error}`
      );
    } finally {
      batchEvaluating.value = false;
    }
  };

  return {
    evaluatingIds,
    batchEvaluating,
    handleEvaluateDataset,
    handleBatchEvaluate
  };
}

