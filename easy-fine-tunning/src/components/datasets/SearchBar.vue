<template>
  <div class="search-bar">
    <el-input
      v-model="localSearchQuery"
      :placeholder="$t('datasets.searchPlaceholder', '搜索数据集...')"
      clearable
      @input="handleInput"
      @clear="handleClear"
    >
      <template #prepend>
        <el-select v-model="localSearchField" style="width: 120px" @change="handleFieldChange">
          <el-option :label="$t('datasets.fieldQuestion', '问题')" value="question" />
          <el-option :label="$t('datasets.fieldAnswer', '答案')" value="answer" />
          <el-option :label="$t('datasets.fieldCOT', '思维链')" value="cot" />
          <el-option :label="$t('datasets.fieldLabel', '标签')" value="questionLabel" />
        </el-select>
      </template>
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>
    <el-badge :value="activeFilterCount" :hidden="activeFilterCount === 0">
      <el-button :icon="Filter" @click="$emit('more-filters-click')">
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
  searchField: {
    type: String,
    default: 'question'
  },
  activeFilterCount: {
    type: Number,
    default: 0
  }
});

const emit = defineEmits(['search-query-change', 'search-field-change', 'more-filters-click']);

const localSearchQuery = ref(props.searchQuery);
const localSearchField = ref(props.searchField);

watch(
  () => props.searchQuery,
  (newVal) => {
    localSearchQuery.value = newVal;
  }
);

watch(
  () => props.searchField,
  (newVal) => {
    localSearchField.value = newVal;
  }
);

const handleInput = (value) => {
  emit('search-query-change', value);
};

const handleClear = () => {
  emit('search-query-change', '');
};

const handleFieldChange = (value) => {
  emit('search-field-change', value);
};
</script>

<style scoped>
.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-bar :deep(.el-input) {
  width: 400px;
}
</style>

