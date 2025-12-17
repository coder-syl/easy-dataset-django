<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('export.progress', '导出进度')"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
  >
    <div class="progress-content">
      <el-progress
        :percentage="progressPercentage"
        :status="progressPercentage === 100 ? 'success' : undefined"
      />
      <div class="progress-text">
        {{ progressText }}
      </div>
      <div v-if="progress.hasMore" class="has-more-text">
        {{ $t('export.processing', '正在处理中...') }}
      </div>
    </div>
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
  progress: {
    type: Object,
    default: () => ({ processed: 0, total: 0, hasMore: true })
  }
});

const emit = defineEmits(['update:open']);

const dialogVisible = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val)
});

const { t } = useI18n();

const progressPercentage = computed(() => {
  if (props.progress.total === 0) return 0;
  return Math.floor((props.progress.processed / props.progress.total) * 100);
});

// 进度文本（使用计算属性避免模板解析错误）
const progressText = computed(() => {
  return t('export.progressText', '已处理：{processed}/{total}', {
    processed: props.progress.processed,
    total: props.progress.total
  });
});
</script>

<style scoped>
.progress-content {
  padding: 20px 0;
}

.progress-text {
  margin-top: 16px;
  text-align: center;
  color: var(--el-text-color-regular);
}

.has-more-text {
  margin-top: 8px;
  text-align: center;
  color: var(--el-text-color-primary);
  font-size: 14px;
}
</style>

