<template>
  <div class="dataset-detail-view">
    <el-card v-loading="loading">
      <!-- 顶部导航栏 -->
      <DatasetHeader
        :project-id="projectId"
        :datasets-all-count="datasetsAllCount"
        :datasets-confirm-count="datasetsConfirmCount"
        :confirming="confirming"
        :unconfirming="unconfirming"
        :current-dataset="currentDataset"
        :shortcuts-enabled="shortcutsEnabled"
        @update:shortcuts-enabled="setShortcutsEnabled"
        @navigate="handleNavigate"
        @confirm="handleConfirm"
        @unconfirm="handleUnconfirm"
        @delete="handleDelete"
      />

      <!-- 主要布局：左右分栏 -->
      <div class="main-layout">
        <!-- 左侧主要内容区域 -->
        <div class="main-content">
          <el-card>
            <EditableField
              :label="$t('datasets.question', '问题')"
              :value="questionValue"
              :editing="editingQuestion"
              @edit="setEditingQuestion(true)"
              @input="setQuestionValue"
              @save="() => handleSave('question', questionValue)"
              :dataset="currentDataset"
              @cancel="() => {
                setEditingQuestion(false);
                setQuestionValue(currentDataset?.question || '');
              }"
            />

            <EditableField
              :label="$t('datasets.answer', '答案')"
              :value="answerValue"
              :editing="editingAnswer"
              @edit="setEditingAnswer(true)"
              @input="setAnswerValue"
              @save="() => handleSave('answer', answerValue)"
              @cancel="() => {
                setEditingAnswer(false);
                setAnswerValue(currentDataset?.answer || '');
              }"
              :dataset="currentDataset"
              @optimize="handleOpenOptimizeDialog"
              :token-count="answerTokens"
              :optimizing="optimizeDialog.loading"
            />

            <EditableField
              :label="$t('datasets.cot', '思维链')"
              :value="cotValue"
              :editing="editingCot"
              @edit="setEditingCot(true)"
              @input="setCotValue"
              @save="() => handleSave('cot', cotValue)"
              :dataset="currentDataset"
              @cancel="() => {
                setEditingCot(false);
                setCotValue(currentDataset?.cot || '');
              }"
              :token-count="cotTokens"
            />
          </el-card>
        </div>

        <!-- 右侧固定侧边栏 -->
        <div class="sidebar">
          <!-- 数据集元数据信息 -->
          <DatasetMetadata
            :current-dataset="currentDataset"
            :project-id="projectId"
            @view-chunk="handleViewChunk"
          />

          <!-- 评分、标签、备注区域 -->
          <DatasetRatingSection
            :dataset="currentDataset"
            :project-id="projectId"
            @update="fetchDatasets"
          />
        </div>
      </div>

      <!-- 消息提示 -->
      <el-drawer
        v-model="snackbar.open"
        :with-header="false"
        size="300px"
        direction="btt"
        :show-close="false"
      >
        <el-alert
          :title="snackbar.message"
          :type="snackbar.severity"
          :closable="true"
          @close="snackbar.open = false"
        />
      </el-drawer>

      <!-- AI优化对话框 -->
      <OptimizeDialog
        v-model:open="optimizeDialog.open"
        @confirm="handleOptimize"
        @close="handleCloseOptimizeDialog"
      />

      <!-- 文本块详情对话框 -->
      <ChunkViewDialog
        v-model:open="viewDialogOpen"
        :chunk="viewChunk"
        @close="handleCloseViewDialog"
      />
    </el-card>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router';
import { computed } from 'vue';
import { useDatasetDetails } from '@/composables/useDatasetDetails';
import DatasetHeader from '@/components/datasets/DatasetHeader.vue';
import DatasetMetadata from '@/components/datasets/DatasetMetadata.vue';
import EditableField from '@/components/datasets/EditableField.vue';
import DatasetRatingSection from '@/components/datasets/DatasetRatingSection.vue';
import OptimizeDialog from '@/components/datasets/OptimizeDialog.vue';
import ChunkViewDialog from '@/components/datasets/ChunkViewDialog.vue';

const route = useRoute();
const router = useRouter();
// 使用 computed 包装路由参数，使其在路由变化时自动更新
const projectId = computed(() =>
  typeof route.params.projectId === 'string'
    ? route.params.projectId
    : String(route.params.projectId)
);
const datasetId = computed(() =>
  typeof route.params.datasetId === 'string'
    ? route.params.datasetId
    : String(route.params.datasetId)
);

const {
  currentDataset,
  loading,
  editingAnswer,
  editingCot,
  editingQuestion,
  answerValue,
  cotValue,
  questionValue,
  snackbar,
  confirming,
  unconfirming,
  optimizeDialog,
  viewDialogOpen,
  viewChunk,
  datasetsAllCount,
  datasetsConfirmCount,
  answerTokens,
  cotTokens,
  shortcutsEnabled,
  setShortcutsEnabled,
  setSnackbar,
  setAnswerValue,
  setCotValue,
  setQuestionValue,
  setEditingAnswer,
  setEditingCot,
  setEditingQuestion,
  handleNavigate,
  handleConfirm,
  handleUnconfirm,
  handleSave,
  handleDelete,
  handleOpenOptimizeDialog,
  handleCloseOptimizeDialog,
  handleOptimize,
  handleViewChunk,
  handleCloseViewDialog,
  fetchDatasets
} = useDatasetDetails(projectId, datasetId);
</script>

<style scoped>
.dataset-detail-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.main-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  margin-top: 24px;
}

.main-content {
  flex: 1;
  min-width: 0;
}

.sidebar {
  width: 360px;
  position: sticky;
  top: 24px;
  max-height: calc(100vh - 48px);
  overflow-y: auto;
}
</style>

