<template>
  <el-dialog
    :model-value="modelValue"
    :title="template ? t('questions.template.edit') : t('questions.template.create')"
    width="720px"
    @update:model-value="$emit('update:modelValue', $event)"
    @close="$emit('close')"
  >
    <el-form :model="formData" label-width="120px">
      <!-- 数据源类型 -->
      <el-form-item :label="t('questions.template.sourceTypeInfo')">
        <el-select v-model="formData.source_type" style="width: 100%">
          <el-option :label="t('questions.template.sourceType.text')" value="text" />
          <el-option :label="t('questions.template.sourceType.image')" value="image" />
        </el-select>
      </el-form-item>

      <!-- 问题内容 -->
      <el-form-item :label="t('questions.template.question')" required :error="errors.question">
        <el-input v-model="formData.question" />
      </el-form-item>

      <!-- 答案类型 -->
      <el-form-item :label="t('questions.template.answerType.label')">
        <el-select v-model="formData.answer_type" style="width: 100%">
          <el-option :label="t('questions.template.answerType.text')" value="text" />
          <el-option :label="t('questions.template.answerType.tags')" value="label" />
          <el-option :label="t('questions.template.answerType.customFormat')" value="custom_format" />
        </el-select>
      </el-form-item>

      <!-- 描述 -->
      <el-form-item :label="t('questions.template.description')">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="2"
          :placeholder="t('questions.template.descriptionHelp')"
        />
      </el-form-item>

      <!-- 标签（答案类型为 label 时显示） -->
      <el-form-item v-if="formData.answer_type === 'label'" :label="t('questions.template.addLabel')" :error="errors.labels">
        <div class="label-input-wrapper">
          <el-input
            v-model="labelInput"
            @keyup.enter.prevent="handleAddLabel"
          />
          <el-button class="label-add-btn" @click="handleAddLabel">
            {{ t('common.add') }}
          </el-button>
        </div>
        <div class="label-chips">
          <el-tag
            v-for="label in formData.labels"
            :key="label"
            closable
            type="primary"
            effect="plain"
            @close="handleDeleteLabel(label)"
          >
            {{ label }}
          </el-tag>
        </div>
      </el-form-item>

      <!-- 自定义格式（答案类型为 custom_format 时显示） -->
      <el-form-item
        v-if="formData.answer_type === 'custom_format'"
        :label="t('questions.template.customFormat')"
        :error="errors.custom_format"
      >
        <el-input
          v-model="formData.custom_format"
          type="textarea"
          :rows="6"
          :placeholder="t('questions.template.customFormatHelp')"
        />
        <div class="field-help">
          {{ t('questions.template.customFormatInfo') }}
        </div>
      </el-form-item>

      <!-- 自动生成开关 -->
      <el-form-item>
        <el-checkbox v-model="formData.auto_generate">
          {{ autoGenerateHelpText }}
        </el-checkbox>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('close')">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="handleSubmit">
        {{ t('common.confirm') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  template: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['update:modelValue', 'submit', 'close']);

const { t } = useI18n();

const formData = ref({
  question: '',
  source_type: 'text',
  answer_type: 'text',
  description: '',
  labels: [],
  custom_format: '',
  auto_generate: true
});

const labelInput = ref('');
const errors = ref({});

const autoGenerateHelpText = computed(() => {
  if (formData.value.source_type === 'image') {
    return t('questions.template.autoGenerateHelpImage');
  }
  return t('questions.template.autoGenerateHelpText');
});

watch(
  () => props.template,
  (template) => {
    if (template) {
      formData.value = {
        question: template.question || '',
        source_type: template.source_type || 'text',
        answer_type: template.answer_type || 'text',
        description: template.description || '',
        labels: template.labels || [],
        custom_format: template.custom_format ? JSON.stringify(template.custom_format, null, 2) : '',
        auto_generate: true
      };
    } else {
      formData.value = {
        question: '',
        source_type: 'text',
        answer_type: 'text',
        description: '',
        labels: [],
        custom_format: '',
        auto_generate: true
      };
    }
    errors.value = {};
  },
  { immediate: true }
);

const handleAddLabel = () => {
  const trimmed = labelInput.value.trim();
  if (trimmed && !formData.value.labels.includes(trimmed)) {
    formData.value.labels.push(trimmed);
  }
  labelInput.value = '';
  if (errors.value.labels) {
    errors.value.labels = null;
  }
};

const handleDeleteLabel = (label) => {
  formData.value.labels = formData.value.labels.filter((l) => l !== label);
};

const validate = () => {
  const newErrors = {};

  if (!formData.value.question.trim()) {
    newErrors.question = t('questions.template.errors.questionRequired');
  }

  if (formData.value.answer_type === 'label' && formData.value.labels.length === 0) {
    newErrors.labels = t('questions.template.errors.labelsRequired');
  }

  if (formData.value.answer_type === 'custom_format') {
    if (!formData.value.custom_format.trim()) {
      newErrors.custom_format = t('questions.template.errors.customFormatRequired');
    } else {
      try {
        JSON.parse(formData.value.custom_format);
      } catch (e) {
        newErrors.custom_format = t('questions.template.errors.invalidJson');
      }
    }
  }

  errors.value = newErrors;
  return Object.keys(newErrors).length === 0;
};

const handleSubmit = () => {
  if (!validate()) return;

  const submitData = {
    question: formData.value.question.trim(),
    source_type: formData.value.source_type,
    answer_type: formData.value.answer_type,
    description: formData.value.description.trim(),
    auto_generate: formData.value.auto_generate,
    template_id: props.template?.id
  };

  if (formData.value.answer_type === 'label') {
    submitData.labels = [...formData.value.labels];
  }

  if (formData.value.answer_type === 'custom_format') {
    try {
      submitData.custom_format = JSON.parse(formData.value.custom_format);
    } catch (e) {
      return;
    }
  }

  emit('submit', submitData);
};
</script>

<style scoped>
.label-input-wrapper {
  display: flex;
  gap: 8px;
  width: 100%;
  margin-bottom: 4px;
}

.label-add-btn {
  min-width: 90px;
}

.label-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.field-help {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>

