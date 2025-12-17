import { ref, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  fetchConversations,
  fetchAllConversationIds,
  deleteConversation,
  exportConversations
} from '@/api/conversation';
import { useDebounceFn } from '@vueuse/core';

/**
 * 多轮对话数据管理 Composable
 */
export function useMultiTurnData(projectId) {
  const router = useRouter();
  const { t } = useI18n();

  // 状态管理
  const conversations = ref([]);
  const loading = ref(true);
  const page = ref(1);
  const rowsPerPage = ref(20);
  const total = ref(0);
  const searchKeyword = ref('');
  const filterDialogOpen = ref(false);
  const exportLoading = ref(false);

  // 批量删除相关状态
  const selectedIds = ref([]);
  const isAllSelected = ref(false);
  const batchDeleteLoading = ref(false);

  // 筛选条件
  const filters = ref({
    roleA: '',
    roleB: '',
    scenario: '',
    scoreMin: '',
    scoreMax: '',
    confirmed: ''
  });

  // 获取多轮对话数据集列表
  const fetchConversationsList = async (newPage = page.value) => {
    try {
      loading.value = true;
      const params = {
        page: newPage,
        pageSize: rowsPerPage.value
      };

      if (searchKeyword.value) {
        params.keyword = searchKeyword.value;
      }
      if (filters.value.roleA) {
        params.roleA = filters.value.roleA;
      }
      if (filters.value.roleB) {
        params.roleB = filters.value.roleB;
      }
      if (filters.value.scenario) {
        params.scenario = filters.value.scenario;
      }
      if (filters.value.scoreMin) {
        params.scoreMin = filters.value.scoreMin;
      }
      if (filters.value.scoreMax) {
        params.scoreMax = filters.value.scoreMax;
      }
      if (filters.value.confirmed) {
        params.confirmed = filters.value.confirmed;
      }

      const response = await fetchConversations(projectId, params);
      // HTTP拦截器已经处理了 {code: 0, data: {...}} 格式，response 已经是 data 部分
      // Django 返回格式: {data: [...], total: number, page: number, pageSize: number}
      const data = response;
      let list = Array.isArray(data?.data) ? data.data : Array.isArray(data) ? data : [];

      // 统一使用下划线字段，兼容 Node 的 camelCase 返回
      list = list.map((item) => ({
        ...item,
        // 轮次
        turn_count: item.turn_count ?? item.turnCount ?? 0,
        max_turns:
          item.max_turns ??
          item.maxTurns ??
          item.turn_count ??
          item.turnCount ??
          0,
        // 角色
        role_a: item.role_a ?? item.roleA,
        role_b: item.role_b ?? item.roleB,
        // 时间
        create_at:
          item.create_at ??
          item.createAt ??
          item.createTime ??
          item.create_time
      }));

      conversations.value = list;
      total.value = data?.total || 0;
    } catch (error) {
      console.error('获取多轮对话数据集失败:', error);
      ElMessage.error(error.message || t('datasets.fetchDataFailed', '获取数据失败'));
      conversations.value = [];
      total.value = 0;
    } finally {
      loading.value = false;
    }
  };

  // 导出数据集
  const handleExport = async () => {
    try {
      exportLoading.value = true;
      const response = await exportConversations(projectId, {
        conversationIds: selectedIds.value.length > 0 ? selectedIds.value : undefined,
        format: 'json'
      });

      // HTTP拦截器已经处理了响应格式
      const data = response;
      const content = data?.content || JSON.stringify(data, null, 2);

      // 创建下载链接
      const dataBlob = new Blob([content], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `multi-turn-conversations-${projectId}-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      ElMessage.success(t('datasets.exportSuccess', '导出成功'));
    } catch (error) {
      console.error('导出失败:', error);
      ElMessage.error(error.message || t('datasets.exportFailed', '导出失败'));
    } finally {
      exportLoading.value = false;
    }
  };

  // 获取所有对话 ID
  const fetchAllIds = async () => {
    try {
      const params = { getAllIds: 'true' };

      // 添加筛选条件
      if (searchKeyword.value) {
        params.keyword = searchKeyword.value;
      }
      if (filters.value.roleA) {
        params.roleA = filters.value.roleA;
      }
      if (filters.value.roleB) {
        params.roleB = filters.value.roleB;
      }
      if (filters.value.scenario) {
        params.scenario = filters.value.scenario;
      }
      if (filters.value.scoreMin) {
        params.scoreMin = filters.value.scoreMin;
      }
      if (filters.value.scoreMax) {
        params.scoreMax = filters.value.scoreMax;
      }
      if (filters.value.confirmed) {
        params.confirmed = filters.value.confirmed;
      }

      const response = await fetchAllConversationIds(projectId, params);
      // HTTP拦截器已经处理了响应格式
      const data = response;
      return data?.allConversationIds || [];
    } catch (error) {
      console.error('获取所有对话ID失败:', error);
      ElMessage.error(error.message || t('datasets.fetchDataFailed', '获取数据失败'));
      return [];
    }
  };

  // 删除对话数据集
  const handleDelete = async (conversationId) => {
    try {
      await ElMessageBox.confirm(
        t('datasets.confirmDeleteConversation', '确定要删除这条对话吗？'),
        t('common.confirmDelete', '确认删除'),
        {
          confirmButtonText: t('common.confirm', '确认'),
          cancelButtonText: t('common.cancel', '取消'),
          type: 'warning'
        }
      );

      await deleteConversation(projectId, conversationId);
      ElMessage.success(t('datasets.deleteSuccess', '删除成功'));
      fetchConversationsList();
    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除失败:', error);
        ElMessage.error(error.message || t('datasets.deleteFailed', '删除失败'));
      }
    }
  };

  // 并发删除函数
  const deleteConversationsConcurrently = async (conversationIds, concurrency = 10) => {
    const results = [];
    const errors = [];

    for (let i = 0; i < conversationIds.length; i += concurrency) {
      const batch = conversationIds.slice(i, i + concurrency);
      const promises = batch.map(async (id) => {
        try {
          await deleteConversation(projectId, id);
          return { id, success: true };
        } catch (error) {
          errors.push({ id, error: error.message });
          return { id, success: false, error: error.message };
        }
      });

      const batchResults = await Promise.all(promises);
      results.push(...batchResults);
    }

    return { results, errors };
  };

  // 批量删除处理
  const handleBatchDelete = async () => {
    let idsToDelete = selectedIds.value;

    // 如果是全选，需要获取所有ID
    if (isAllSelected.value) {
      idsToDelete = await fetchAllIds();
      if (idsToDelete.length === 0) {
        ElMessage.error(t('datasets.noDataToDelete', '没有可删除的数据'));
        return;
      }
    }

    if (idsToDelete.length === 0) {
      ElMessage.error(t('datasets.pleaseSelectData', '请选择要删除的数据'));
      return;
    }

    try {
      await ElMessageBox.confirm(
        t('datasets.batchDeleteConfirm', '确定要删除选中的 {count} 条对话吗？', {
          count: idsToDelete.length
        }),
        t('common.confirmDelete', '确认删除'),
        {
          confirmButtonText: t('common.confirm', '确认'),
          cancelButtonText: t('common.cancel', '取消'),
          type: 'warning'
        }
      );

      batchDeleteLoading.value = true;
      const { results, errors } = await deleteConversationsConcurrently(idsToDelete);

      const successCount = results.filter((r) => r.success).length;
      const failCount = errors.length;

      if (failCount === 0) {
        ElMessage.success(t('common.deleteSuccess', '删除成功', { count: successCount }));
      } else {
        ElMessage.warning(
          t('datasets.batchDeletePartialSuccess', '部分删除成功：成功 {success} 条，失败 {fail} 条', {
            success: successCount,
            fail: failCount
          })
        );
      }

      // 清空选择状态
      selectedIds.value = [];
      isAllSelected.value = false;

      // 刷新数据
      fetchConversationsList();
    } catch (error) {
      if (error !== 'cancel') {
        console.error('批量删除失败:', error);
        ElMessage.error(error.message || t('datasets.batchDeleteFailed', '批量删除失败'));
      }
    } finally {
      batchDeleteLoading.value = false;
    }
  };

  // 处理选择变化
  const handleSelectionChange = (newSelectedIds) => {
    selectedIds.value = newSelectedIds;
    // 如果没有选中任何项，取消全选状态
    if (newSelectedIds.length === 0) {
      isAllSelected.value = false;
    }
  };

  // 处理全选
  const handleSelectAll = (selectAll) => {
    isAllSelected.value = selectAll;
    if (!selectAll) {
      selectedIds.value = [];
    }
  };

  // 查看详情
  const handleView = (conversationId) => {
    router.push(`/projects/${projectId}/multi-turn/${conversationId}`);
  };

  // 应用筛选
  const applyFilters = () => {
    page.value = 1;
    filterDialogOpen.value = false;
    fetchConversationsList(1);
  };

  // 重置筛选
  const resetFilters = () => {
    filters.value = {
      roleA: '',
      roleB: '',
      scenario: '',
      scoreMin: '',
      scoreMax: '',
      confirmed: ''
    };
    searchKeyword.value = '';
    page.value = 1;
    fetchConversationsList(1);
  };

  // 处理搜索
  const handleSearch = () => {
    page.value = 1;
    fetchConversationsList(1);
  };

  // 处理页面变化
  const handlePageChange = (newPage) => {
    // Element Plus 的页码从 1 开始，API 也从 1 开始，直接使用
    page.value = newPage;
  };

  // 处理每页行数变化
  const handleRowsPerPageChange = (newRowsPerPage) => {
    rowsPerPage.value = newRowsPerPage;
    page.value = 1;
    fetchConversationsList(1);
  };

  // 防抖搜索
  const debouncedSearch = useDebounceFn(() => {
    if (searchKeyword.value) {
      handleSearch();
    }
  }, 500);

  watch(searchKeyword, () => {
    debouncedSearch();
  });

  // 监听筛选条件变化
  watch(
    [page, rowsPerPage],
    () => {
      fetchConversationsList();
    },
    { immediate: false }
  );

  // 初始化
  onMounted(() => {
    fetchConversationsList();
  });

  return {
    // 状态
    conversations,
    loading,
    page,
    rowsPerPage,
    total,
    searchKeyword,
    filterDialogOpen,
    exportLoading,
    filters,

    // 批量删除相关状态
    selectedIds,
    isAllSelected,
    batchDeleteLoading,

    // 状态设置函数
    setSearchKeyword: (value) => {
      searchKeyword.value = value;
    },
    setFilterDialogOpen: (value) => {
      filterDialogOpen.value = value;
    },
    setFilters: (value) => {
      filters.value = value;
    },

    // 操作函数
    fetchConversations: fetchConversationsList,
    handleExport,
    handleDelete,
    handleView,
    applyFilters,
    resetFilters,
    handleSearch,
    handlePageChange,
    handleRowsPerPageChange,

    // 批量删除相关函数
    handleBatchDelete,
    handleSelectionChange,
    handleSelectAll
  };
}

