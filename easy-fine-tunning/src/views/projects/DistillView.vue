<template>
  <div class="distill-view">
    <el-card class="distill-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="title-area">
            <h3 class="title-text">{{ t('distill.title') }}</h3>
            <span class="title-sub">{{ t('distill.description') }}</span>
          </div>
          <div class="header-actions">
            <el-button
              type="primary"
              size="default"
              @click="openAutoDistillDialog"
              :disabled="!selectedModel"
            >
              {{ t('distill.autoDistillButton') }}
            </el-button>
            <el-button
              type="primary"
              plain
              size="default"
              @click="openTagDialog()"
              :disabled="!selectedModel"
            >
              {{ t('distill.generateRootTags') }}
            </el-button>
          </div>
        </div>
      </template>

      <el-alert
        v-if="error"
        type="error"
        :closable="false"
        class="mb-16"
      >
        {{ error }}
      </el-alert>

      <div class="stats-row" v-if="stats">
        <div class="stat-item">
          <div class="stat-label">{{ t('distill.tagsCount') }}</div>
          <div class="stat-value">{{ stats.tagsCount }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">{{ t('distill.questionsCount') }}</div>
          <div class="stat-value">{{ stats.questionsCount }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">{{ t('distill.datasetsCount') }}</div>
          <div class="stat-value">{{ stats.datasetsCount }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">
            {{ t('distill.multiTurnDatasetsCount') }}
          </div>
          <div class="stat-value">{{ stats.multiTurnDatasetsCount }}</div>
        </div>
      </div>

      <div class="tree-wrapper" v-loading="loading">
        <DistillTreeView
          v-if="projectId"
          ref="treeRef"
          :project-id="projectId"
          :tags="tags"
          @generate-sub-tags="openTagDialog"
          @generate-questions="openQuestionDialog"
          @update:tags="(val) => (tags = val)"
        />
      </div>
    </el-card>

    <!-- 生成标签对话框 -->
    <TagGenerationDialog
      v-model="tagDialogOpen"
      v-if="projectId"
      :project-id="projectId"
      :parent-tag="selectedTag"
      :tag-path="selectedTagPath"
      :model="selectedModel"
      @generated="handleTagGenerated"
    />

    <!-- 生成问题对话框 -->
    <QuestionGenerationDialog
      v-model="questionDialogOpen"
      v-if="projectId && selectedTag"
      :project-id="projectId"
      :tag="selectedTag"
      :tag-path="selectedTagPath"
      :model="selectedModel"
      @generated="handleQuestionGenerated"
    />

    <!-- 全自动蒸馏配置（前台 / 后台） -->
    <AutoDistillDialog
      v-model="autoDistillDialogOpen"
      v-if="projectId"
      :project="project"
      :stats="stats"
      @start="handleStartAutoDistill"
      @start-background="handleStartAutoDistillBackground"
    />

    <!-- 全自动蒸馏进度 -->
    <AutoDistillProgress
      v-model="autoDistillProgressOpen"
      :progress="distillProgress"
      :running="autoDistillRunning"
      @close="handleCloseProgressDialog"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onBeforeUnmount } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import DistillTreeView from '@/components/distill/DistillTreeView.vue';
import TagGenerationDialog from '@/components/distill/TagGenerationDialog.vue';
import QuestionGenerationDialog from '@/components/distill/QuestionGenerationDialog.vue';
import AutoDistillDialog from '@/components/distill/AutoDistillDialog.vue';
import AutoDistillProgress from '@/components/distill/AutoDistillProgress.vue';
import { fetchAllDistillTags } from '@/api/distill';
import { createTask } from '@/api/task';
import { fetchAllDatasetIds } from '@/api/dataset';
import { fetchAllConversationIds } from '@/api/conversation';
import { useModelStore } from '@/stores/model';
import http from '@/api/http';
import { autoDistillService } from '@/services/autoDistillService';

const { t } = useI18n();
const route = useRoute();
const modelStore = useModelStore();

const projectId = computed(() => route.params.projectId);
const selectedModel = computed(() => modelStore.selectedModelInfo);

const loading = ref(false);
const error = ref('');
const project = ref(null);
const tags = ref([]);
const stats = ref({
  tagsCount: 0,
  questionsCount: 0,
  datasetsCount: 0,
  multiTurnDatasetsCount: 0,
});

const treeRef = ref(null);

const tagDialogOpen = ref(false);
const questionDialogOpen = ref(false);
const autoDistillDialogOpen = ref(false);
const creatingTask = ref(false);
const autoDistillProgressOpen = ref(false);
const autoDistillRunning = ref(false);

const selectedTag = ref(null);
const selectedTagPath = ref('');

const distillProgress = ref({
  stage: 'initializing',
  tagsTotal: 0,
  tagsBuilt: 0,
  questionsTotal: 0,
  questionsBuilt: 0,
  datasetsTotal: 0,
  datasetsBuilt: 0,
  multiTurnDatasetsTotal: 0,
  multiTurnDatasetsBuilt: 0,
  logs: [],
});

const fetchProject = async () => {
  if (!projectId.value) return;
  try {
    loading.value = true;
    const res = await http.get(`/projects/${projectId.value}/`);
    const data = res?.data && Object.keys(res.data || {}).length ? res.data : res;
    project.value = data;
  } catch (e) {
    console.error('获取项目信息失败:', e);
    error.value = t('common.fetchError') || '获取项目信息失败';
  } finally {
    loading.value = false;
  }
};

const loadTags = async () => {
  if (!projectId.value) return;
  try {
    loading.value = true;
    const res = await fetchAllDistillTags(projectId.value);
    const list = Array.isArray(res?.tags) ? res.tags : res || [];
    tags.value = list;
    stats.value.tagsCount = list.length;
  } catch (e) {
    console.error('获取蒸馏标签失败:', e);
    ElMessage.error(t('textSplit.fetchChunksFailed') || '获取标签失败');
  } finally {
    loading.value = false;
  }
};

const loadStats = async () => {
  if (!projectId.value) return;
  try {
    const questions = await http.get(`/projects/${projectId.value}/questions/tree/`, {
      params: { isDistill: 'yes' },
    });
    const questionList = Array.isArray(questions) ? questions : questions?.data || [];
    const questionsCount = questionList.length;
    const datasetsCount = questionList.filter((q) => q.answered).length;

    const datasetIds = await fetchAllDatasetIds(projectId.value);
    const datasetTotal = Array.isArray(datasetIds) ? datasetIds.length : datasetIds?.total || 0;

    let multiTurnTotal = 0;
    try {
      const convIds = await fetchAllConversationIds(projectId.value);
      multiTurnTotal = Array.isArray(convIds)
        ? convIds.length
        : Array.isArray(convIds?.allConversationIds)
        ? convIds.allConversationIds.length
        : 0;
    } catch (e) {
      console.log('获取多轮对话数据集统计失败:', e.message);
    }

    stats.value = {
      tagsCount: tags.value.length,
      questionsCount,
      datasetsCount: datasetTotal || datasetsCount,
      multiTurnDatasetsCount: multiTurnTotal,
    };
  } catch (e) {
    console.error('获取蒸馏统计信息失败:', e);
  }
};

onMounted(async () => {
  await fetchProject();
  await loadTags();
  await loadStats();

  if (typeof window !== 'undefined') {
    window.addEventListener('refreshDistillStats', loadStats);
  }
});

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('refreshDistillStats', loadStats);
  }
});

const openTagDialog = (tag = null, tagPath = '') => {
  if (!selectedModel.value) {
    ElMessage.error(t('distill.selectModelFirst'));
    return;
  }
  selectedTag.value = tag;
  selectedTagPath.value = tagPath;
  tagDialogOpen.value = true;
};

const openQuestionDialog = (tag, tagPath) => {
  if (!selectedModel.value) {
    ElMessage.error(t('distill.selectModelFirst'));
    return;
  }
  selectedTag.value = tag;
  selectedTagPath.value = tagPath;
  questionDialogOpen.value = true;
};

const handleTagGenerated = async () => {
  tagDialogOpen.value = false;
  await loadTags();
};

const handleQuestionGenerated = async () => {
  questionDialogOpen.value = false;
  await loadStats();
  if (treeRef.value && typeof treeRef.value.fetchQuestionsStats === 'function') {
    treeRef.value.fetchQuestionsStats();
  }
};

const openAutoDistillDialog = () => {
  if (!selectedModel.value) {
    ElMessage.error(t('distill.selectModelFirst'));
    return;
  }
  autoDistillDialogOpen.value = true;
};

const initProgress = (config) => {
  distillProgress.value = {
    stage: 'initializing',
    tagsTotal: config.estimatedTags || 0,
    tagsBuilt: stats.value.tagsCount || 0,
    questionsTotal: config.estimatedQuestions || 0,
    questionsBuilt: stats.value.questionsCount || 0,
    datasetsTotal: config.estimatedQuestions || 0,
    datasetsBuilt: stats.value.datasetsCount || 0,
    multiTurnDatasetsTotal:
      config.datasetType === 'multi-turn' || config.datasetType === 'both'
        ? config.estimatedQuestions
        : 0,
    multiTurnDatasetsBuilt: stats.value.multiTurnDatasetsCount || 0,
    logs: [
      t('distill.autoDistillStarted', {
        time: new Date().toLocaleTimeString(),
      }),
    ],
  };
};

const updateProgress = (update) => {
  distillProgress.value = (() => {
    const prev = distillProgress.value;
    const next = { ...prev };

    if (update.stage) next.stage = update.stage;
    if (update.tagsTotal) next.tagsTotal = update.tagsTotal;
    if (update.questionsTotal) next.questionsTotal = update.questionsTotal;
    if (update.datasetsTotal) next.datasetsTotal = update.datasetsTotal;
    if (update.multiTurnDatasetsTotal) next.multiTurnDatasetsTotal = update.multiTurnDatasetsTotal;

    const inc = update.updateType === 'increment';

    if (update.tagsBuilt) {
      next.tagsBuilt = inc ? (next.tagsBuilt || 0) + update.tagsBuilt : update.tagsBuilt;
    }
    if (update.questionsBuilt) {
      next.questionsBuilt = inc
        ? (next.questionsBuilt || 0) + update.questionsBuilt
        : update.questionsBuilt;
    }
    if (update.datasetsBuilt) {
      next.datasetsBuilt = inc
        ? (next.datasetsBuilt || 0) + update.datasetsBuilt
        : update.datasetsBuilt;
    }
    if (update.multiTurnDatasetsBuilt) {
      next.multiTurnDatasetsBuilt = inc
        ? (next.multiTurnDatasetsBuilt || 0) + update.multiTurnDatasetsBuilt
        : update.multiTurnDatasetsBuilt;
    }

    return next;
  })();
};

const addLog = (message) => {
  const logs = [...(distillProgress.value.logs || []), message];
  distillProgress.value.logs = logs.length > 200 ? logs.slice(-200) : logs;
};

const handleStartAutoDistill = async (config) => {
  if (!projectId.value || !selectedModel.value) return;
  autoDistillDialogOpen.value = false;
  autoDistillProgressOpen.value = true;
  autoDistillRunning.value = true;

  initProgress(config);

  try {
    if (!selectedModel.value) {
      addLog(t('distill.selectModelFirst'));
      autoDistillRunning.value = false;
      return;
    }

    await autoDistillService.executeDistillTask({
      projectId: projectId.value,
      topic: config.topic,
      levels: config.levels,
      tagsPerLevel: config.tagsPerLevel,
      questionsPerTag: config.questionsPerTag,
      datasetType: config.datasetType,
      model: selectedModel.value,
      language: 'zh-CN',
      concurrencyLimit: project.value?.taskConfig?.concurrencyLimit || 5,
      onProgress: updateProgress,
      onLog: addLog,
    });

    autoDistillRunning.value = false;
  } catch (e) {
    console.error('自动蒸馏任务执行失败:', e);
    addLog(
      t('distill.taskExecutionError', {
        error: e?.message || t('common.unknownError'),
      }),
    );
    autoDistillRunning.value = false;
  }
};

const handleStartAutoDistillBackground = async (config) => {
  if (!projectId.value || !selectedModel.value) return;

  autoDistillDialogOpen.value = false;
  try {
    creatingTask.value = true;
    await createTask(projectId.value, {
      taskType: 'data-distillation',
      modelInfo: selectedModel.value,
      language: 'zh-CN',
      detail: t('distill.autoDistillTaskDetail', { topic: config.topic }),
      totalCount: config.estimatedQuestions,
      note: {
        topic: config.topic,
        levels: config.levels,
        tagsPerLevel: config.tagsPerLevel,
        questionsPerTag: config.questionsPerTag,
        datasetType: config.datasetType,
        estimatedTags: config.estimatedTags,
        estimatedQuestions: config.estimatedQuestions,
      },
    });
    ElMessage.success(t('tasks.createSuccess') || '后台任务已创建');
  } catch (e) {
    console.error('创建蒸馏任务失败:', e);
    ElMessage.error(t('tasks.createFailed') || '创建任务失败');
  } finally {
    creatingTask.value = false;
  }
};

const handleCloseProgressDialog = async () => {
  if (autoDistillRunning.value) {
    autoDistillProgressOpen.value = false;
    return;
  }
  autoDistillProgressOpen.value = false;
  await loadTags();
  await loadStats();
  if (treeRef.value && typeof treeRef.value.fetchQuestionsStats === 'function') {
    treeRef.value.fetchQuestionsStats();
  }
};
</script>

<style scoped>
.distill-view {
  padding: 16px;
  max-width: 1400px;
  margin: auto;
}

.distill-card :deep(.el-card__body) {
  padding: 16px 20px 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-area {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-text {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.title-sub {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stats-row {
  display: flex;
  gap: 24px; /* 统一并适当增大四个统计卡片之间的间距 */
  margin: 16px 0 20px;
}

.stat-item {
  flex: 1;
  padding: 8px 12px;
  border-radius: 6px;
  background: var(--el-bg-color-page);
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
}

.tree-wrapper {
  margin-top: 8px;
}

.mb-16 {
  margin-bottom: 16px;
}

.dialog-body {
  padding: 4px 0;
}

.field-block {
  margin-bottom: 16px;
}

.field-label {
  font-size: 14px;
  margin-bottom: 4px;
  color: var(--el-text-color-regular);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>