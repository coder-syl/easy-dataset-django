<template>
  <div class="action-bar">
    <el-button
      :type="selectedCount > 0 ? 'danger' : 'default'"
 
      :icon="Delete"
      :loading="batchDeleteLoading"
      :disabled="selectedCount === 0"
      @click="$emit('batch-delete')"
    >
      {{ $t('datasets.batchDelete', '批量删除') }}<span v-if="selectedCount">({{ selectedCount }})</span>
    </el-button>
    <el-button
      :icon="DataAnalysis"
      :loading="batchEvaluating"
      @click="$emit('batch-evaluate')"
    >
      {{ batchEvaluating ? $t('datasets.evaluating', '评估中...') : $t('datasets.batchEvaluate', '批量评估') }}
    </el-button>

    <el-button :icon="Upload" @click="$emit('import')">
      {{ $t('import.title', '导入') }}
    </el-button>
    <el-button :icon="Download" @click="$emit('export')">
      {{ $t('export.title', '导出') }}
    </el-button>
  </div>
</template>

<script setup>
import { DataAnalysis, Upload, Download, Delete } from '@element-plus/icons-vue';

defineProps({
  batchEvaluating: {
    type: Boolean,
    default: false
  }
  ,selectedCount: {
    type: Number,
    default: 0
  }
  ,batchDeleteLoading: {
    type: Boolean,
    default: false
  }
});

defineEmits(['batch-evaluate', 'import', 'export', 'batch-delete']);
</script>

<style scoped>
.action-bar {
  display: flex;
  gap: 12px;
}
</style>

