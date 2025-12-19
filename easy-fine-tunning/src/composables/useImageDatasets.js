import { ref, computed, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { useI18n } from 'vue-i18n';
import { fetchImageDatasets, deleteImageDataset } from '@/api/imageDatasets';

export function useImageDatasets(projectId, filters) {
  const { t } = useI18n();
  const datasets = ref({ data: [], total: 0 });
  const loading = ref(false);
  const page = ref(1);
  const pageSize = ref(20);

  // 使用 computed 稳定 filters 对象引用
  const stableFilters = computed(() => {
    if (!filters || typeof filters.value !== 'object') {
      return {
        search: '',
        confirmed: undefined,
        minScore: undefined,
        maxScore: undefined
      };
    }
    return {
      search: filters.value?.search || '',
      confirmed: filters.value?.confirmed,
      minScore: filters.value?.minScore,
      maxScore: filters.value?.maxScore
    };
  });

  // 获取数据集列表
  const fetchDatasets = async () => {
    if (!projectId.value) return;

    try {
      loading.value = true;
      const params = {
        page: page.value,
        pageSize: pageSize.value
      };

      // 搜索条件
      if (stableFilters.value.search) {
        params.search = stableFilters.value.search;
      }

      // 确认状态筛选
      if (stableFilters.value.confirmed !== undefined) {
        params.confirmed = stableFilters.value.confirmed;
      }

      // 评分筛选
      if (stableFilters.value.minScore !== undefined) {
        params.minScore = stableFilters.value.minScore;
      }
      if (stableFilters.value.maxScore !== undefined) {
        params.maxScore = stableFilters.value.maxScore;
      }

      const response = await fetchImageDatasets(projectId.value, params);
      // http 拦截器已经解包了 { code: 0, data: {...} } 格式，返回的是 data 部分
      // Django 返回格式: { code: 0, data: { data: [...], total: ..., page: ..., pageSize: ... } }
      // 解包后: { data: [...], total: ..., page: ..., pageSize: ... }
      let data = response;
      
      // 兼容不同的响应格式
      if (data && typeof data === 'object' && !Array.isArray(data)) {
        // 如果 response 是对象，检查是否有嵌套的 data 字段
        if ('data' in data && Array.isArray(data.data)) {
          datasets.value = {
            data: data.data,
            total: data.total || 0
          };
        } else if (Array.isArray(data)) {
          // 如果 response 直接是数组
          datasets.value = {
            data: data,
            total: data.length
          };
        } else {
          datasets.value = {
            data: [],
            total: 0
          };
        }
      } else if (Array.isArray(data)) {
        // 如果 response 直接是数组
        datasets.value = {
          data: data,
          total: data.length
        };
      } else {
        datasets.value = {
          data: [],
          total: 0
        };
      }
    } catch (error) {
      console.error('Failed to fetch datasets:', error);
      ElMessage.error(t('imageDatasets.fetchFailed', '获取数据集失败'));
    } finally {
      loading.value = false;
    }
  };

  // 删除数据集
  const handleDeleteDataset = async (datasetId) => {
    try {
      await deleteImageDataset(projectId.value, datasetId);
      ElMessage.success(t('imageDatasets.deleteSuccess', '删除成功'));
      await fetchDatasets();
    } catch (error) {
      console.error('Failed to delete dataset:', error);
      ElMessage.error(t('imageDatasets.deleteFailed', '删除失败'));
    }
  };

  // 监听 filters 变化
  watch(
    [() => projectId.value, page, pageSize, stableFilters],
    () => {
      if (projectId.value) {
        fetchDatasets();
      }
    },
    { immediate: true }
  );

  return {
    datasets,
    loading,
    page,
    pageSize,
    fetchDatasets,
    handleDeleteDataset
  };
}

