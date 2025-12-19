<template>
  <div class="image-dataset-detail-view">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
    </div>

    <!-- 无数据状态 -->
    <el-alert
      v-else-if="!currentDataset"
      :title="$t('imageDatasets.notFound', '数据集不存在')"
      type="error"
      :closable="false"
    />

    <!-- 主要内容 -->
    <template v-else>
      <!-- 顶部导航栏 -->
      <ImageDatasetHeader
        :project-id="projectId"
        :datasets-all-count="datasetsAllCount"
        :datasets-confirm-count="datasetsConfirmCount"
        :confirming="confirming"
        :unconfirming="unconfirming"
        :current-dataset="currentDataset"
        @navigate="handleNavigate"
        @confirm="handleConfirm"
        @unconfirm="handleUnconfirm"
        @delete="handleDelete"
      />

      <!-- 主要布局：左右分栏 -->
      <div class="content-layout">
        <!-- 左侧主要内容区域 -->
        <DatasetContent
          :dataset="currentDataset"
          :project-id="projectId"
          @answer-change="handleAnswerChange"
        />

        <!-- 右侧固定侧边栏 -->
        <DatasetSidebar
          :dataset="currentDataset"
          :project-id="projectId"
          @update="handleUpdate"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { Loading } from '@element-plus/icons-vue';
import { useImageDatasetDetails } from '@/composables/useImageDatasetDetails';
import ImageDatasetHeader from '@/components/image-datasets/ImageDatasetHeader.vue';
import DatasetContent from '@/components/image-datasets/DatasetContent.vue';
import DatasetSidebar from '@/components/image-datasets/DatasetSidebar.vue';

const route = useRoute();

const projectId = computed(() => route.params.projectId);
const datasetId = computed(() => route.params.datasetId);

const {
  currentDataset,
  loading,
  confirming,
  unconfirming,
  datasetsAllCount,
  datasetsConfirmCount,
  updateDataset,
  handleNavigate,
  handleConfirm,
  handleUnconfirm,
  handleDelete
} = useImageDatasetDetails(projectId, datasetId);

// 处理答案变化
const handleAnswerChange = async (newAnswer) => {
  await updateDataset({ answer: newAnswer });
};

// 处理元数据更新
const handleUpdate = async (updates) => {
  await updateDataset(updates);
};
</script>

<style scoped>
.image-dataset-detail-view {
  padding: 20px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 70vh;
}

.content-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}
</style>

