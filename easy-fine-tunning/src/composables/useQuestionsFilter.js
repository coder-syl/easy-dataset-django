import { ref, watch } from 'vue';
import { useDebounceFn } from '@vueuse/core';
import { fetchQuestions } from '@/api/question';

/**
 * 问题筛选和搜索 Composable
 */
export function useQuestionsFilter(projectId) {
  // 过滤和搜索状态
  const answerFilter = ref('all'); // 'all', 'answered', 'unanswered'
  const searchTerm = ref('');
  const chunkNameFilter = ref('');
  const sourceTypeFilter = ref('all'); // 'all', 'text', 'image'

  // 防抖后的搜索词
  const debouncedSearchTerm = ref('');
  const debouncedChunkNameFilter = ref('');

  // 选择状态
  const selectedQuestions = ref([]);

  // 防抖搜索
  const debouncedSearch = useDebounceFn(() => {
    debouncedSearchTerm.value = searchTerm.value;
  }, 500);

  const debouncedChunkNameSearch = useDebounceFn(() => {
    debouncedChunkNameFilter.value = chunkNameFilter.value;
  }, 500);

  watch(searchTerm, () => {
    debouncedSearch();
  });

  watch(chunkNameFilter, () => {
    debouncedChunkNameSearch();
  });

  // 处理问题选择
  const handleSelectQuestion = (questionKey, newSelected) => {
    if (newSelected !== undefined && newSelected !== null) {
      // 处理批量选择的情况
      if (Array.isArray(newSelected)) {
        selectedQuestions.value = newSelected;
      } else if (typeof newSelected === 'boolean') {
        // 单个问题选择/取消
        if (newSelected) {
          if (!selectedQuestions.value.includes(questionKey)) {
            selectedQuestions.value.push(questionKey);
          }
        } else {
          selectedQuestions.value = selectedQuestions.value.filter((id) => id !== questionKey);
        }
      }
    } else {
      // 切换单个问题的选中状态
      const index = selectedQuestions.value.indexOf(questionKey);
      if (index > -1) {
        selectedQuestions.value.splice(index, 1);
      } else {
        selectedQuestions.value.push(questionKey);
      }
    }
  };

  // 全选/取消全选
  const handleSelectAll = async () => {
    if (selectedQuestions.value.length > 0) {
      selectedQuestions.value = [];
    } else {
      try {
        const response = await fetchQuestions(projectId, {
          status: answerFilter.value,
          input: searchTerm.value,
          chunkName: encodeURIComponent(chunkNameFilter.value),
          sourceType: sourceTypeFilter.value,
          selectedAll: '1'
        });
        // Django 返回格式: { data: [...] } 或直接是数组
        const data = response?.data || response || [];
        selectedQuestions.value = Array.isArray(data) ? data.map((item) => item.id) : [];
      } catch (error) {
        console.error('获取所有问题ID失败:', error);
      }
    }
  };

  // 处理搜索输入变化
  const handleSearchChange = (value) => {
    searchTerm.value = value;
  };

  // 处理过滤器变化
  const handleFilterChange = (value) => {
    answerFilter.value = value;
  };

  // 处理文本块名称筛选变化
  const handleChunkNameFilterChange = (value) => {
    chunkNameFilter.value = value;
  };

  // 处理数据源类型筛选变化
  const handleSourceTypeFilterChange = (value) => {
    sourceTypeFilter.value = value;
  };

  // 清空选择
  const clearSelection = () => {
    selectedQuestions.value = [];
  };

  // 重置所有过滤条件
  const resetFilters = () => {
    searchTerm.value = '';
    answerFilter.value = 'all';
    chunkNameFilter.value = '';
    sourceTypeFilter.value = 'all';
    selectedQuestions.value = [];
  };

  return {
    // 状态
    answerFilter,
    searchTerm,
    debouncedSearchTerm,
    chunkNameFilter,
    debouncedChunkNameFilter,
    sourceTypeFilter,
    selectedQuestions,

    // 方法
    setAnswerFilter: (value) => {
      answerFilter.value = value;
    },
    setSearchTerm: (value) => {
      searchTerm.value = value;
    },
    setChunkNameFilter: (value) => {
      chunkNameFilter.value = value;
    },
    setSourceTypeFilter: (value) => {
      sourceTypeFilter.value = value;
    },
    setSelectedQuestions: (value) => {
      selectedQuestions.value = value;
    },
    handleSelectQuestion,
    handleSelectAll,
    handleSearchChange,
    handleFilterChange,
    handleChunkNameFilterChange,
    handleSourceTypeFilterChange,
    clearSelection,
    resetFilters
  };
}

