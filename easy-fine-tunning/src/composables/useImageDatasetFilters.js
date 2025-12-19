import { ref, watch } from 'vue';

const STORAGE_KEY = 'imageDatasetFilters';

export function useImageDatasetFilters(projectId) {
  const searchQuery = ref('');
  const statusFilter = ref('all');
  const scoreFilter = ref([0, 5]);
  const isInitialized = ref(false);

  // 从 localStorage 恢复筛选条件
  const restoreFilters = () => {
    try {
      const stored = localStorage.getItem(`${STORAGE_KEY}_${projectId.value}`);
      if (stored) {
        const filters = JSON.parse(stored);
        searchQuery.value = filters.searchQuery || '';
        statusFilter.value = filters.statusFilter || 'all';
        scoreFilter.value = filters.scoreFilter || [0, 5];
      }
    } catch (error) {
      console.error('Failed to restore filters:', error);
    }
    isInitialized.value = true;
  };

  // 保存筛选条件到 localStorage
  watch(
    [searchQuery, statusFilter, scoreFilter, isInitialized],
    () => {
      if (isInitialized.value) {
        try {
          localStorage.setItem(
            `${STORAGE_KEY}_${projectId.value}`,
            JSON.stringify({
              searchQuery: searchQuery.value,
              statusFilter: statusFilter.value,
              scoreFilter: scoreFilter.value
            })
          );
        } catch (error) {
          console.error('Failed to save filters:', error);
        }
      }
    },
    { deep: true }
  );

  // 初始化
  restoreFilters();

  // 计算活跃筛选条件数
  const getActiveFilterCount = () => {
    let count = 0;
    if (statusFilter.value !== 'all') count++;
    if (Array.isArray(scoreFilter.value) && (scoreFilter.value[0] > 0 || scoreFilter.value[1] < 5)) {
      count++;
    }
    return count;
  };

  // 重置筛选条件
  const resetFilters = () => {
    searchQuery.value = '';
    statusFilter.value = 'all';
    scoreFilter.value = [0, 5];
  };

  // 获取筛选对象
  const getFilters = () => ({
    search: searchQuery.value,
    confirmed: statusFilter.value === 'all' ? undefined : statusFilter.value === 'confirmed',
    minScore: scoreFilter.value[0] > 0 ? scoreFilter.value[0] : undefined,
    maxScore: scoreFilter.value[1] < 5 ? scoreFilter.value[1] : undefined
  });

  return {
    searchQuery,
    statusFilter,
    scoreFilter,
    isInitialized,
    getActiveFilterCount,
    resetFilters,
    getFilters
  };
}

