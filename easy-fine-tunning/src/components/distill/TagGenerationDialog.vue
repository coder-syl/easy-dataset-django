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

      <div v-if="parentTag && tagPath" class="field-block">
        <div class="field-label">{{ t('distill.tagPath') }}:</div>
        <el-card shadow="never" class="path-card">
          {{ tagPath || parentTag.label }}
        </el-card>
      </div>

      <div class="field-block">
        <div class="field-label">{{ t('distill.parentTag') }}:</div>
        <el-input
          v-model="parentTagName"
          :disabled="!parentTag || loading"
          :placeholder="t('distill.parentTagPlaceholder')"
        />
        <div class="field-help">
          {{
            !parentTag
              ? t('distill.rootTopicHelperText') || '使用项目名称作为顶级主题'
              : t('distill.parentTagHelp')
          }}
        </div>
      </div>

      <div class="field-block">
        <div class="field-label">{{ t('distill.tagCount') }}:</div>
        <el-input-number
          v-model="count"
          :min="1"
          :max="100"
          :disabled="loading"
        />
        <div class="field-help">
          {{ t('distill.tagCountHelp') }}
        </div>
      </div>

      <div v-if="generatedTags.length > 0" class="field-block">
        <div class="field-label">{{ t('distill.generatedTags') }}:</div>
        <div class="tags-wrapper">
          <el-tag
            v-for="tag in generatedTags"
            :key="tag.id || tag.label"
            type="info"
            effect="plain"
            class="tag-item"
          >
            {{ tag.label }}
          </el-tag>
        </div>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">
          {{ t('common.cancel') }}
        </el-button>
        <el-button
          v-if="generatedTags.length === 0"
          type="primary"
          :loading="loading"
          :disabled="!parentTagName"
          @click="handleGenerateTags"
        >
          {{ loading ? t('common.generating') : t('distill.generateTags') }}
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
import { ref, watch, onMounted, computed } from 'vue';
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
  parentTag: {
    type: Object,
    default: null,
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
const generatedTags = ref([]);
const parentTagName = ref('');

const dialogTitle = computed(() =>
  props.parentTag
    ? t('distill.generateSubTagsTitle', { parentTag: props.parentTag.label })
    : t('distill.generateRootTagsTitle'),
);

watch(
  () => props.modelValue,
  (val) => {
    open.value = val;
    if (val) {
      initParentTagName();
    }
  },
);

const initParentTagName = async () => {
  if (props.parentTag) {
    parentTagName.value = props.parentTag.label || '';
    return;
  }

  // 顶级标签：使用项目名称
  try {
    const project = await http.get(`/projects/${props.projectId}/`);
    parentTagName.value = project?.name || '';
  } catch (e) {
    parentTagName.value = '';
  }
};

onMounted(() => {
  if (open.value) {
    initParentTagName();
  }
});

const handleGenerateTags = async () => {
  try {
    loading.value = true;
    error.value = '';

    const payload = {
      parentTag: parentTagName.value,
      parentTagId: props.parentTag ? props.parentTag.id : null,
      tagPath: props.tagPath || parentTagName.value,
      count: count.value,
      model: props.model,
    };

    const res = await http.post(
      `/projects/${props.projectId}/distill/tags/`,
      payload,
    );

    const list = Array.isArray(res?.data) ? res.data : res?.tags || res || [];
    generatedTags.value = list;
  } catch (e) {
    console.error('生成标签失败:', e);
    error.value =
      e?.message || t('distill.generateTagsError') || '生成标签失败';
    ElMessage.error(error.value);
  } finally {
    loading.value = false;
  }
};

const handleGenerateComplete = () => {
  emit('generated', generatedTags.value);
  handleClose();
};

const handleClose = () => {
  open.value = false;
  emit('update:modelValue', false);
  loading.value = false;
  error.value = '';
  count.value = 5;
  generatedTags.value = [];
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

.tags-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  margin-bottom: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>


