<template>
  <div class="task-status-chip">
    <el-icon v-if="status === 0" class="is-loading"><Loading /></el-icon>
    <el-tag :type="statusInfo.color" size="small">
      {{ statusInfo.label }}
    </el-tag>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { Loading } from '@element-plus/icons-vue';

const props = defineProps({
  status: {
    type: Number,
    required: true,
  },
});

const { t } = useI18n();

// 状态映射配置
const STATUS_CONFIG = {
  0: {
    label: t('tasks.status.processing', '处理中'),
    color: 'warning',
  },
  1: {
    label: t('tasks.status.completed', '已完成'),
    color: 'success',
  },
  2: {
    label: t('tasks.status.failed', '失败'),
    color: 'danger',
  },
  3: {
    label: t('tasks.status.aborted', '已中断'),
    color: 'info',
  },
};

const statusInfo = computed(() => {
  return STATUS_CONFIG[props.status] || {
    label: t('tasks.status.unknown', '未知'),
    color: 'info',
  };
});
</script>

<style scoped>
.task-status-chip {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>

