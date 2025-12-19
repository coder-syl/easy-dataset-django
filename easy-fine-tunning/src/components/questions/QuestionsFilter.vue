<template>
  <div class="questions-filter">
    <div class="filter-content">
      <div class="select-area">
        <el-checkbox
          :model-value="isAllSelected"
          :indeterminate="isIndeterminate"
          @change="handleSelectAllChange"
        />
        <span class="select-text">
          {{ selectedQuestionsCount > 0
            ? $t('questions.selectedCount', { count: selectedQuestionsCount })
            : $t('questions.selectAll') }}
          ({{ $t('questions.totalCount', { count: totalQuestions }) }})
        </span>
      </div>

      <div class="filter-area">
        <el-input
          v-model="localSearchTerm"
          :placeholder="$t('questions.searchPlaceholder')"
          clearable
          style="width: 240px"
          @input="handleSearchInput"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-input
          v-model="localChunkNameFilter"
          :placeholder="$t('questions.filterChunkNamePlaceholder')"
          clearable
          style="width: 200px"
          @input="handleChunkNameInput"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select v-model="localSourceTypeFilter" style="width: 140px" @change="handleSourceTypeChange">
          <el-option :label="$t('questions.sourceTypeAll')" value="all" />
          <el-option :label="$t('questions.sourceTypeText')" value="text" />
          <el-option :label="$t('questions.sourceTypeImage')" value="image" />
        </el-select>

        <el-select v-model="localAnswerFilter" style="width: 140px" @change="handleAnswerFilterChange">
          <el-option :label="$t('questions.filterAll')" value="all" />
          <el-option :label="$t('questions.filterAnswered')" value="answered" />
          <el-option :label="$t('questions.filterUnanswered')" value="unanswered" />
        </el-select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { Search } from '@element-plus/icons-vue';

const props = defineProps({
  selectedQuestionsCount: {
    type: Number,
    default: 0
  },
  totalQuestions: {
    type: Number,
    default: 0
  },
  isAllSelected: {
    type: Boolean,
    default: false
  },
  isIndeterminate: {
    type: Boolean,
    default: false
  },
  searchTerm: {
    type: String,
    default: ''
  },
  answerFilter: {
    type: String,
    default: 'all'
  },
  chunkNameFilter: {
    type: String,
    default: ''
  },
  sourceTypeFilter: {
    type: String,
    default: 'all'
  },
  activeTab: {
    type: String,
    default: 'list'
  }
});

const emit = defineEmits([
  'select-all',
  'search-change',
  'filter-change',
  'chunk-name-filter-change',
  'source-type-filter-change'
]);

const localSearchTerm = ref(props.searchTerm);
const localChunkNameFilter = ref(props.chunkNameFilter);
const localSourceTypeFilter = ref(props.sourceTypeFilter);
const localAnswerFilter = ref(props.answerFilter);

watch(() => props.searchTerm, (val) => {
  localSearchTerm.value = val;
});

watch(() => props.chunkNameFilter, (val) => {
  localChunkNameFilter.value = val;
});

watch(() => props.sourceTypeFilter, (val) => {
  localSourceTypeFilter.value = val;
});

watch(() => props.answerFilter, (val) => {
  localAnswerFilter.value = val;
});

const handleSelectAllChange = () => {
  emit('select-all');
};

const handleSearchInput = (val) => {
  emit('search-change', val);
};

const handleChunkNameInput = (val) => {
  emit('chunk-name-filter-change', val);
};

const handleSourceTypeChange = (val) => {
  emit('source-type-filter-change', val);
};

const handleAnswerFilterChange = (val) => {
  emit('filter-change', val);
};
</script>

<style scoped>
.questions-filter {
  padding: 12px 20px;
}

.filter-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.select-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.select-text {
  font-size: 14px;
}

.filter-area {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-area .el-input {
  width: 200px;
}

.filter-area .el-select {
  width: 150px;
}
</style>

