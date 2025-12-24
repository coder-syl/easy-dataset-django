import { ref, watch, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ElMessage, ElMessageBox } from 'element-plus';
import { fetchDatasetDetail, updateDataset, deleteDataset, optimizeDataset, fetchDatasetTokenCount } from '@/api/dataset';
import { useModelStore } from '@/stores/model';
import http from '@/api/http';

/**
 * 数据集详情页面业务逻辑 Composable
 */
export function useDatasetDetails(projectIdRef, datasetIdRef) {
  const router = useRouter();
  const { t, locale } = useI18n();
  const modelStore = useModelStore();

  // 支持传入 ref/computed 或普通字符串
  const projectId = computed(() =>
    typeof projectIdRef === 'string' ? projectIdRef : projectIdRef.value
  );
  const datasetId = computed(() =>
    typeof datasetIdRef === 'string' ? datasetIdRef : datasetIdRef.value
  );

  const currentDataset = ref(null);
  const loading = ref(true);
  const editingAnswer = ref(false);
  const editingCot = ref(false);
  const editingQuestion = ref(false);
  const answerValue = ref('');
  const cotValue = ref('');
  const questionValue = ref('');
  const snackbar = ref({
    open: false,
    message: '',
    severity: 'success'
  });
  const confirming = ref(false);
  const unconfirming = ref(false);
  const optimizeDialog = ref({
    open: false,
    loading: false
  });
  const viewDialogOpen = ref(false);
  const viewChunk = ref(null);
  const datasetsAllCount = ref(0);
  const datasetsConfirmCount = ref(0);
  const answerTokens = ref(0);
  const cotTokens = ref(0);
  const shortcutsEnabled = ref((() => {
    const storedValue = localStorage.getItem('shortcutsEnabled');
    return storedValue !== null ? storedValue === 'true' : false;
  })());

  // 异步获取Token数量
  const fetchTokenCount = async () => {
    try {
      const response = await fetchDatasetTokenCount(projectId.value, datasetId.value);
      // HTTP拦截器已经处理了 {code: 0, data: {...}} 格式，response 已经是 data 部分
      const data = response;
      if (data?.answerTokens !== undefined) {
        answerTokens.value = data.answerTokens;
      }
      if (data?.cotTokens !== undefined) {
        cotTokens.value = data.cotTokens;
      }
    } catch (error) {
      console.error('获取Token数量失败:', error);
    }
  };

  // 获取数据集详情
  const fetchDatasets = async () => {
    try {
      loading.value = true;
      console.log('[useDatasetDetails] 获取数据集详情:', { projectId, datasetId });
      const response = await fetchDatasetDetail(projectId.value, datasetId.value);
      console.log('[useDatasetDetails] API 响应:', response);
      // HTTP拦截器已经处理了 {code: 0, data: {...}} 格式，response 已经是 data 部分
      // Django 返回格式: {datasets: {...}, datasetsAllCount: ..., datasetsConfirmCount: ...}
      const data = response;
      const dataset = data?.datasets || data;
      console.log('[useDatasetDetails] 解析后的数据集:', dataset);
      if (!dataset || !dataset.id) {
        // 数据集不存在，重定向回列表页
        console.warn('[useDatasetDetails] 数据集不存在或格式错误:', { data, dataset });
        ElMessage.error('数据集不存在');
        router.push(`/projects/${projectId.value}/datasets`);
        return;
      }
      currentDataset.value = dataset;
      cotValue.value = dataset?.cot || '';
      answerValue.value = dataset?.answer || '';
      questionValue.value = dataset?.question || '';
      datasetsAllCount.value = data?.datasetsAllCount || data?.total || 0;
      datasetsConfirmCount.value = data?.datasetsConfirmCount || data?.confirmedCount || 0;

      // 数据加载完成后，异步获取Token数量
      fetchTokenCount();
    } catch (error) {
      console.error('[useDatasetDetails] 获取数据集详情失败:', error);
      console.error('[useDatasetDetails] 错误详情:', {
        message: error?.message,
        response: error?.response,
        status: error?.response?.status,
        data: error?.response?.data
      });
      const errorMessage = error?.response?.data?.message || error?.message || '获取数据集详情失败';
      
      // 如果是数据集不存在，重定向回列表页
      if (errorMessage.includes('不存在') || error?.response?.status === 404) {
        console.warn('[useDatasetDetails] 数据集不存在，重定向到列表页');
        ElMessage.error(errorMessage);
        router.push(`/projects/${projectId.value}/datasets`);
        return;
      }
      
      ElMessage.error(errorMessage);
    } finally {
      loading.value = false;
    }
  };

  // 确认并保存数据集
  const handleConfirm = async () => {
    try {
      confirming.value = true;
      await updateDataset(projectId.value, datasetId.value, {
        confirmed: true
      });

      currentDataset.value = { ...currentDataset.value, confirmed: true };

      ElMessage.success(t('common.operationSuccess', '操作成功'));

      // 导航到下一个数据集
      handleNavigate('next');
    } catch (error) {
      ElMessage.error(error.message || t('common.operationFailed', '操作失败'));
    } finally {
      confirming.value = false;
    }
  };

  // 取消确认数据集
  const handleUnconfirm = async () => {
    try {
      unconfirming.value = true;
      await updateDataset(projectId.value, datasetId.value, {
        confirmed: false
      });

      currentDataset.value = { ...currentDataset.value, confirmed: false };

      ElMessage.success(t('datasets.unconfirmed', '已取消确认'));
    } catch (error) {
      ElMessage.error(error.message || t('datasets.unconfirmFailed', '取消确认失败'));
    } finally {
      unconfirming.value = false;
    }
  };

  // 导航到其他数据集
  const handleNavigate = async (direction) => {
    try {
      const response = await fetchDatasetDetail(projectId.value, datasetId.value, {
        operateType: direction
      });
      // Django 返回格式: {code: 0, data: {...}} 或 {code: 0, data: null}
      const data = response?.data || response;
      if (data && data.id) {
        router.push(`/projects/${projectId.value}/datasets/${data.id}`);
      } else {
        ElMessage.warning(
          t('datasets.noMoreData', `已经是${direction === 'next' ? '最后' : '第'}一条数据了`)
        );
      }
    } catch (error) {
      ElMessage.error(error.message);
    }
  };

  // 保存编辑
  const handleSave = async (field, value) => {
    try {
      await updateDataset(projectId.value, datasetId.value, {
        [field]: value
      });

      currentDataset.value = { ...currentDataset.value, [field]: value };

      ElMessage.success(t('common.saveSuccess', '保存成功'));

      // 重置编辑状态
      if (field === 'answer') editingAnswer.value = false;
      if (field === 'cot') editingCot.value = false;
      if (field === 'question') editingQuestion.value = false;

      // 如果更新了答案或思维链，重新获取Token数量
      if (field === 'answer' || field === 'cot') {
        fetchTokenCount();
      }
    } catch (error) {
      ElMessage.error(error.message || t('common.saveFailed', '保存失败'));
    }
  };

  // 删除数据集
  const handleDelete = async () => {
    try {
      await ElMessageBox.confirm(
        t('datasets.deleteConfirm', '确定要删除这条数据吗？此操作不可撤销。'),
        t('common.confirmDelete', '确认删除'),
        {
          confirmButtonText: t('common.confirm', '确认'),
          cancelButtonText: t('common.cancel', '取消'),
          type: 'warning'
        }
      );

      // 尝试获取下一个数据集
      let nextDatasetId = null;
      try {
        const nextResponse = await fetchDatasetDetail(projectId.value, datasetId.value, {
          operateType: 'next'
        });
        const nextData = nextResponse?.data || nextResponse;
        if (nextData && nextData.id) {
          nextDatasetId = nextData.id;
        }
      } catch (error) {
        console.error('获取下一个数据集失败:', error);
      }

      // 删除当前数据集
      await deleteDataset(projectId.value, datasetId.value);

      // 导航逻辑：有下一个就跳转下一个，没有则返回列表页
      if (nextDatasetId) {
        router.push(`/projects/${projectId.value}/datasets/${nextDatasetId}`);
      } else {
        router.push(`/projects/${projectId.value}/datasets`);
      }

      ElMessage.success(t('common.deleteSuccess', '删除成功'));
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error(error.message || t('common.deleteFailed', '删除失败'));
      }
    }
  };

  // 优化对话框相关操作
  const handleOpenOptimizeDialog = () => {
    optimizeDialog.value = {
      open: true,
      loading: false
    };
  };

  const handleCloseOptimizeDialog = () => {
    if (!optimizeDialog.value.loading) {
      optimizeDialog.value = {
        open: false,
        loading: false
      };
    }
  };

  // 优化操作
  const handleOptimize = async (advice) => {
    const selectedModel = modelStore.selectedModelInfo;
    if (!selectedModel || !selectedModel.modelName) {
      ElMessage.error(t('datasets.selectModelFirst', '请先选择模型，可以在顶部导航栏选择'));
      return;
    }

    // 立即关闭对话框，并设置优化中状态
    optimizeDialog.value = {
      open: false,
      loading: true
    };

    ElMessage.info(t('datasets.optimizing', '已开始优化，请稍候...'));

    // 异步后台处理
    (async () => {
      try {
        const language = locale.value === 'zh-CN' ? '中文' : 'en';
        const model = {
          modelName: selectedModel.modelName,
          ...selectedModel
        };

        await optimizeDataset(projectId.value, {
          datasetId: datasetId.value,
          model,
          advice,
          language
        });

        // 优化成功后，重新查询数据以获取最新状态
        await fetchDatasets();
        fetchTokenCount();

        ElMessage.success(t('datasets.optimizeSuccess', 'AI智能优化成功'));
    } catch (error) {
        ElMessage.error(error.message);
      } finally {
        optimizeDialog.value = {
          open: false,
          loading: false
        };
      }
    })();
  };

  // 查看文本块详情
  const handleViewChunk = async (chunkContent) => {
    try {
      viewChunk.value = chunkContent;
      viewDialogOpen.value = true;
    } catch (error) {
      console.error('查看文本块出错', error);
      snackbar.value = {
        open: true,
        message: error.message,
        severity: 'error'
      };
      viewDialogOpen.value = false;
    }
  };

  // 关闭文本块详情对话框
  const handleCloseViewDialog = () => {
    viewDialogOpen.value = false;
  };

  // 监听快捷键状态变化
  watch(shortcutsEnabled, (val) => {
    localStorage.setItem('shortcutsEnabled', val.toString());
  });

  // 监听 projectId / datasetId 变化（路由切换时自动刷新）
  watch(
    [projectId, datasetId],
    ([pId, dId]) => {
      if (pId && dId) {
        fetchDatasets();
      }
    },
    { immediate: true }
  );

  return {
    loading,
    currentDataset,
    answerValue,
    cotValue,
    questionValue,
    editingAnswer,
    editingCot,
    editingQuestion,
    confirming,
    unconfirming,
    snackbar,
    optimizeDialog,
    viewDialogOpen,
    viewChunk,
    datasetsAllCount,
    datasetsConfirmCount,
    answerTokens,
    cotTokens,
    shortcutsEnabled,
    setShortcutsEnabled: (val) => {
      shortcutsEnabled.value = val;
    },
    setSnackbar: (val) => {
      snackbar.value = val;
    },
    setAnswerValue: (val) => {
      answerValue.value = val;
    },
    setCotValue: (val) => {
      cotValue.value = val;
    },
    setQuestionValue: (val) => {
      questionValue.value = val;
    },
    setEditingAnswer: (val) => {
      editingAnswer.value = val;
    },
    setEditingCot: (val) => {
      editingCot.value = val;
    },
    setEditingQuestion: (val) => {
      editingQuestion.value = val;
    },
    handleNavigate,
    handleConfirm,
    handleUnconfirm,
    handleSave,
    handleDelete,
    handleOpenOptimizeDialog,
    handleCloseOptimizeDialog,
    handleOptimize,
    handleViewChunk,
    handleCloseViewDialog,
    fetchDatasets
  };
}

