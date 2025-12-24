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
          {{ statsText }}
        </span>
      </div>

      <!-- 右侧：翻页、确认/取消确认、删除按钮 -->
      <div class="right-section">
        <el-button :icon="ArrowLeft" circle @click="handlePrev" />
        <el-button :icon="ArrowRight" circle @click="handleNext" />
        <el-divider direction="vertical" />

        <!-- 确认/取消确认按钮 -->
        <el-button
          v-if="currentDatasetLocal && currentDatasetLocal.confirmed"
          type="warning"
          :icon="RefreshLeft"
          :loading="unconfirmingLocal"
          @click="handleUnconfirm"
        >
          {{ unconfirmingLocal ? $t('common.unconfirming', '取消中...') : $t('datasets.unconfirm', '取消确认') }}
        </el-button>
        <el-button
          v-else
          type="primary"
          :loading="confirmingLocal"
          @click="handleConfirm"
        >
          {{ confirmingLocal ? $t('common.confirming', '确认中...') : $t('datasets.confirmSave', '确认保留') }}
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
import { ArrowLeft, ArrowRight, RefreshLeft, Delete } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import { computed, unref } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  projectId: {
    type: [String, Number],
    required: true
  },
  datasets_all_count: {
    type: Number,
    default: 0
  },
  datasets_confirm_count: {
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

const { t } = useI18n();

const datasetsAll = computed(() => {
  const v = unref(props.datasets_all_count ?? props.datasetsAllCount ?? props.datasetsAllCount);
  return Number(v || 0);
});
const datasetsConfirm = computed(() => {
  const v = unref(props.datasets_confirm_count ?? props.datasetsConfirmCount ?? props.datasetsConfirmCount);
  return Number(v || 0);
});
const confirmingLocal = computed(() => Boolean(unref(props.confirming ?? props.confirmingLocal ?? props.confirming)));
const unconfirmingLocal = computed(() => Boolean(unref(props.unconfirming ?? props.unconfirmingLocal ?? props.unconfirming)));
const currentDatasetLocal = computed(() => unref(props.currentDataset ?? props.current_dataset ?? props.currentDataset) || null);
const regeneratingLocal = computed(() => Boolean(unref(props.regenerating ?? props.regeneratingLocal ?? props.regenerating)));

// compute stats text similar to DatasetHeader, using unwrapped values
const statsText = computed(() => {
  const total = datasetsAll.value;
  const confirmed = datasetsConfirm.value;
  const percentage = total > 0 ? ((confirmed / total) * 100).toFixed(2) : '0.00';
  return t('datasets.stats', { total, confirmed, percentage });
});

const handleBack = () => {
  router.push(`/projects/${props.projectId}/image-datasets`);
};

const handleNavigate = (direction) => {
  console.log('[ImageDatasetHeader] navigate clicked:', direction);
  emit('navigate', direction);
};

const handlePrev = () => {
  console.log('[ImageDatasetHeader] prev clicked');
  handleNavigate('prev');
};

const handleNext = () => {
  console.log('[ImageDatasetHeader] next clicked');
  handleNavigate('next');
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

