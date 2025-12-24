import { ref, computed, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useI18n } from 'vue-i18n';
import {
  fetchImageDatasetDetail,
  updateImageDataset,
  deleteImageDataset,
  fetchImageDatasets
} from '@/api/imageDatasets';
import { regenerateImageDataset } from '@/api/imageDatasets';
import { useModelStore } from '@/stores/model';
 
export function useImageDatasetDetails(projectId, datasetId) {
  const router = useRouter();
  const { t, locale } = useI18n();
  const modelStore = useModelStore();

  const currentDataset = ref(null);
  const loading = ref(true);
  const confirming = ref(false);
  const unconfirming = ref(false);
  const regenerating = ref(false);
  const saving = ref(false);
  const datasets_all_count = ref(0);
  const datasets_confirm_count = ref(0);

  // 获取数据集列表信息
  const fetchDatasetsList = async () => {
    try {
      const response = await fetchImageDatasets(projectId.value, { page: 1, pageSize: 1000 });
      // debug log for response shape
      console.debug('[useImageDatasetDetails] fetchDatasetsList response:', response);
      // Normalize wrapper: support { code:0, data: { data: [...], total, confirmed_count } } and { data: [...], total, confirmed_count } and raw array
      let payload = response?.data || response;
      if (payload && payload.code !== undefined && payload.data !== undefined) {
        payload = payload.data;
      }
      const datasets = payload && payload.data ? payload.data : Array.isArray(payload) ? payload : [];
      // prefer snake_case server fields: total and confirmed_count
      datasets_all_count.value = Number(payload && payload.total ? payload.total : (Array.isArray(datasets) ? datasets.length : 0));
      datasets_confirm_count.value = Number(payload && payload.confirmed_count !== undefined ? payload.confirmed_count : (Array.isArray(datasets) ? datasets.filter((d) => !!d.confirmed).length : 0));
      console.log('[useImageDatasetDetails] datasets_all_count:', datasets_all_count.value);
      console.log('[useImageDatasetDetails] datasets_confirm_count:', datasets_confirm_count.value);
    } catch (error) {
      console.error('Failed to fetch datasets list:', error);
    }
  };

  // 获取当前数据集详情
  const fetchDatasetDetail = async () => {
    try {
      loading.value = true;
      const response = await fetchImageDatasetDetail(projectId.value, datasetId.value);
      const data = response?.data || response;
      // Backend detail returns snake_case: { dataset: {...}, datasets_all_count, datasets_confirm_count }
      if (data && data.dataset) {
        currentDataset.value = data.dataset;
        if (typeof data.datasets_all_count !== 'undefined') {
          datasets_all_count.value = Number(data.datasets_all_count);
        }
        if (typeof data.datasets_confirm_count !== 'undefined') {
          datasets_confirm_count.value = Number(data.datasets_confirm_count);
        }
      } else {
        currentDataset.value = data;
      }
    } catch (error) {
      console.error('Failed to fetch dataset detail:', error);
      ElMessage.error(t('imageDatasets.fetchDetailFailed', '获取详情失败'));
    } finally {
      loading.value = false;
    }
  };

  // 初始化
  watch(
    [projectId, datasetId],
    () => {
      if (projectId.value && datasetId.value) {
        fetchDatasetDetail();
        fetchDatasetsList();
      }
    },
    { immediate: true }
  );

  // 也在 mounted 时确保触发一次，避免某些路由时序问题未触发 watch
  onMounted(() => {
    if (projectId.value && datasetId.value) {
      console.log('[useImageDatasetDetails] onMounted fetching dataset and list', { projectId: projectId.value, datasetId: datasetId.value });
      fetchDatasetDetail();
      fetchDatasetsList();
    } else {
      console.log('[useImageDatasetDetails] onMounted missing params', { projectId: projectId.value, datasetId: datasetId.value });
    }
  });

  // 更新数据集
  const updateDataset = async (updates) => {
    try {
      saving.value = true;
      await updateImageDataset(projectId.value, datasetId.value, updates);
      ElMessage.success(t('imageDatasets.updateSuccess', '更新成功'));
      // 刷新数据
      await fetchDatasetDetail();
      await fetchDatasetsList();
    } catch (error) {
      console.error('Failed to update dataset:', error);
      ElMessage.error(t('imageDatasets.updateFailed', '更新失败'));
    } finally {
      saving.value = false;
    }
  };

  // 翻页导航
  const handleNavigate = async (direction, skipCurrentId = null) => {
    try {
      console.debug('[useImageDatasetDetails] handleNavigate start', { direction, skipCurrentId });
      const response = await fetchImageDatasets(projectId.value, { page: 1, pageSize: 1000 });
      console.debug('[useImageDatasetDetails] fetchImageDatasets response:', response);
      let payload = response?.data || response;
      if (payload && payload.code !== undefined && payload.data !== undefined) {
        payload = payload.data;
      }
      const datasets = payload && payload.data ? payload.data : Array.isArray(payload) ? payload : [];

      if (datasets.length === 0) {
        router.push(`/projects/${projectId.value}/image-datasets`);
        return;
      }

      // 确定当前索引
      let currentIndex = -1;
      const searchId = skipCurrentId || datasetId.value;
      const currentDatasetId = String(searchId);

      // 查找当前数据集的索引
      currentIndex = datasets.findIndex((d) => String(d.id) === currentDatasetId);

      // 如果找不到（删除场景或其他原因），从第一个开始
      if (currentIndex === -1) {
        currentIndex = 0;
      }

      // 计算下一个索引
      let nextIndex;
      if (direction === 'prev') {
        nextIndex = currentIndex > 0 ? currentIndex - 1 : datasets.length - 1;
      } else {
        nextIndex = currentIndex < datasets.length - 1 ? currentIndex + 1 : 0;
      }

      const nextDataset = datasets[nextIndex];
      if (nextDataset) {
        console.debug('[useImageDatasetDetails] navigating to', nextDataset.id);
        router.push(`/projects/${projectId.value}/image-datasets/${nextDataset.id}`);
      } else {
        console.warn('[useImageDatasetDetails] nextDataset not found', { datasets, currentDatasetId, currentIndex, nextIndex });
      }
    } catch (error) {
      console.error('Failed to navigate:', error);
      ElMessage.error(t('common.navigationFailed', '导航失败'));
    }
  };

  // 确认保留
  const handleConfirm = async () => {
    confirming.value = true;
    try {
      await updateDataset({ confirmed: true });
      // 确认后导航到下一条
      await handleNavigate('next');
    } finally {
      confirming.value = false;
    }
  };

  // 取消确认
  const handleUnconfirm = async () => {
    unconfirming.value = true;
    try {
      await updateDataset({ confirmed: false });
    } finally {
      unconfirming.value = false;
    }
  };

  // 删除数据集
  const handleDelete = async () => {
    try {
      await ElMessageBox.confirm(
        t('imageDatasets.deleteConfirm', '确定要删除这个图像数据集吗？'),
        t('common.confirm', '确认'),
        {
          type: 'warning'
        }
      );
      await deleteImageDataset(projectId.value, datasetId.value);
      ElMessage.success(t('imageDatasets.deleteSuccess', '删除成功'));
      // 导航到下一条，传递 datasetId 以便 handleNavigate 知道是删除场景
      await handleNavigate('next', datasetId.value);
    } catch (error) {
      if (error !== 'cancel') {
        console.error('Failed to delete dataset:', error);
        ElMessage.error(t('imageDatasets.deleteFailed', '删除失败'));
      }
    }
  };

  // 重新生成（Regenerate）已保存的数据集答案（会更新数据库记录）
  const regenerateDataset = async (options = {}) => {
    try {
      regenerating.value = true;
      const model = options.model || modelStore.selectedModelInfo || null;
      const payload = {
        model,
        language: locale.value === 'zh-CN' ? 'zh' : 'en',
        previewOnly: options.previewOnly || false
      };
      await regenerateImageDataset(projectId.value, datasetId.value, payload);
      // 刷新数据
      await fetchDatasetDetail();
      await fetchDatasetsList();
      ElMessage.success(t('images.regenerateSuccess', 'AI 识别成功'));
    } catch (error) {
      console.error('Failed to regenerate dataset:', error);
      ElMessage.error(t('images.regenerateFailed', 'AI 识别失败'));
    } finally {
      regenerating.value = false;
    }
  };

  return {
    currentDataset,
    loading,
    saving,
    confirming,
    unconfirming,
    datasets_all_count,
    datasets_confirm_count,
    updateDataset,
    handleNavigate,
    handleConfirm,
    handleUnconfirm,
    handleDelete,
    fetchDatasetDetail,
    regenerateDataset,
    regenerating
  };
}

