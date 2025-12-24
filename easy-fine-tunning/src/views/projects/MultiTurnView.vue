<template>
  <div class="multi-turn-view projects-container">
    <el-card v-loading="loading" class="main-card ed-card">
      <template #header>
        <div class="card-header">
          <h3>{{ $t('datasets.multiTurn', '多轮对话数据集') }}</h3>
        </div>
      </template>

      <!-- 搜索和操作栏 -->
      <div class="search-action-bar">
        <SearchBar
          :search-keyword="searchKeyword"
          :export-loading="exportLoading"
          :selected-count="selectedCount"
          :batch-delete-loading="batchDeleteLoading"
          @search-change="(v) => { setSearchKeyword(v); page.value = 1; handleSearch(); }"
          @search="() => { page.value = 1; handleSearch(); }"
          @filter-click="() => setFilterDialogOpen(true)"
          @export-click="openExportDialog"
          @batch-delete="handleBatchDelete"
        />
        <ActionBar
          :batch-evaluating="batchEvaluating"
          :selected-count="selectedCount"
          :batch-delete-loading="batchDeleteLoading"
          @export="openExportDialog"
          @batch-evaluate="handleBatchEvaluate"
          @import="openImportDialog"
          @batch-delete="handleBatchDelete"
        />
      </div>

      

      <!-- 对话列表 -->
      <ConversationTable
        :conversations="conversations"
        :loading="loading"
        :page="page"
        :rows-per-page="rowsPerPage"
        :total="total"
        :selected-ids="selectedIds"
        :is-all-selected="isAllSelected"
        :evaluating-ids="evaluatingIds"
        @view="handleView"
        @delete="handleDelete"
        @evaluate="handleEvaluateConversation"
        @selection-change="handleSelectionChange"
        @select-all="handleSelectAll"
        @page-change="handlePageChange"
        @rows-per-page-change="handleRowsPerPageChange"
      />

  <!-- 导出对话框：使用通用导出弹窗 -->
  <MultiTurnExportDialog
    v-model:open="exportDialogOpen"
    :project-id="projectId"
    :selected-ids="selectedIds"
    @export="handleExportDatasets"
  />
  <!-- 导入对话框 -->
  <ImportDatasetDialog
    v-model:open="importDialogOpen"
    :project-id="projectId"
    @import-success="() => { fetchConversationsList(); }"
  />

      <!-- 筛选对话框 -->
      <FilterDialog
        v-model:open="filterDialogOpen"
        :filters="filters"
        @update:filters="setFilters"
        @reset="resetFilters"
        @apply="applyFilters"
        @close="setFilterDialogOpen(false)"
      />
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { Delete } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useDebounceFn } from '@vueuse/core';
import { useMultiTurnData } from '@/composables/useMultiTurnData';
import SearchBar from '@/components/datasets/SearchBar.vue';
import ActionBar from '@/components/datasets/ActionBar.vue';
import MultiTurnExportDialog from '@/components/datasets/MultiTurnExportDialog.vue';
import ConversationTable from '@/components/multi-turn/ConversationTable.vue';
import FilterDialog from '@/components/multi-turn/FilterDialog.vue';
import ImportDatasetDialog from '@/components/datasets/ImportDatasetDialog.vue';
import { useConversationEvaluation } from '@/composables/useConversationEvaluation';

const route = useRoute();
const { t } = useI18n();
const projectId = route.params.projectId;

// 使用多轮对话数据管理
const {
  conversations,
  loading,
  page,
  rowsPerPage,
  total,
  searchKeyword,
  filterDialogOpen,
  exportLoading,
  filters,
  selectedIds,
  isAllSelected,
  batchDeleteLoading,
  setSearchKeyword,
  setFilterDialogOpen,
  setFilters,
  handleExport,
  handleDelete,
  handleView,
  applyFilters,
  resetFilters,
  handleSearch,
  handlePageChange,
  handleRowsPerPageChange,
  handleBatchDelete,
  handleSelectionChange,
  handleSelectAll
} = useMultiTurnData(projectId);

const projectIdRef = ref(projectId);

// 导出处理：接收 ExportDatasetDialog 的选项并调用后端导出接口
import { exportConversations } from '@/api/conversation';
const handleExportDatasets = async (exportOptions) => {
  try {
    exportLoading.value = true;
    // 构建后端需要的请求体，优先使用 selectedIds
    const payload = {
      conversationIds: selectedIds.value.length > 0 ? selectedIds.value : undefined,
      format: exportOptions.fileFormat || 'json',
      formatType: exportOptions.formatType || 'sharegpt',
      includeCOT: exportOptions.includeCOT || false,
      confirmedOnly: exportOptions.confirmedOnly || false,
      customFields: exportOptions.customFields || undefined
    };

    const response = await exportConversations(projectId, payload);
    // response may be: { content: text, ... } or raw text/string - handle both
    console.debug('[MultiTurnView] export response:', response);
    const data = response;
    let content;
    if (data && typeof data === 'object' && typeof data.content !== 'undefined') {
      content = data.content;
    } else if (typeof data === 'string') {
      content = data;
    } else if (data && data.data && typeof data.data.content !== 'undefined') {
      content = data.data.content;
    } else {
      content = JSON.stringify(data, null, 2);
    }

    // 如果后端返回 count 且为 0，提示用户导出结果为空
    const exportedCount = data && (data.count || (data.data && data.data.count)) ? (data.count || data.data.count) : null;
    if (exportedCount !== null && exportedCount === 0) {
      ElMessage.warning('导出结果为空：未找到符合条件的对话');
    }

    // 生成下载
    const blobType = payload.format === 'csv' ? 'text/csv' : 'application/json';
    const dataBlob = new Blob([content], { type: blobType });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `multi-turn-conversations-${projectId}-${new Date().toISOString().slice(0,10)}.${payload.format === 'csv' ? 'csv' : 'json'}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    ElMessage.success('导出成功');
  } catch (error) {
    console.error('多轮导出失败:', error);
    ElMessage.error(error.message || '导出失败');
  } finally {
    exportLoading.value = false;
  }
};
// 导出弹窗状态
const exportDialogOpen = ref(false);
const importDialogOpen = ref(false);
const openExportDialog = () => {
  console.log('[MultiTurnView] export button clicked, opening dialog');
  try {
    exportDialogOpen.value = true;
  } catch (e) {
    console.error('failed to open export dialog', e);
  }
};
const openImportDialog = () => {
  importDialogOpen.value = true;
};

// 清除选择
const clearSelection = () => {
  selectedIds.value = [];
  isAllSelected.value = false;
};

// 使用多轮评估 composable
const { evaluatingIds, batchEvaluating, handleEvaluateConversation, handleBatchEvaluate } =
  useConversationEvaluation(projectIdRef, () => {
    // refresh list after evaluation
    fetchConversationsList();
  });

// 计算选中数量
const selectedCount = computed(() => {
  return isAllSelected.value ? total.value : selectedIds.value.length;
});

// 选中数量文本
const selectedCountText = computed(() => {
  return t('datasets.selected', '已选中 {count} 项', { count: selectedCount.value });
});

// 获取活跃筛选条件数量
const getActiveFilterCount = () => {
  let count = 0;
  if (filters.value.status !== 'all') count++;
  if (filters.value.scoreRange && (filters.value.scoreRange[0] > 0 || filters.value.scoreRange[1] < 5)) count++;
  if (filters.value.scenario) count++;
  return count;
};

// 防抖搜索
const debouncedSearchKeyword = ref(searchKeyword.value);
const updateDebouncedSearch = useDebounceFn((newVal) => {
  debouncedSearchKeyword.value = newVal;
  setSearchKeyword(newVal);
  handleSearch();
}, 500);

// 搜索查询变化
const handleSearchQueryChange = (value) => {
  setSearchKeyword(value);
  page.value = 1;
};
</script>

<style scoped>
.multi-turn-view {
  padding: 20px;
}

.main-card {
  min-height: calc(100vh - 200px);
}

.card-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.search-action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
  padding: 16px;
  background-color: var(--el-color-primary-light-9);
  border-radius: 8px;
}

/* Ensure SearchBar and ActionBar don't overlap: make search area flexible and allow shrinking */
.search-action-bar :deep(.search-bar) {
  flex: 1 1 auto;
  min-width: 0;
}
.search-action-bar :deep(.action-bar) {
  flex: 0 0 auto;
  z-index: 2;
}

.selected-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 16px;
  background-color: var(--el-color-info-light-9);
  border-radius: 4px;
}

.selected-count {
  font-size: 14px;
  color: var(--el-text-color-regular);
}
</style>

