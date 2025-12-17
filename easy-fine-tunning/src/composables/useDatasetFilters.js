import { ref, watch, onMounted } from 'vue';

/**
 * 数据集筛选条件管理 Composable
 * 负责筛选条件的保存、恢复和管理
 */
export function useDatasetFilters(projectId) {
  const filterConfirmed = ref('all');
  const filterHasCot = ref('all');
  const filterIsDistill = ref('all');
  const filterScoreRange = ref([0, 5]);
  const filterCustomTag = ref('');
  const filterNoteKeyword = ref('');
  const filterChunkName = ref('');
  const searchQuery = ref('');
  const searchField = ref('question');
  const page = ref(1);
  const rowsPerPage = ref(10);
  const isInitialized = ref(false);

  // 从 localStorage 恢复筛选条件
  onMounted(() => {
    try {
      const savedFilters = localStorage.getItem(`datasets-filters-${projectId}`);
      if (savedFilters) {
        const filters = JSON.parse(savedFilters);
        filterConfirmed.value = filters.filterConfirmed || 'all';
        filterHasCot.value = filters.filterHasCot || 'all';
        filterIsDistill.value = filters.filterIsDistill || 'all';
        filterScoreRange.value = filters.filterScoreRange || [0, 5];
        filterCustomTag.value = filters.filterCustomTag || '';
        filterNoteKeyword.value = filters.filterNoteKeyword || '';
        filterChunkName.value = filters.filterChunkName || '';
        searchQuery.value = filters.searchQuery || '';
        searchField.value = filters.searchField || 'question';
        page.value = filters.page || 1;
        rowsPerPage.value = filters.rowsPerPage || 10;
      }
    } catch (error) {
      console.error('恢复筛选条件失败:', error);
    }
    isInitialized.value = true;
  });

  // 保存筛选条件到 localStorage
  watch(
    [
      filterConfirmed,
      filterHasCot,
      filterIsDistill,
      filterScoreRange,
      filterCustomTag,
      filterNoteKeyword,
      filterChunkName,
      searchQuery,
      searchField,
      page,
      rowsPerPage,
      isInitialized
    ],
    () => {
      if (!isInitialized.value) return;
      try {
        const filters = {
          filterConfirmed: filterConfirmed.value,
          filterHasCot: filterHasCot.value,
          filterIsDistill: filterIsDistill.value,
          filterScoreRange: filterScoreRange.value,
          filterCustomTag: filterCustomTag.value,
          filterNoteKeyword: filterNoteKeyword.value,
          filterChunkName: filterChunkName.value,
          searchQuery: searchQuery.value,
          searchField: searchField.value,
          page: page.value,
          rowsPerPage: rowsPerPage.value
        };
        localStorage.setItem(`datasets-filters-${projectId}`, JSON.stringify(filters));
      } catch (error) {
        console.error('保存筛选条件失败:', error);
      }
    },
    { deep: true }
  );

  /**
   * 计算当前活跃的筛选条件数量
   */
  const getActiveFilterCount = () => {
    let count = 0;
    if (filterConfirmed.value !== 'all') count++;
    if (filterHasCot.value !== 'all') count++;
    if (filterIsDistill.value !== 'all') count++;
    if (filterScoreRange.value[0] > 0 || filterScoreRange.value[1] < 5) count++;
    if (filterCustomTag.value) count++;
    if (filterNoteKeyword.value) count++;
    if (filterChunkName.value) count++;
    return count;
  };

  /**
   * 重置所有筛选条件为默认值
   */
  const resetFilters = () => {
    filterConfirmed.value = 'all';
    filterHasCot.value = 'all';
    filterIsDistill.value = 'all';
    filterScoreRange.value = [0, 5];
    filterCustomTag.value = '';
    filterNoteKeyword.value = '';
    filterChunkName.value = '';
    searchQuery.value = '';
    searchField.value = 'question';
    page.value = 1;
    rowsPerPage.value = 10;
  };

  return {
    // 筛选条件状态
    filterConfirmed,
    filterHasCot,
    filterIsDistill,
    filterScoreRange,
    filterCustomTag,
    filterNoteKeyword,
    filterChunkName,
    searchQuery,
    searchField,
    // 分页状态
    page,
    rowsPerPage,
    // 初始化状态
    isInitialized,
    // 工具方法
    resetFilters,
    getActiveFilterCount
  };
}

