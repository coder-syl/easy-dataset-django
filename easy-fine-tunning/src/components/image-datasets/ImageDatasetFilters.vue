<template>
  <div class="filters-container">
    <!-- 搜索框 -->
    <el-input
      v-model="localSearchQuery"
      :placeholder="$t('imageDatasets.searchPlaceholder', '搜索问题或答案...')"
      clearable
      class="search-input"
      @input="handleSearchChange"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>

    <!-- 更多筛选按钮 - 带 Badge 显示活跃筛选条件数 -->
    <el-badge :value="activeFilterCount" :hidden="activeFilterCount === 0" class="filter-badge">
      <el-button
        :icon="Filter"
        @click="$emit('more-filters-click')"
      >
        {{ $t('datasets.moreFilters', '更多筛选') }}
      </el-button>
    </el-badge>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { Search, Filter } from '@element-plus/icons-vue';

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  },
  activeFilterCount: {
    type: Number,
    default: 0
  }
});

const emit = defineEmits(['update:searchQuery', 'more-filters-click']);

const localSearchQuery = ref(props.searchQuery);

watch(
  () => props.searchQuery,
  (val) => {
    localSearchQuery.value = val;
  }
);

const handleSearchChange = (val) => {
  emit('update:searchQuery', val);
};
</script>

<style scoped>
.filters-container {
  display: flex;
  gap: 16px;
  align-items: center;
}

.search-input {
  width: 400px;
}

.filter-badge {
  flex-shrink: 0;
}
</style>

