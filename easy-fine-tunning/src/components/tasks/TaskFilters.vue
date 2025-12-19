<template>
  <div class="task-filters">
    <el-select
      v-model="localStatusFilter"
      size="default"
      style="width: 120px; margin-right: 12px"
      @change="handleStatusChange"
    >
      <el-option :label="$t('datasets.filterAll', '全部')" value="all" />
      <el-option :label="$t('tasks.status.processing', '处理中')" value="0" />
      <el-option :label="$t('tasks.status.completed', '已完成')" value="1" />
      <el-option :label="$t('tasks.status.failed', '失败')" value="2" />
      <el-option :label="$t('tasks.status.aborted', '已中断')" value="3" />
    </el-select>

    <el-select
      v-model="localTypeFilter"
      size="default"
      style="width: 150px; margin-right: 12px"
      @change="handleTypeChange"
    >
      <el-option :label="$t('datasets.filterAll', '全部')" value="all" />
      <el-option :label="$t('tasks.types.file-processing', '文件处理')" value="file-processing" />
      <el-option :label="$t('tasks.types.text-processing', '文本处理')" value="text-processing" />
      <el-option :label="$t('tasks.types.question-generation', '问题生成')" value="question-generation" />
      <el-option :label="$t('tasks.types.answer-generation', '答案生成')" value="answer-generation" />
      <el-option :label="$t('tasks.types.data-distillation', '数据蒸馏')" value="data-distillation" />
    </el-select>

    <el-tooltip :content="$t('tasks.actions.refresh', '刷新')" placement="top">
      <el-button :icon="Refresh" circle size="default" :loading="loading" @click="handleRefresh" />
    </el-tooltip>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { Refresh } from '@element-plus/icons-vue';

const props = defineProps({
  statusFilter: {
    type: String,
    default: 'all',
  },
  typeFilter: {
    type: String,
    default: 'all',
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:status-filter', 'update:type-filter', 'refresh']);

const localStatusFilter = ref(props.statusFilter);
const localTypeFilter = ref(props.typeFilter);

watch(() => props.statusFilter, (newVal) => {
  localStatusFilter.value = newVal;
});

watch(() => props.typeFilter, (newVal) => {
  localTypeFilter.value = newVal;
});

const handleStatusChange = (value) => {
  emit('update:status-filter', value);
};

const handleTypeChange = (value) => {
  emit('update:type-filter', value);
};

const handleRefresh = () => {
  emit('refresh');
};
</script>

<style scoped>
.task-filters {
  display: flex;
  align-items: center;
}
</style>

