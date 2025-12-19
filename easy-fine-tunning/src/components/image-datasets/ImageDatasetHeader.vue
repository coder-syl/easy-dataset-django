<template>
  <el-card class="header-card">
    <div class="header-row">
      <!-- 左侧：返回按钮和统计信息 -->
      <div class="left-section">
        <el-button :icon="ArrowLeft" @click="handleBack">
          {{ $t('imageDatasets.title', '图像数据集') }}
        </el-button>
        <el-divider direction="vertical" />
        <span class="stats-text">
          {{ $t('imageDatasets.totalDatasets', '共 {count} 个数据集', { count: datasetsAllCount }) }}，
          {{ $t('imageDatasets.confirmedDatasets', '已确认 {count} 个', { count: datasetsConfirmCount }) }}
          ({{ datasetsAllCount > 0 ? ((datasetsConfirmCount / datasetsAllCount) * 100).toFixed(2) : 0 }}%)
        </span>
      </div>

      <!-- 右侧：翻页、确认/取消确认、删除按钮 -->
      <div class="right-section">
        <el-button :icon="ArrowLeft" circle @click="handleNavigate('prev')" />
        <el-button :icon="ArrowRight" circle @click="handleNavigate('next')" />
        <el-divider direction="vertical" />

        <!-- 确认/取消确认按钮 -->
        <el-button
          v-if="currentDataset?.confirmed"
          type="warning"
          :icon="Undo"
          :loading="unconfirming"
          @click="handleUnconfirm"
        >
          {{ unconfirming ? $t('common.unconfirming', '取消中...') : $t('datasets.unconfirm', '取消确认') }}
        </el-button>
        <el-button
          v-else
          type="primary"
          :loading="confirming"
          @click="handleConfirm"
        >
          {{ confirming ? $t('common.confirming', '确认中...') : $t('datasets.confirmSave', '确认保留') }}
        </el-button>

        <el-button
          type="danger"
          :icon="Delete"
          @click="handleDelete"
        >
          {{ $t('common.delete', '删除') }}
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ArrowLeft, ArrowRight, Undo, Delete } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';

const props = defineProps({
  projectId: {
    type: [String, Number],
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
    default: null
  }
});

const emit = defineEmits(['navigate', 'confirm', 'unconfirm', 'delete']);

const router = useRouter();

const handleBack = () => {
  router.push(`/projects/${props.projectId}/image-datasets`);
};

const handleNavigate = (direction) => {
  emit('navigate', direction);
};

const handleConfirm = () => {
  emit('confirm');
};

const handleUnconfirm = () => {
  emit('unconfirm');
};

const handleDelete = () => {
  emit('delete');
};
</script>

<style scoped>
.header-card {
  margin-bottom: 24px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stats-text {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.right-section {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>

