<template>
  <!-- 文字类型输入 -->
  <div v-if="answerType === 'text'" class="answer-input">
    <div class="header-row">
      <h3 class="title">{{ $t('images.answer', '文本答案') }} *</h3>
      <AIGenerateButton
        :project-id="projectId"
        :dataset-id="datasetId"
        :image-name="imageName"
        :question="question"
        @success="handleAnswerChange"
      />
    </div>
    <el-input
      v-model="localAnswer"
      type="textarea"
      :rows="6"
      :placeholder="$t('images.answerPlaceholder', '请输入答案...')"
      @input="handleAnswerChange"
    />
  </div>

  <!-- 标签类型输入 -->
  <div v-else-if="answerType === 'label'" class="answer-input">
    <div class="header-row">
      <h3 class="title">{{ $t('images.selectLabels', '标签选择') }} *</h3>
      <AIGenerateButton
        :project-id="projectId"
        :dataset-id="datasetId"
        :image-name="imageName"
        :question="question"
        :answer-type="answerType"
        @success="handleAnswerChange"
      />
    </div>

    <!-- 可选标签 -->
    <el-card class="labels-card">
      <div class="labels-title">{{ $t('images.availableLabels', '可选标签') }}</div>
      <div class="labels-container">
        <el-tag
          v-for="label in labelOptions"
          :key="label"
          :type="selectedLabels.includes(label) ? 'primary' : 'info'"
          :effect="selectedLabels.includes(label) ? 'dark' : 'plain'"
          class="label-chip"
          @click="handleToggleLabel(label)"
        >
          {{ label }}
        </el-tag>
        <div v-if="labelOptions.length === 0" class="no-labels">
          {{ $t('images.noLabelsAvailable', '暂无可选标签') }}
        </div>
      </div>
    </el-card>
  </div>

  <!-- 自定义格式输入 -->
  <div v-else-if="answerType === 'custom_format'" class="answer-input">
    <div class="header-row">
      <h3 class="title">{{ $t('images.customFormatAnswer', '自定义格式答案') }} *</h3>
      <div class="header-actions">
        <AIGenerateButton
          :project-id="projectId"
          :dataset-id="datasetId"
          :image-name="imageName"
          :question="question"
          @success="handleAnswerChange"
        />
        <el-button
          v-if="customFormat"
          size="small"
          @click="handleUseTemplate"
        >
          {{ $t('images.useTemplate', '使用模板') }}
        </el-button>
      </div>
    </div>

    <!-- 显示格式要求 -->
    <el-card v-if="customFormat" class="format-card">
      <div class="format-title">{{ $t('images.formatRequirement', '格式要求') }}</div>
      <pre class="format-preview">{{ formatPreview }}</pre>
    </el-card>

    <!-- JSON 输入框 -->
    <el-input
      v-model="localAnswer"
      type="textarea"
      :rows="10"
      :placeholder="$t('images.customFormatPlaceholder', '请输入符合格式的 JSON...')"
      :class="{ 'is-error': jsonError }"
      @input="handleJsonChange"
    />
    <div v-if="jsonError" class="error-text">{{ jsonError }}</div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import AIGenerateButton from './AIGenerateButton.vue';

const props = defineProps({
  answerType: {
    type: String,
    default: 'text'
  },
  answer: {
    type: [String, Array],
    default: ''
  },
  labels: {
    type: [String, Array],
    default: () => []
  },
  customFormat: {
    type: [String, Object],
    default: null
  },
  projectId: {
    type: [String, Number],
    default: null
  },
  datasetId: {
    type: [String, Number],
    default: null
  },
  imageName: {
    type: String,
    default: ''
  },
  question: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['answer-change']);

const { t, locale } = useI18n();

const localAnswer = ref(props.answer || '');
const jsonError = ref('');

// 监听 props.answer 变化
watch(
  () => props.answer,
  (val) => {
    if (props.answerType === 'label') {
      localAnswer.value = Array.isArray(val) ? val : [];
    } else {
      localAnswer.value = val || '';
    }
  },
  { immediate: true }
);

// 标签选项
const labelOptions = computed(() => {
  let options = [];
  if (typeof props.labels === 'string' && props.labels) {
    try {
      options = JSON.parse(props.labels);
    } catch (e) {
      options = [];
    }
  } else if (Array.isArray(props.labels)) {
    options = props.labels;
  }

  // 添加"其他"选项
  const otherLabel = locale.value === 'en' ? 'other' : '其他';
  if (!options.includes('其他') && !options.includes('other')) {
    options.push(otherLabel);
  }

  return options;
});

// 已选择的标签
const selectedLabels = computed(() => {
  if (props.answerType === 'label') {
    return Array.isArray(localAnswer.value) ? localAnswer.value : [];
  }
  return [];
});

// 格式预览
const formatPreview = computed(() => {
  if (!props.customFormat) return '';
  if (typeof props.customFormat === 'string') {
    return props.customFormat;
  }
  return JSON.stringify(props.customFormat, null, 2);
});

// 处理答案变化
const handleAnswerChange = (newAnswer) => {
  if (props.answerType === 'label') {
    localAnswer.value = Array.isArray(newAnswer) ? newAnswer : [];
  } else {
    localAnswer.value = newAnswer || '';
  }
  emit('answer-change', localAnswer.value);
};

// 切换标签
const handleToggleLabel = (label) => {
  const current = [...selectedLabels.value];
  if (current.includes(label)) {
    const filtered = current.filter((l) => l !== label);
    handleAnswerChange(filtered);
  } else {
    handleAnswerChange([...current, label]);
  }
};

// JSON 变化处理
const handleJsonChange = (value) => {
  localAnswer.value = value;
  jsonError.value = '';

  if (value.trim()) {
    try {
      JSON.parse(value);
    } catch (e) {
      jsonError.value = t('images.invalidJsonFormat', 'JSON 格式不正确');
    }
  }

  emit('answer-change', localAnswer.value);
};

// 使用模板
const handleUseTemplate = () => {
  if (props.customFormat) {
    try {
      let templateJson;
      if (typeof props.customFormat === 'string') {
        templateJson = JSON.parse(props.customFormat);
      } else {
        templateJson = props.customFormat;
      }
      const formatted = JSON.stringify(templateJson, null, 2);
      handleAnswerChange(formatted);
      jsonError.value = '';
    } catch (e) {
      handleAnswerChange('{}');
    }
  }
};
</script>

<style scoped>
.answer-input {
  width: 100%;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.labels-card {
  margin-bottom: 16px;
  background-color: var(--el-fill-color-lighter);
}

.labels-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.labels-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.label-chip {
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  height: 32px;
  padding: 0 12px;
}

.label-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.no-labels {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  font-style: italic;
}

.format-card {
  margin-bottom: 16px;
  background-color: var(--el-fill-color-lighter);
}

.format-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.format-preview {
  margin: 0;
  padding: 12px;
  background-color: var(--el-bg-color);
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: var(--el-text-color-primary);
  overflow: auto;
  max-height: 150px;
  border: 1px solid var(--el-border-color);
}

.is-error :deep(.el-textarea__inner) {
  border-color: var(--el-color-error);
}

.error-text {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-color-error);
}
</style>

