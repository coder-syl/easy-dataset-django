import { ref, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useI18n } from 'vue-i18n';
import {
  fetchImageDatasetDetail,
  updateImageDataset,
  deleteImageDataset,
  fetchImageDatasets
} from '@/api/imageDatasets';

export function useImageDatasetDetails(projectId, datasetId) {
  const router = useRouter();
  const { t } = useI18n();

  const currentDataset = ref(null);
  const loading = ref(true);
  const confirming = ref(false);
  const unconfirming = ref(false);
  const saving = ref(false);
  const datasetsAllCount = ref(0);
  const datasetsConfirmCount = ref(0);

  // 获取数据集列表信息
  const fetchDatasetsList = async () => {
    try {
      const response = await fetchImageDatasets(projectId.value, { page: 1, pageSize: 1000 });
      const data = response?.data || response;
      const datasets = data.data || [];
      datasetsAllCount.value = data.total || 0;
      datasetsConfirmCount.value = datasets.filter((d) => d.confirmed).length;
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
      currentDataset.value = data;
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
      const response = await fetchImageDatasets(projectId.value, { page: 1, pageSize: 1000 });
      const data = response?.data || response;
      const datasets = data.data || [];

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
        router.push(`/projects/${projectId.value}/image-datasets/${nextDataset.id}`);
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

  return {
    currentDataset,
    loading,
    saving,
    confirming,
    unconfirming,
    datasetsAllCount,
    datasetsConfirmCount,
    updateDataset,
    handleNavigate,
    handleConfirm,
    handleUnconfirm,
    handleDelete,
    fetchDatasetDetail
  };
}

