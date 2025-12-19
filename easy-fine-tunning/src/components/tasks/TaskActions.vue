<template>
  <div class="task-actions">
    <el-tooltip
      v-if="task.status === 0"
      :content="$t('tasks.actions.abort', '中断任务')"
      placement="top"
    >
      <el-button
        :icon="CircleClose"
        circle
        size="small"
        type="warning"
        @click="handleAbort"
      />
    </el-tooltip>
    <el-tooltip
      v-else
      :content="$t('tasks.actions.delete', '删除任务')"
      placement="top"
    >
      <el-button
        :icon="Delete"
        circle
        size="small"
        @click="handleDelete"
      />
    </el-tooltip>
  </div>
</template>

<script setup>
import { CircleClose, Delete } from '@element-plus/icons-vue';

const props = defineProps({
  task: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['abort', 'delete']);

const handleAbort = () => {
  emit('abort', props.task.id);
};

const handleDelete = () => {
  emit('delete', props.task.id);
};
</script>

<style scoped>
.task-actions {
  display: flex;
  justify-content: flex-end;
}
</style>

