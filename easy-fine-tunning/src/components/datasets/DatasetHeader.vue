<template>
  <el-card class="dataset-header">
    <div class="header-content">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="handleBackToList">
          {{ $t('common.backToList', '返回列表') }}
        </el-button>
        <el-divider direction="vertical" />
        <h3>{{ $t('datasets.datasetDetail', '数据集详情') }}</h3>
        <span class="stats-text">
          {{ statsText }}
        </span>
      </div>
      <div class="header-right">
        <el-button :icon="ArrowLeft" circle @click="$emit('navigate', 'prev')" />
        <el-button :icon="ArrowRight" circle @click="$emit('navigate', 'next')" />
        <el-divider direction="vertical" />
        <el-button
          v-if="currentDataset?.confirmed"
          type="warning"
          :loading="unconfirming"
          :icon="RefreshLeft"
          @click="$emit('unconfirm')"
        >
          {{ $t('datasets.unconfirm', '取消确认') }}
        </el-button>
        <el-button
          v-else
          type="primary"
          :loading="confirming"
          @click="$emit('confirm')"
        >
          {{ $t('datasets.confirmSave', '确认并保存') }}
        </el-button>
        <el-button type="danger" :icon="Delete" @click="$emit('delete')">
          {{ $t('common.delete', '删除') }}
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { ArrowLeft, ArrowRight, Delete, RefreshLeft } from '@element-plus/icons-vue';

const props = defineProps({
  projectId: {
    type: String,
    required: true
  },
  datasetsAllCount: {
    type: Number,
    default: 0
  },
  datasetsConfirmCount: {
    type: Number,
    default: 0
  },
  confirming: {
    type: Boolean,
    default: false
  },
  unconfirming: {
    type: Boolean,
    default: false
  },
  currentDataset: {
    type: Object,
    default: () => ({})
  },
  shortcutsEnabled: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:shortcuts-enabled', 'navigate', 'confirm', 'unconfirm', 'delete']);

const router = useRouter();
const { t } = useI18n();

// 统计文本（使用计算属性避免模板解析错误）
const statsText = computed(() => {
  const percentage = props.datasetsAllCount > 0
    ? ((props.datasetsConfirmCount / props.datasetsAllCount) * 100).toFixed(2)
    : '0.00';
  return t('datasets.stats', '总计：{total}，已确认：{confirmed} ({percentage}%)', {
    total: props.datasetsAllCount,
    confirmed: props.datasetsConfirmCount,
    percentage
  });
});

const handleBackToList = () => {
  router.push(`/projects/${props.projectId}/datasets`);
};
</script>

<style scoped>
.dataset-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.stats-text {
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>

