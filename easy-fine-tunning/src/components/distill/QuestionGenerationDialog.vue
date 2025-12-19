<template>
  <el-dialog
    :model-value="open"
    :title="dialogTitle"
    width="520px"
    @close="handleClose"
  >
    <div class="dialog-body">
      <el-alert
        v-if="error"
        type="error"
        :closable="false"
        class="mb-16"
      >
        {{ error }}
      </el-alert>

      <div class="field-block">
        <div class="field-label">{{ t('distill.tagPath') }}:</div>
        <el-card shadow="never" class="path-card">
          {{ tagPath || tagLabel }}
        </el-card>
      </div>

      <div class="field-block">
        <div class="field-label">{{ t('distill.questionCount') }}:</div>
        <el-input-number
          v-model="count"
          :min="1"
          :max="100"
          :disabled="loading"
        />
        <div class="field-help">
          {{ t('distill.questionCountHelp') }}
        </div>
      </div>

      <div v-if="generatedQuestions.length > 0" class="field-block">
        <div class="field-label">{{ t('distill.generatedQuestions') }}:</div>
        <el-card shadow="never" class="questions-card">
          <div
            v-for="q in generatedQuestions"
            :key="q.id || q.question"
            class="question-item"
          >
            {{ q.question }}
          </div>
        </el-card>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">
          {{ t('common.cancel') }}
        </el-button>
        <el-button
          v-if="generatedQuestions.length === 0"
          type="primary"
          :loading="loading"
          @click="handleGenerateQuestions"
        >
          {{ loading ? t('common.generating') : t('distill.generateQuestions') }}
        </el-button>
        <el-button
          v-else
          type="primary"
          @click="handleGenerateComplete"
        >
          {{ t('common.complete') }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import http from '@/api/http';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  projectId: {
    type: String,
    required: true,
  },
  tag: {
    type: Object,
    required: true,
  },
  tagPath: {
    type: String,
    default: '',
  },
  model: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(['update:modelValue', 'generated']);

const { t } = useI18n();

const open = ref(props.modelValue);
const loading = ref(false);
const error = ref('');
const count = ref(5);
const generatedQuestions = ref([]);

const tagLabel = computed(() => props.tag?.label || t('distill.unknownTag'));

const dialogTitle = computed(() =>
  t('distill.generateQuestionsTitle', { tag: tagLabel.value }),
);

watch(
  () => props.modelValue,
  (val) => {
    open.value = val;
  },
);

const handleGenerateQuestions = async () => {
  try {
    loading.value = true;
    error.value = '';

    const payload = {
      tagPath: props.tagPath,
      currentTag: props.tag.label,
      tagId: props.tag.id,
      count: count.value,
      model: props.model,
    };

    const res = await http.post(
      `/projects/${props.projectId}/distill/questions/`,
      payload,
    );

    const list = Array.isArray(res)
      ? res
      : Array.isArray(res?.data)
      ? res.data
      : [];

    if (!Array.isArray(list)) {
      throw new Error('生成结果格式异常');
    }

    generatedQuestions.value = list;
    emit('generated', list);
  } catch (e) {
    console.error('生成问题失败:', e);
    error.value =
      e?.message || t('distill.generateQuestionsError') || '生成问题失败';
    ElMessage.error(error.value);
  } finally {
    loading.value = false;
  }
};

const handleGenerateComplete = () => {
  emit('generated', generatedQuestions.value);
  handleClose();
};

const handleClose = () => {
  open.value = false;
  emit('update:modelValue', false);
  loading.value = false;
  error.value = '';
  count.value = 5;
  generatedQuestions.value = [];
};
</script>

<style scoped>
.dialog-body {
  padding: 4px 0;
}

.mb-16 {
  margin-bottom: 16px;
}

.field-block {
  margin-bottom: 16px;
}

.field-label {
  font-size: 14px;
  margin-bottom: 4px;
  color: var(--el-text-color-regular);
}

.field-help {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.path-card {
  padding: 8px 12px;
  font-size: 13px;
}

.questions-card {
  padding: 8px 12px;
  max-height: 260px;
  overflow-y: auto;
}

.question-item {
  font-size: 13px;
  line-height: 1.6;
  padding: 4px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.question-item:last-child {
  border-bottom: none;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>


