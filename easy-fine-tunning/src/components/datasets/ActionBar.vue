<template>
  <div class="action-bar">
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
import { DataAnalysis, Upload, Download } from '@element-plus/icons-vue';

defineProps({
  batchEvaluating: {
    type: Boolean,
    default: false
  }
});

defineEmits(['batch-evaluate', 'import', 'export']);
</script>

<style scoped>
.action-bar {
  display: flex;
  gap: 12px;
}
</style>

