<template>
  <div class="multi-turn-view">
    <el-card v-loading="loading" class="main-card">
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
          @search-change="setSearchKeyword"
          @search="handleSearch"
          @filter-click="setFilterDialogOpen(true)"
          @export-click="handleExport"
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
        @view="handleView"
        @delete="handleDelete"
        @selection-change="handleSelectionChange"
        @select-all="handleSelectAll"
        @page-change="handlePageChange"
        @rows-per-page-change="handleRowsPerPageChange"
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
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useMultiTurnData } from '@/composables/useMultiTurnData';
import SearchBar from '@/components/multi-turn/SearchBar.vue';
import ConversationTable from '@/components/multi-turn/ConversationTable.vue';
import FilterDialog from '@/components/multi-turn/FilterDialog.vue';

const route = useRoute();
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

// 计算选中数量
const selectedCount = computed(() => {
  return isAllSelected.value ? total.value : selectedIds.value.length;
});
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
</style>

