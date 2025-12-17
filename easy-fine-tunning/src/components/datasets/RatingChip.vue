<template>
  <el-tag
    :type="config.type"
    :effect="config.effect"
    size="small"
    class="rating-chip"
    :style="{ backgroundColor: config.backgroundColor, color: config.color }"
  >
    <el-icon class="star-icon"><Star /></el-icon>
    <span class="rating-text">{{ formatScore(score) }} {{ config.label }}</span>
  </el-tag>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { Star } from '@element-plus/icons-vue';

const props = defineProps({
  score: {
    type: Number,
    default: 0
  }
});

const { t } = useI18n();

const getRatingConfig = (score) => {
  if (score >= 4.5) {
    return {
      type: 'success',
      effect: 'plain',
      backgroundColor: '#e8f5e8',
      color: '#2e7d32',
      label: t('datasets.ratingExcellent', '优秀')
    };
  } else if (score >= 3.5) {
    return {
      type: 'success',
      effect: 'plain',
      backgroundColor: '#f1f8e9',
      color: '#388e3c',
      label: t('datasets.ratingGood', '良好')
    };
  } else if (score >= 2.5) {
    return {
      type: 'warning',
      effect: 'plain',
      backgroundColor: '#fff3e0',
      color: '#f57c00',
      label: t('datasets.ratingAverage', '一般')
    };
  } else if (score >= 1.5) {
    return {
      type: 'danger',
      effect: 'plain',
      backgroundColor: '#ffebee',
      color: '#f44336',
      label: t('datasets.ratingPoor', '较差')
    };
  } else if (score > 0) {
    return {
      type: 'danger',
      effect: 'plain',
      backgroundColor: '#ffebee',
      color: '#d32f2f',
      label: t('datasets.ratingVeryPoor', '很差')
    };
  } else {
    return {
      type: 'info',
      effect: 'plain',
      backgroundColor: '#f5f5f5',
      color: '#757575',
      label: t('datasets.ratingUnrated', '未评分')
    };
  }
};

const config = computed(() => getRatingConfig(props.score));

const formatScore = (score) => {
  if (score === 0) return '';
  return score.toFixed(1);
};
</script>

<style scoped>
.rating-chip {
  white-space: nowrap !important;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  max-width: 100%;
  word-break: keep-all;
}

.star-icon {
  margin-right: 4px;
  flex-shrink: 0;
}

.rating-text {
  white-space: nowrap !important;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
  word-break: keep-all;
}

.rating-chip :deep(.el-tag__content) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap !important;
  word-break: keep-all;
  text-align: center;
}
</style>

