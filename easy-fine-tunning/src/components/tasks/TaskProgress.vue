<template>
  <div v-if="totalCount > 0" class="task-progress">
    <el-progress
      :percentage="progress"
      :stroke-width="6"
      :show-text="false"
      style="width: 120px"
    />
    <span class="progress-text">
      {{ completedCount }} / {{ totalCount }} ({{ Math.round(progress) }}%)
    </span>
  </div>
  <span v-else>-</span>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  task: {
    type: Object,
    required: true,
  },
});

const totalCount = computed(() => props.task.totalCount || props.task.total_count || 0);
const completedCount = computed(() => props.task.completedCount || props.task.completed_count || 0);

// 计算进度百分比
const progress = computed(() => {
  if (totalCount.value === 0) return 0;
  return (completedCount.value / totalCount.value) * 100;
});
</script>

<style scoped>
.task-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}
</style>

