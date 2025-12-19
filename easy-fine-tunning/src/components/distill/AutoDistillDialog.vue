<template>
  <el-dialog
    :model-value="modelValue"
    :title="t('distill.autoDistillTitle')"
    width="720px"
    @close="handleClose"
  >
    <div class="dialog-body">
      <div class="left-panel">
        <el-form label-position="top" class="form">
          <el-form-item :label="t('distill.distillTopic')">
            <el-input
              v-model="topic"
              :placeholder="
                t('distill.distillTopicPlaceholder', { defaultValue: t('distill.distillTopic') })
              "
            />
            <div class="field-help">
              {{ t('distill.rootTopicHelperText') }}
            </div>
          </el-form-item>

          <el-form-item :label="t('distill.tagLevels')">
            <el-input-number
              v-model="levels"
              :min="1"
              :max="5"
            />
            <div class="field-help">
              {{ t('distill.tagLevelsHelper', { max: 5 }) }}
            </div>
          </el-form-item>

          <el-form-item :label="t('distill.tagsPerLevel')">
            <el-input-number
              v-model="tagsPerLevel"
              :min="1"
              :max="50"
            />
            <div class="field-help">
              {{ t('distill.tagsPerLevelHelper', { max: 50 }) }}
            </div>
          </el-form-item>

          <el-form-item :label="t('distill.questionsPerTag')">
            <el-input-number
              v-model="questionsPerTag"
              :min="1"
              :max="50"
            />
            <div class="field-help">
              {{ t('distill.questionsPerTagHelper', { max: 50 }) }}
            </div>
          </el-form-item>

          <el-form-item :label="t('distill.datasetType', { defaultValue: '数据集类型' })">
            <el-radio-group v-model="datasetType">
              <el-radio label="single-turn">
                {{ t('distill.singleTurnDataset', { defaultValue: '单轮对话数据集' }) }}
              </el-radio>
              <el-radio label="multi-turn">
                {{ t('distill.multiTurnDataset', { defaultValue: '多轮对话数据集' }) }}
              </el-radio>
              <el-radio label="both">
                {{ t('distill.bothDatasetTypes', { defaultValue: '两种数据集都生成' }) }}
              </el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </div>

      <div class="right-panel">
        <el-card shadow="never" class="stats-card">
          <div class="stats-card-header">
            <div class="stats-title">
              {{ t('distill.estimationInfo') }}
            </div>
          </div>

          <div class="stats-section">
            <div class="stats-row">
              <div class="stats-label">{{ t('distill.estimatedTags') }}:</div>
              <div class="stats-value">{{ estimatedTags }}</div>
            </div>
            <div class="stats-row">
              <div class="stats-label">{{ t('distill.estimatedQuestions') }}:</div>
              <div class="stats-value">{{ estimatedQuestions }}</div>
            </div>

            <el-divider />

            <div class="stats-row">
              <div class="stats-label">{{ t('distill.currentTags') }}:</div>
              <div class="stats-value">{{ stats?.tagsCount || 0 }}</div>
            </div>
            <div class="stats-row">
              <div class="stats-label">{{ t('distill.currentQuestions') }}:</div>
              <div class="stats-value">{{ stats?.questionsCount || 0 }}</div>
            </div>
          </div>

          <div class="stats-footer">
            <div class="stats-row emphasize">
              <div class="stats-label">{{ t('distill.newTags') }}:</div>
              <div class="stats-value emphasize">{{ newTags }}</div>
            </div>
            <div class="stats-row emphasize">
              <div class="stats-label">{{ t('distill.newQuestions') }}:</div>
              <div class="stats-value emphasize">{{ newQuestions }}</div>
            </div>
          </div>
        </el-card>

        <el-alert
          v-if="error"
          type="error"
          :closable="false"
          class="mt-12"
        >
          {{ error }}
        </el-alert>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">
          {{ t('common.cancel') }}
        </el-button>
        <el-button
          type="primary"
          plain
          :disabled="!canSubmit"
          @click="handleStartBackground"
        >
          {{ t('distill.startAutoDistillBackground', { defaultValue: '开始自动蒸馏（后台运行）' }) }}
        </el-button>
        <el-button
          type="primary"
          :disabled="!canSubmit"
          @click="handleStart"
        >
          {{ t('distill.startAutoDistill') }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  project: {
    type: Object,
    default: null,
  },
  stats: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(['update:modelValue', 'start', 'start-background']);

const { t } = useI18n();

const topic = ref('');
const levels = ref(2);
const tagsPerLevel = ref(10);
const questionsPerTag = ref(10);
const datasetType = ref('single-turn');
const error = ref('');

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      initTopic();
      recompute();
    }
  },
);

const initTopic = () => {
  if (props.project) {
    const defaultTopic =
      props.project.name && props.project.name.trim()
        ? props.project.name
        : t('distill.unnamedProject', { defaultValue: '未命名项目' });
    topic.value = defaultTopic;
  }
};

const estimatedTags = ref(0);
const estimatedQuestions = ref(0);
const newTags = ref(0);
const newQuestions = ref(0);

const recompute = () => {
  const leafTagsCount = Math.pow(tagsPerLevel.value, levels.value);
  const totalQuestions = leafTagsCount * questionsPerTag.value;

  let totalTags;
  if (tagsPerLevel.value === 1) {
    totalTags = levels.value + 1;
  } else {
    totalTags = (1 - Math.pow(tagsPerLevel.value, levels.value + 1)) / (1 - tagsPerLevel.value);
  }

  estimatedTags.value = leafTagsCount;
  estimatedQuestions.value = totalQuestions;

  const currentTags = props.stats?.tagsCount || 0;
  const currentQuestions = props.stats?.questionsCount || 0;

  newTags.value = Math.max(0, leafTagsCount - currentTags);
  newQuestions.value = Math.max(0, totalQuestions - currentQuestions);

  if (leafTagsCount <= currentTags && totalQuestions <= currentQuestions) {
    error.value = t('distill.autoDistillInsufficientError');
  } else {
    error.value = '';
  }
};

watch([levels, tagsPerLevel, questionsPerTag, () => props.stats], () => {
  recompute();
});

const canSubmit = computed(() => {
  const trimmed = (topic.value || '').trim();
  return !!trimmed && !error.value;
});

const handleClose = () => {
  emit('update:modelValue', false);
};

const buildPayload = () => {
  const trimmedTopic = (topic.value || '').trim();
  return {
    topic: trimmedTopic,
    levels: levels.value,
    tagsPerLevel: tagsPerLevel.value,
    questionsPerTag: questionsPerTag.value,
    estimatedTags: estimatedTags.value,
    estimatedQuestions: estimatedQuestions.value,
    datasetType: datasetType.value,
  };
};

const handleStart = () => {
  if (!canSubmit.value) return;
  emit('start', buildPayload());
};

const handleStartBackground = () => {
  if (!canSubmit.value) return;
  emit('start-background', buildPayload());
};
</script>

<style scoped>
.dialog-body {
  display: flex;
  gap: 16px;
}

.left-panel {
  flex: 1;
  min-width: 0;
}

.right-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.form {
  padding-right: 8px;
}

.field-help {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.stats-card {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.stats-card-header {
  margin-bottom: 8px;
}

.stats-title {
  font-size: 16px;
  font-weight: 600;
}

.stats-section {
  flex: 1;
}

.stats-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.stats-label {
  color: var(--el-text-color-secondary);
}

.stats-value {
  font-weight: 500;
}

.stats-footer {
  border-top: 1px dashed var(--el-border-color-light);
  padding-top: 8px;
  margin-top: 8px;
}

.stats-row.emphasize .stats-label {
  color: var(--el-color-primary);
}

.stats-row.emphasize .stats-value {
  color: var(--el-color-primary);
  font-size: 18px;
  font-weight: 600;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.mt-12 {
  margin-top: 12px;
}
</style>


