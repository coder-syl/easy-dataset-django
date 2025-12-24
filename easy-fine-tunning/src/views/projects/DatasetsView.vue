<template>
  <div class="datasets-view">
    <el-card v-loading="loading" class="main-card">
      <template #header>
        <div class="card-header">
          <h3>{{ $t('datasets.singleTurn', '单轮问答数据集') }}</h3>
        </div>
      </template>

      <!-- 搜索和操作栏 -->
      <div class="search-action-bar">
        <SearchBar
          :search-query="searchQuery"
          :search-field="searchField"
          :active-filter-count="getActiveFilterCount()"
          @search-query-change="handleSearchQueryChange"
          @search-field-change="handleSearchFieldChange"
          @more-filters-click="filterDialogOpen = true"
        />
        <ActionBar
          :batch-evaluating="batchEvaluating"
          :selected-count="selectedIds.length"
          :batch-delete-loading="(deleteDialog && deleteDialog.value && deleteDialog.value.deleting) || false"
          @batch-delete="handleBatchDelete"
          @batch-evaluate="handleBatchEvaluate"
          @import="importDialogOpen = true"
          @export="exportDialogOpen = true"
        />
      </div>

      <!-- 选中项操作栏 (已移动到顶部ActionBar) -->

      <!-- 数据集列表 -->
      <DatasetList
        :datasets="datasets.data"
        :page="page"
        :rows-per-page="rowsPerPage"
        :total="datasets.total"
        :selected-ids="selectedIds"
        :evaluating-ids="evaluatingIds"
        @view-details="handleViewDetails"
        @delete="handleDeleteClick"
        @evaluate="handleEvaluateDataset"
        @select-all="handleSelectAll"
        @select-item="handleSelectItem"
        @selection-change="handleSelectionChange"
        @page-change="handlePageChange"
        @rows-per-page-change="handleRowsPerPageChange"
      />

      <!-- 筛选对话框 -->
      <FilterDialog
        v-model:open="filterDialogOpen"
        :filter-confirmed="filterConfirmed"
        :filter-has-cot="filterHasCot"
        :filter-is-distill="filterIsDistill"
        :filter-score-range="filterScoreRange"
        :filter-custom-tag="filterCustomTag"
        :filter-note-keyword="filterNoteKeyword"
        :filter-chunk-name="filterChunkName"
        :available-tags="availableTags"
        @update:filter-confirmed="filterConfirmed = $event"
        @update:filter-has-cot="filterHasCot = $event"
        @update:filter-is-distill="filterIsDistill = $event"
        @update:filter-score-range="filterScoreRange = $event"
        @update:filter-custom-tag="filterCustomTag = $event"
        @update:filter-note-keyword="filterNoteKeyword = $event"
        @update:filter-chunk-name="filterChunkName = $event"
        @reset-filters="handleResetFilters"
        @apply-filters="handleApplyFilters"
      />

      <!-- 删除确认对话框 -->
      <DeleteConfirmDialog
        v-model:open="deleteDialog.open"
        :datasets="deleteDialog.datasets"
        :batch="deleteDialog.batch"
        :progress="deleteProgress"
        :deleting="deleteDialog.deleting"
        @confirm="handleDeleteConfirm"
        @close="deleteDialog.open = false"
      />

      <!-- 导出对话框 -->
      <ExportDatasetDialog
        v-model:open="exportDialogOpen"
        :project-id="projectId"
        @export="handleExportDatasets"
      />

      <!-- 导入对话框 -->
      <ImportDatasetDialog
        v-model:open="importDialogOpen"
        :project-id="projectId"
        @import-success="handleImportSuccess"
      />

      <!-- 导出进度对话框 -->
      <ExportProgressDialog v-model:open="exportProgress.show" :progress="exportProgress" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Delete } from '@element-plus/icons-vue';
import { useDebounceFn } from '@vueuse/core';
import {
  fetchDatasets,
  fetchAllDatasetIds,
  deleteDataset,
  batchEvaluateDatasets
} from '@/api/dataset';
import { fetchDatasetTags } from '@/api/dataset';
import { useDatasetFilters } from '@/composables/useDatasetFilters';
import { useDatasetExport } from '@/composables/useDatasetExport';
import { useDatasetEvaluation } from '@/composables/useDatasetEvaluation';
import SearchBar from '@/components/datasets/SearchBar.vue';
import ActionBar from '@/components/datasets/ActionBar.vue';
import DatasetList from '@/components/datasets/DatasetList.vue';
import FilterDialog from '@/components/datasets/FilterDialog.vue';
import DeleteConfirmDialog from '@/components/datasets/DeleteConfirmDialog.vue';
import ExportDatasetDialog from '@/components/datasets/ExportDatasetDialog.vue';
import ImportDatasetDialog from '@/components/datasets/ImportDatasetDialog.vue';
import ExportProgressDialog from '@/components/datasets/ExportProgressDialog.vue';
import { useModelStore } from '@/stores/model';

const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const projectId = route.params.projectId;
const modelStore = useModelStore();

// 数据状态
const loading = ref(false);
const datasets = ref({ data: [], total: 0, confirmedCount: 0 });
const selectedIds = ref([]);
const availableTags = ref([]);
const filterDialogOpen = ref(false);

// 删除对话框状态
const deleteDialog = ref({
  open: false,
  datasets: [],
  batch: false,
  deleting: false
});

// 删除进度状态
const deleteProgress = ref({
  total: 0,
  completed: 0,
  percentage: 0
});

// 导出对话框状态
const exportDialogOpen = ref(false);
const importDialogOpen = ref(false);

// 导出进度状态
const exportProgress = ref({
  show: false,
  processed: 0,
  total: 0,
  hasMore: true
});

// 使用筛选条件管理
const {
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
  isInitialized,
  getActiveFilterCount,
  resetFilters
} = useDatasetFilters(projectId);

// 使用数据集导出
const { exportDatasets, exportDatasetsStreaming } = useDatasetExport(projectId);

// 使用数据集评估
const { evaluatingIds, batchEvaluating, handleEvaluateDataset, handleBatchEvaluate } =
  useDatasetEvaluation(projectId, () => getDatasetsList(true));

// 选中数量文本（使用计算属性避免模板解析错误）
const selectedCountText = computed(() => {
  return t('datasets.selected', '已选中 {count} 项', { count: selectedIds.value.length });
});

// 防抖搜索
const debouncedSearchQuery = ref(searchQuery.value);
const updateDebouncedSearch = useDebounceFn((newVal) => {
  debouncedSearchQuery.value = newVal;
}, 500);

watch(searchQuery, (newVal) => {
  updateDebouncedSearch(newVal);
});

// 获取数据集列表
const getDatasetsList = async (forceRefresh = false) => {
  try {
    loading.value = true;
    const params = {
      page: page.value,
      size: rowsPerPage.value
    };

    if (filterConfirmed.value !== 'all') {
      params.status = filterConfirmed.value;
    }

    if (debouncedSearchQuery.value) {
      params.input = encodeURIComponent(debouncedSearchQuery.value);
      params.field = searchField.value;
    }

    if (filterHasCot.value !== 'all') {
      params.hasCot = filterHasCot.value;
    }

    if (filterIsDistill.value !== 'all') {
      params.isDistill = filterIsDistill.value;
    }

    if (filterScoreRange.value[0] > 0 || filterScoreRange.value[1] < 5) {
      params.scoreRange = `${filterScoreRange.value[0]}-${filterScoreRange.value[1]}`;
    }

    if (filterCustomTag.value) {
      params.customTag = encodeURIComponent(filterCustomTag.value);
    }

    if (filterNoteKeyword.value) {
      params.noteKeyword = encodeURIComponent(filterNoteKeyword.value);
    }

    if (filterChunkName.value) {
      params.chunkName = encodeURIComponent(filterChunkName.value);
    }

    if (forceRefresh) {
      params._t = Date.now();
    }

    const response = await fetchDatasets(projectId, params);
    // HTTP拦截器已经处理了 {code: 0, data: {...}} 格式，response 已经是 data 部分
    // 兼容多种数据格式: {data: [], total: number} 或 {datasets: [], total: number} 或直接是数组
    const respData = response;
    const list = respData?.data || respData?.datasets || (Array.isArray(respData) ? respData : []);
    const total = respData?.total || respData?.count || list.length || 0;
    const confirmedCount = respData?.confirmedCount || 0;
    
    datasets.value = {
      data: list,
      total,
      confirmedCount
    };
  } catch (error) {
    console.error('获取数据集列表失败:', error);
    ElMessage.error(error.message || t('datasets.fetchFailed', '获取数据集列表失败'));
    datasets.value = { data: [], total: 0, confirmedCount: 0 };
  } finally {
    loading.value = false;
  }
};

// 获取可用标签
const fetchAvailableTags = async () => {
  try {
    const response = await fetchDatasetTags(projectId);
    // HTTP拦截器已经处理了 {code: 0, data: {...}} 格式
    const data = response;
    availableTags.value = data?.tags?.map((tag) => tag.tag) || data?.tags || [];
  } catch (error) {
    console.error('获取标签失败:', error);
  }
};

// 监听筛选条件变化（排除搜索查询，搜索查询由防抖处理）
watch(
  [
    page,
    rowsPerPage,
    filterConfirmed,
    filterHasCot,
    filterIsDistill,
    filterScoreRange,
    filterCustomTag,
    filterNoteKeyword,
    filterChunkName,
    searchField,
    isInitialized
  ],
  () => {
    if (isInitialized.value) {
      getDatasetsList();
    }
  },
  { deep: true }
);

// 监听防抖后的搜索查询变化
watch(debouncedSearchQuery, () => {
  if (isInitialized.value) {
    page.value = 1;
    getDatasetsList();
  }
});

// 初始化
onMounted(() => {
  // 等待筛选条件从localStorage恢复后再获取数据
  const initData = () => {
    if (isInitialized.value) {
      getDatasetsList();
      fetchAvailableTags();
    }
  };
  
  if (isInitialized.value) {
    initData();
  } else {
    watch(isInitialized, (val) => {
      if (val) {
        initData();
      }
    });
  }
});

// 处理搜索查询变化
const handleSearchQueryChange = (value) => {
  searchQuery.value = value;
  page.value = 1;
};

// 处理搜索字段变化
const handleSearchFieldChange = (value) => {
  searchField.value = value;
  page.value = 1;
};

// 处理页码变化
const handlePageChange = (newPage) => {
  // Element Plus 的页码从 1 开始，API 也从 1 开始，直接使用
  page.value = newPage;
};

// 处理每页行数变化
const handleRowsPerPageChange = (newRowsPerPage) => {
  page.value = 1;
  rowsPerPage.value = newRowsPerPage;
};

// 处理查看详情
const handleViewDetails = (datasetId) => {
  if (!datasetId || !projectId) {
    console.error('Missing datasetId or projectId:', { datasetId, projectId });
    return;
  }
  // 确保 datasetId 是字符串
  // Vue Router 会自动处理URL编码，所以直接使用ID即可
  const id = String(datasetId);
  console.log('Navigating to dataset detail:', { projectId, datasetId: id });
  router.push(`/projects/${projectId}/datasets/${id}`);
};

// 处理删除点击
const handleDeleteClick = (dataset) => {
  deleteDialog.value = {
    open: true,
    datasets: [dataset],
    batch: false,
    deleting: false
  };
};

// 处理批量删除点击
const handleBatchDeleteClick = () => {
  deleteDialog.value = {
    open: true,
    datasets: selectedIds.value.map((id) => ({ id })),
    batch: true,
    deleting: false,
    count: selectedIds.value.length
  };
};

// 处理删除确认
const handleDeleteConfirm = async () => {
  if (deleteDialog.value.batch) {
    deleteDialog.value.deleting = true;
    await handleBatchDelete();
    resetDeleteProgress();
  } else {
    const [dataset] = deleteDialog.value.datasets;
    if (dataset) {
      await handleDelete(dataset);
    }
  }
  selectedIds.value = [];
  getDatasetsList();
  deleteDialog.value.open = false;
};

// 批量删除
const handleBatchDelete = async () => {
  try {
    const total = selectedIds.value.length;
    deleteProgress.value = { total, completed: 0, percentage: 0 };

    // 并发删除，限制并发数为 3
    const concurrency = 3;
    for (let i = 0; i < selectedIds.value.length; i += concurrency) {
      const batch = selectedIds.value.slice(i, i + concurrency);
      await Promise.all(
        batch.map(async (datasetId) => {
          try {
            await deleteDataset(projectId, datasetId);
            deleteProgress.value.completed++;
            deleteProgress.value.percentage = Math.floor(
              (deleteProgress.value.completed / deleteProgress.value.total) * 100
            );
          } catch (error) {
            console.error(`删除数据集 ${datasetId} 失败:`, error);
          }
        })
      );
    }

    ElMessage.success(t('common.deleteSuccess', '删除成功'));
  } catch (error) {
    ElMessage.error(error.message || t('common.deleteFailed', '删除失败'));
  } finally {
    deleteDialog.value.deleting = false;
  }
};

// 删除单个数据集
const handleDelete = async (dataset) => {
  try {
    await deleteDataset(projectId, dataset.id);
    ElMessage.success(t('datasets.deleteSuccess', '删除成功'));
    getDatasetsList();
  } catch (error) {
    ElMessage.error(error.message || t('datasets.deleteFailed', '删除失败'));
  }
};

// 重置删除进度
const resetDeleteProgress = () => {
  deleteProgress.value = {
    total: deleteDialog.value.count || 0,
    completed: 0,
    percentage: 0
  };
};

// 处理全选/取消全选
const handleSelectAll = async (checked) => {
  try {
    // eslint-disable-next-line no-console
    console.debug('[DatasetsView] handleSelectAll called:', checked, 'selectedBefore', selectedIds.value.length);
  } catch (e) {}
  if (checked) {
    // 先立即选中当前页以保证 UI 响应性
    try {
      const currentPageIds = (datasets.value.data || []).map((d) => String(d.id));
      selectedIds.value = currentPageIds;
    } catch (e) {
      selectedIds.value = [];
    }

    // 同步后台请求所有匹配的 ID（如果用户期望跨页全选）
    try {
      const params = {};
      if (filterConfirmed.value !== 'all') {
        params.status = filterConfirmed.value;
      }
      if (debouncedSearchQuery.value) {
        params.input = encodeURIComponent(debouncedSearchQuery.value);
        params.field = searchField.value;
      }
      if (filterHasCot.value !== 'all') {
        params.hasCot = filterHasCot.value;
      }
      if (filterIsDistill.value !== 'all') {
        params.isDistill = filterIsDistill.value;
      }
      if (filterScoreRange.value[0] > 0 || filterScoreRange.value[1] < 5) {
        params.scoreRange = `${filterScoreRange.value[0]}-${filterScoreRange.value[1]}`;
      }
      if (filterCustomTag.value) {
        params.customTag = encodeURIComponent(filterCustomTag.value);
      }
      if (filterNoteKeyword.value) {
        params.noteKeyword = encodeURIComponent(filterNoteKeyword.value);
      }
      if (filterChunkName.value) {
        params.chunkName = encodeURIComponent(filterChunkName.value);
      }

      const response = await fetchAllDatasetIds(projectId, params);
      const respData = response;
      const raw = respData?.allDatasetIds || respData || [];
      const ids = Array.isArray(raw)
        ? raw.map((it) => (it && typeof it === 'object' ? String(it.id || it._id || it.id_str || '') : String(it))).filter(Boolean)
        : [];
      // 如果请求返回了更完整的 ID 列表，替换本地 selectedIds
      if (ids.length > 0) {
        selectedIds.value = ids;
      }
    } catch (error) {
      console.error('获取数据集ID失败:', error);
      ElMessage.error(error.message || t('datasets.fetchIdsFailed', '获取数据集ID失败'));
    }
  } else {
    // 取消全选：只取消当前页的选中（保留跨页选中）
    const currentPageIds = (datasets.value.data || []).map((d) => String(d.id));
    selectedIds.value = selectedIds.value.filter((id) => !currentPageIds.includes(String(id)));
  }
};

// 处理单个选择
const handleSelectItem = (datasetId) => {
  try {
    // eslint-disable-next-line no-console
    console.debug('[DatasetsView] handleSelectItem toggled:', datasetId, 'selectedBefore', selectedIds.value.length);
  } catch (e) {}
  const index = selectedIds.value.indexOf(datasetId);
  if (index > -1) {
    selectedIds.value.splice(index, 1);
  } else {
    selectedIds.value.push(datasetId);
  }
  try {
    // eslint-disable-next-line no-console
    console.debug('[DatasetsView] selectedAfter', selectedIds.value.length);
  } catch (e) {}
};

// 接收子组件 el-table 的 selection-change 事件，更新 selectedIds
const handleSelectionChange = (ids) => {
  try {
    // eslint-disable-next-line no-console
    console.debug('[DatasetsView] handleSelectionChange from child:', ids);
  } catch (e) {}
  selectedIds.value = Array.isArray(ids) ? [...ids] : [];
};

// 处理导出数据集
const handleExportDatasets = async (exportOptions) => {
  try {
    const exportOptionsWithSelection = exportOptions.balanceMode
      ? { ...exportOptions }
      : { ...exportOptions, ...(selectedIds.value.length > 0 && { selectedIds: selectedIds.value }) };

    const balancedTotal = Array.isArray(exportOptions.balanceConfig)
      ? exportOptions.balanceConfig.reduce((sum, c) => sum + (parseInt(c.maxCount) || 0), 0)
      : 0;
    const totalCount = exportOptions.balanceMode
      ? balancedTotal
      : selectedIds.value.length > 0
        ? selectedIds.value.length
        : datasets.value.total || 0;

    const STREAMING_THRESHOLD = 1000;
    const needsChunkContent =
      exportOptions.formatType === 'custom' && exportOptions.customFields?.includeChunk;

    let success = false;

    if (totalCount > STREAMING_THRESHOLD || needsChunkContent) {
      exportProgress.value = { show: true, processed: 0, total: totalCount, hasMore: true };

      success = await exportDatasetsStreaming(exportOptionsWithSelection, (progress) => {
        exportProgress.value = {
          ...exportProgress.value,
          processed: progress.processed,
          hasMore: progress.hasMore
        };
      });

      exportProgress.value = { show: false, processed: 0, total: 0, hasMore: false };
    } else {
      success = await exportDatasets(exportOptionsWithSelection);
    }

    if (success) {
      exportDialogOpen.value = false;
    }
  } catch (error) {
    console.error('Export failed:', error);
    exportProgress.value = { show: false, processed: 0, total: 0, hasMore: false };
  }
};

// 处理导入成功
const handleImportSuccess = () => {
  getDatasetsList();
  ElMessage.success(t('import.importSuccess', '数据集导入成功'));
};

// 处理重置筛选
const handleResetFilters = () => {
  resetFilters();
  getDatasetsList();
};

// 处理应用筛选
const handleApplyFilters = () => {
  filterDialogOpen.value = false;
  page.value = 1;
  getDatasetsList();
};
</script>

<style scoped>
.datasets-view {
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

.selected-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background-color: var(--el-color-info-light-9);
  border-radius: 8px;
}

.selected-count {
  color: var(--el-text-color-regular);
  font-size: 14px;
}
</style>
