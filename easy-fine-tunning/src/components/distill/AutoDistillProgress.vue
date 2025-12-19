<template>
  <el-dialog
    :model-value="modelValue"
    :title="t('distill.autoDistillProgress')"
    width="720px"
    :close-on-click-modal="false"
    :show-close="canClose"
    @close="handleClose"
  >
    <div class="dialog-body">
      <div class="section">
        <div class="section-title">
          {{ t('distill.overallProgress') }}
        </div>
        <div class="overall-progress">
          <el-progress
            :percentage="overallProgress"
            :stroke-width="10"
            :show-text="false"
          />
          <div class="overall-percent">
            {{ overallProgress }}%
          </div>
        </div>

        <div class="summary-grid">
          <el-card shadow="never" class="summary-card">
            <div class="summary-label">{{ t('distill.tagsProgress') }}</div>
            <div class="summary-value">
              {{ progress.tagsBuilt || 0 }} / {{ progress.tagsTotal || 0 }}
            </div>
          </el-card>

          <el-card shadow="never" class="summary-card">
            <div class="summary-label">{{ t('distill.questionsProgress') }}</div>
            <div class="summary-value">
              {{ progress.questionsBuilt || 0 }} / {{ progress.questionsTotal || 0 }}
            </div>
          </el-card>

          <el-card shadow="never" class="summary-card">
            <div class="summary-label">{{ t('distill.datasetsProgress') }}</div>
            <div class="summary-value">
              {{ progress.datasetsBuilt || 0 }} / {{ progress.datasetsTotal || 0 }}
            </div>
          </el-card>

          <el-card
            v-if="progress.multiTurnDatasetsTotal > 0"
            shadow="never"
            class="summary-card"
          >
            <div class="summary-label">
              {{ t('distill.multiTurnDatasetsProgress', { defaultValue: '多轮对话进度' }) }}
            </div>
            <div class="summary-value">
              {{ progress.multiTurnDatasetsBuilt || 0 }} / {{ progress.multiTurnDatasetsTotal || 0 }}
            </div>
          </el-card>
        </div>
      </div>

      <div class="section">
        <div class="section-title">
          {{ t('distill.currentStage') }}
        </div>
        <el-card shadow="never" class="stage-card">
          <div class="stage-text">
            {{ stageText }}
          </div>
        </el-card>
      </div>

      <div class="section">
        <div class="section-title">
          {{ t('distill.realTimeLogs') }}
        </div>
        <el-card shadow="never" class="logs-card">
          <div
            ref="logContainer"
            class="logs-container"
          >
            <template v-if="(progress.logs || []).length > 0">
              <div
                v-for="(log, idx) in progress.logs"
                :key="idx"
                :class="['log-line', logClass(log)]"
              >
                {{ log }}
              </div>
            </template>
            <template v-else>
              <div class="log-empty">
                {{ t('distill.waitingForLogs') }}
              </div>
            </template>
          </div>
        </el-card>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button
          v-if="canClose"
          type="primary"
          @click="handleClose"
        >
          {{ t('common.close') }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  progress: {
    type: Object,
    default: () => ({}),
  },
  running: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:modelValue', 'close']);

const { t } = useI18n();

const logContainer = ref(null);

const canClose = computed(() => !props.running && (!props.progress.stage || props.progress.stage === 'completed'));

const overallProgress = computed(() => {
  const { tagsBuilt, tagsTotal, questionsBuilt, questionsTotal, datasetsBuilt, datasetsTotal } =
    props.progress || {};
  const tagProgress = tagsTotal ? (tagsBuilt / tagsTotal) * 30 : 0;
  const questionProgress = questionsTotal ? (questionsBuilt / questionsTotal) * 35 : 0;
  const datasetProgress = datasetsTotal ? (datasetsBuilt / datasetsTotal) * 35 : 0;
  return Math.min(100, Math.round(tagProgress + questionProgress + datasetProgress));
});

const stageText = computed(() => {
  const stage = props.progress?.stage;
  switch (stage) {
    case 'level1':
      return t('distill.stageBuildingLevel1');
    case 'level2':
      return t('distill.stageBuildingLevel2');
    case 'level3':
      return t('distill.stageBuildingLevel3');
    case 'level4':
      return t('distill.stageBuildingLevel4');
    case 'level5':
      return t('distill.stageBuildingLevel5');
    case 'questions':
      return t('distill.stageBuildingQuestions');
    case 'datasets':
      return t('distill.stageBuildingDatasets');
    case 'multi-turn-datasets':
      return t('distill.stageBuildingMultiTurnDatasets', { defaultValue: '生成多轮对话数据集中...' });
    case 'completed':
      return t('distill.stageCompleted');
    default:
      return t('distill.stageInitializing');
  }
});

const handleClose = () => {
  if (!canClose.value) return;
  emit('update:modelValue', false);
  emit('close');
};

const scrollToBottom = () => {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight;
  }
};

onMounted(() => {
  scrollToBottom();
});

watch(
  () => props.progress?.logs,
  () => {
    scrollToBottom();
  },
);

const logClass = (log) => {
  const lower = String(log).toLowerCase();
  if (log.includes('成功') || log.includes('完成') || log.includes('Successfully')) {
    return 'log-success';
  }
  if (log.includes('失败') || lower.includes('error')) {
    return 'log-error';
  }
  return '';
};
</script>

<style scoped>
.dialog-body {
  padding: 4px 0;
}

.section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.overall-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.overall-percent {
  min-width: 40px;
  text-align: right;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 12px;
}

.summary-card {
  padding: 8px 10px;
}

.summary-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.summary-value {
  font-size: 16px;
  font-weight: 600;
}

.stage-card {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}

.stage-text {
  font-size: 14px;
  font-weight: 500;
}

.logs-card {
  padding: 0;
}

.logs-container {
  max-height: 260px;
  overflow-y: auto;
  padding: 8px 10px;
  background-color: #111827;
  color: #e5e7eb;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New',
    monospace;
  font-size: 12px;
}

.log-line {
  margin-bottom: 2px;
  white-space: pre-wrap;
}

.log-success {
  color: #4caf50;
}

.log-error {
  color: #f44336;
}

.log-empty {
  color: #6b7280;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}
</style>


