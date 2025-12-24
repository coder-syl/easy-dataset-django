<template>
  <div class="image-datasets-view projects-container">
    <el-card v-loading="loading" class="main-card ed-card">
      <template #header>
        <div class="card-header">
          <h3>{{ $t('imageDatasets.title', '图像问答数据集') }}</h3>
        </div>
      </template>

      <!-- 搜索和操作栏 -->
      <div class="search-action-bar">
        <SearchBar
          :search-query="filters.searchQuery.value"
          :search-field="'question'"
          :active-filter-count="filters.getActiveFilterCount()"
          @search-query-change="handleSearchQueryChange"
          @search-field-change="() => {}"
          @more-filters-click="filterDialogOpen = true"
        />
        <ActionBar
          :batch-evaluating="batchEvaluating"
          :selected-count="selectedIds.length"
          :batch-delete-loading="false"
          @batch-delete="handleBatchDeleteClick"
          @batch-evaluate="handleBatchEvaluate"
          @import="() => {}"
          @export="exportDialogOpen = true"
        />
      </div>


      <!-- 数据集列表 -->
      <div class="datasets-content">
        <ImageDatasetList
          :datasets="datasets.data"
          :page="page"
          :rows-per-page="pageSize"
          :total="datasets.total"
          :selected-ids="selectedIds"
          :evaluating-ids="evaluatingIds"
          @view-details="handleViewDetails"
          @delete="handleDeleteDataset"
          @evaluate="handleEvaluateDataset"
          @select-all="handleSelectAll"
          @select-item="handleSelectItem"
          @selection-change="handleSelectionChange"
          @page-change="handlePageChange"
          @rows-per-page-change="handleRowsPerPageChange"
        />
      </div>
    </el-card>

    <!-- 筛选对话框 -->
    <ImageDatasetFilterDialog
      v-model:open="filterDialogOpen"
      v-model:status-filter="filters.statusFilter"
      v-model:score-filter="filters.scoreFilter"
      @reset="handleResetFilters"
      @apply="handleApplyFilters"
    />

    <!-- 导出对话框 -->
    <ExportImageDatasetDialog
      v-model:open="exportDialogOpen"
      @export="handleExport"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useI18n } from 'vue-i18n';
import { Delete } from '@element-plus/icons-vue';
import { useDebounceFn } from '@vueuse/core';
import { useImageDatasets } from '@/composables/useImageDatasets';
import { useImageDatasetFilters } from '@/composables/useImageDatasetFilters';
import { fetchAllDatasetIds } from '@/api/dataset';
import { useImageDatasetExport } from '@/composables/useImageDatasetExport';
import { useImageDatasetEvaluation } from '@/composables/useImageDatasetEvaluation';
import SearchBar from '@/components/datasets/SearchBar.vue';
import ActionBar from '@/components/datasets/ActionBar.vue';
import ImageDatasetList from '@/components/image-datasets/ImageDatasetList.vue';
import ImageDatasetFilterDialog from '@/components/image-datasets/ImageDatasetFilterDialog.vue';
import ExportImageDatasetDialog from '@/components/image-datasets/ExportImageDatasetDialog.vue';

const route = useRoute();
const router = useRouter();
const { t } = useI18n();

const projectId = computed(() => route.params.projectId);

// 筛选
const filters = useImageDatasetFilters(projectId);

// 数据
const { datasets, loading, page, pageSize, fetchDatasets, handleDeleteDataset: deleteDataset } = useImageDatasets(
  projectId,
  computed(() => filters.getFilters())
);

// 导出
const { exportImageDatasets } = useImageDatasetExport(projectId);

// 评估
const { evaluatingIds, batchEvaluating, handleEvaluateDataset: evaluateDataset, handleBatchEvaluate } =
  useImageDatasetEvaluation(projectId, () => fetchDatasets());

// 对话框状态
const filterDialogOpen = ref(false);
const exportDialogOpen = ref(false);

// 选中项
const selectedIds = ref([]);

// 选中数量文本
const selectedCountText = computed(() => {
  return t('datasets.selected', '已选中 {count} 项', { count: selectedIds.value.length });
});

// 防抖搜索
const debouncedSearchQuery = ref(filters.searchQuery.value);
const updateDebouncedSearch = useDebounceFn((newVal) => {
  debouncedSearchQuery.value = newVal;
  filters.searchQuery.value = newVal;
}, 500);

watch(
  () => filters.searchQuery.value,
  (newVal) => {
    updateDebouncedSearch(newVal);
  }
);

// 搜索查询变化
const handleSearchQueryChange = (value) => {
  filters.searchQuery.value = value;
  page.value = 1;
};

// 页面变化
const handlePageChange = (newPage) => {
  page.value = newPage;
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

// 每页行数变化
const handleRowsPerPageChange = (newPageSize) => {
  page.value = 1;
  pageSize.value = newPageSize;
};

// 全选/取消全选
const handleSelectAll = (checked) => {
  try {
    // eslint-disable-next-line no-console
    console.debug('[ImageDatasetsView] handleSelectAll called:', checked, 'selectedBefore', selectedIds.value.length);
  } catch (e) {}
  if (checked) {
    // 先选中当前页以保证即时反馈
    const currentPageIds = (datasets.value.data || []).map((d) => String(d.id));
    selectedIds.value = [...currentPageIds];

    // 异步请求所有匹配 ID（用于跨页全选），若返回则替换 selectedIds
    (async () => {
      try {
        const params = {};
        if (filters.statusFilter && filters.statusFilter.value !== 'all') {
          params.status = filters.statusFilter.value;
        }
        if (filters.scoreFilter && filters.scoreFilter.value) {
          // noop for now — adjust if backend supports
        }
        if (filters.getFilters) {
          // include other filters if needed
          Object.assign(params, filters.getFilters());
        }
        const response = await fetchAllDatasetIds(projectId.value, params);
        const respData = response;
        const raw = respData?.allDatasetIds || respData || [];
        const ids = Array.isArray(raw)
          ? raw.map((it) => (it && typeof it === 'object' ? String(it.id || it._id || it.id_str || '') : String(it))).filter(Boolean)
          : [];
        if (ids.length > 0) {
          selectedIds.value = [...ids];
          try {
            // eslint-disable-next-line no-console
            console.debug('[ImageDatasetsView] fetched all ids count:', ids.length);
          } catch (e) {}
        }
      } catch (error) {
        console.error('获取图像数据集 ID 失败:', error);
      }
    })();
  } else {
    // 取消全选：只取消当前页的选中（保留跨页选中）
    const currentPageIds = (datasets.value.data || []).map((d) => String(d.id));
    selectedIds.value = selectedIds.value.filter((id) => !currentPageIds.includes(String(id)));
  }
};

// 选择单个项
const handleSelectItem = (datasetId) => {
  try {
    // eslint-disable-next-line no-console
    console.debug('[ImageDatasetsView] handleSelectItem toggled:', datasetId, 'selectedBefore', selectedIds.value.length);
  } catch (e) {}
  const index = selectedIds.value.indexOf(datasetId);
  if (index > -1) {
    selectedIds.value.splice(index, 1);
  } else {
    selectedIds.value.push(datasetId);
  }
  try {
    // eslint-disable-next-line no-console
    console.debug('[ImageDatasetsView] selectedAfter', selectedIds.value.length);
  } catch (e) {}
};

// 接收子组件 selection-change 事件
const handleSelectionChange = (ids) => {
  try {
    // eslint-disable-next-line no-console
    console.debug('[ImageDatasetsView] handleSelectionChange from child:', ids);
  } catch (e) {}
  selectedIds.value = Array.isArray(ids) ? [...ids] : [];
};

// 查看详情
const handleViewDetails = (datasetId) => {
  router.push(`/projects/${projectId.value}/image-datasets/${datasetId}`);
};

// 删除数据集
const handleDeleteDataset = async (datasetId) => {
  try {
    await ElMessageBox.confirm(
      t('imageDatasets.deleteConfirm', '确定要删除这个图像数据集吗？'),
      t('common.confirm', '确认'),
      {
        type: 'warning'
      }
    );
    await deleteDataset(datasetId);
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error);
    }
  }
};

// 评估数据集
const handleEvaluateDataset = async (dataset) => {
  await evaluateDataset(dataset);
};

// 重置筛选
const handleResetFilters = () => {
  filters.resetFilters();
  filterDialogOpen.value = false;
  page.value = 1;
};

// 应用筛选
const handleApplyFilters = () => {
  filterDialogOpen.value = false;
  page.value = 1;
};

// 导出
const handleExport = async (exportOptions) => {
  exportDialogOpen.value = false;
  await exportImageDatasets(exportOptions);
};

// 批量删除
const handleBatchDeleteClick = async () => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning(t('datasets.selectItemsFirst', '请先选择要删除的数据集'));
    return;
  }

  try {
    await ElMessageBox.confirm(
      t('datasets.batchDeleteConfirm', '确定要删除选中的 {count} 个数据集吗？', {
        count: selectedIds.value.length
      }),
      t('common.confirm', '确认'),
      {
        type: 'warning'
      }
    );

    // 批量删除
    for (const id of selectedIds.value) {
      try {
        await deleteDataset(id);
      } catch (error) {
        console.error(`删除数据集 ${id} 失败:`, error);
      }
    }

    selectedIds.value = [];
    ElMessage.success(t('datasets.batchDeleteSuccess', '批量删除成功'));
    await fetchDatasets();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error);
    }
  }
};
</script>

<style scoped>
.image-datasets-view {
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
  padding: 12px 16px;
  margin-bottom: 16px;
  background-color: var(--el-color-info-light-9);
  border-radius: 4px;
}

.selected-count {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.datasets-content {
  min-height: 400px;
}
</style>
