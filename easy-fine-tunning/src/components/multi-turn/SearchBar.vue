<template>
  <div class="search-bar">
    <div class="search-left">
      <el-input
        v-model="localSearchKeyword"
        :placeholder="$t('datasets.searchPlaceholder', '搜索数据集...')"
        clearable
        @keyup.enter="handleSearch"
        @clear="handleClear"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button :icon="Filter" @click="$emit('filter-click')">
        {{ $t('datasets.moreFilters', '更多筛选') }}
      </el-button>
    </div>
    <div class="search-right">
      <el-button
        v-if="selectedCount > 0"
        type="danger"
        :icon="Delete"
        :loading="batchDeleteLoading"
        @click="$emit('batch-delete')"
      >
        {{ $t('datasets.batchDelete', '批量删除') }} ({{ selectedCount }})
      </el-button>
      <el-button
        type="primary"
        :icon="Download"
        :loading="exportLoading"
        @click="$emit('export-click')"
      >
        {{ $t('export.export', '导出') }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { Search, Filter, Delete, Download } from '@element-plus/icons-vue';

const props = defineProps({
  searchKeyword: {
    type: String,
    default: ''
  },
  exportLoading: {
    type: Boolean,
    default: false
  },
  selectedCount: {
    type: Number,
    default: 0
  },
  batchDeleteLoading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['search-change', 'search', 'filter-click', 'export-click', 'batch-delete']);

const localSearchKeyword = ref(props.searchKeyword);

watch(
  () => props.searchKeyword,
  (newVal) => {
    localSearchKeyword.value = newVal;
  }
);

watch(localSearchKeyword, (newVal) => {
  emit('search-change', newVal);
});

const handleSearch = () => {
  emit('search');
};

const handleClear = () => {
  emit('search-change', '');
  emit('search');
};
</script>

<style scoped>
.search-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.search-left {
  display: flex;
  gap: 12px;
  align-items: center;
  flex: 1;
  min-width: 300px;
}

.search-left :deep(.el-input) {
  width: 400px;
}

.search-right {
  display: flex;
  gap: 12px;
  align-items: center;
}
</style>

