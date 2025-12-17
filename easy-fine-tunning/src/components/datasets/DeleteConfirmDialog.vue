<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('common.confirmDelete', '确认删除')"
    width="500px"
    @close="handleClose"
  >
    <div v-if="batch">
      <p>{{ batchDeleteConfirmText }}</p>
      <el-progress
        v-if="deleting"
        :percentage="progress.percentage"
        :status="progress.percentage === 100 ? 'success' : undefined"
      />
      <div v-if="deleting" class="progress-text">
        {{ deletingProgressText }}
      </div>
    </div>
    <div v-else>
      <p>{{ $t('datasets.deleteConfirm', '确定要删除这条数据吗？此操作不可撤销。') }}</p>
      <div v-if="datasets.length > 0" class="dataset-preview">
        <p class="preview-label">{{ $t('datasets.question', '问题') }}:</p>
        <p class="preview-text">{{ datasets[0].question }}</p>
      </div>
    </div>

    <template #footer>
      <el-button :disabled="deleting" @click="handleClose">{{ $t('common.cancel', '取消') }}</el-button>
      <el-button type="danger" :loading="deleting" @click="handleConfirm">
        {{ $t('common.confirm', '确认') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  datasets: {
    type: Array,
    default: () => []
  },
  batch: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Object,
    default: () => ({ total: 0, completed: 0, percentage: 0 })
  },
  deleting: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:open', 'confirm', 'close']);

const { t } = useI18n();

const dialogVisible = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val)
});

// 批量删除确认文本（使用计算属性避免模板解析错误）
const batchDeleteConfirmText = computed(() => {
  return t('datasets.batchDeleteConfirm', '确定要删除选中的 {count} 条数据吗？此操作不可撤销。', {
    count: props.datasets.length
  });
});

// 删除进度文本（使用计算属性避免模板解析错误）
const deletingProgressText = computed(() => {
  return t('datasets.deletingProgress', '正在删除：{completed}/{total}', {
    completed: props.progress.completed,
    total: props.progress.total
  });
});

const handleClose = () => {
  emit('close');
};

const handleConfirm = () => {
  emit('confirm');
};
</script>

<style scoped>
.progress-text {
  margin-top: 12px;
  text-align: center;
  color: var(--el-text-color-regular);
}

.dataset-preview {
  margin-top: 16px;
  padding: 12px;
  background-color: var(--el-bg-color-page);
  border-radius: 4px;
}

.preview-label {
  font-weight: 600;
  margin-bottom: 8px;
}

.preview-text {
  color: var(--el-text-color-regular);
  word-break: break-word;
}
</style>

