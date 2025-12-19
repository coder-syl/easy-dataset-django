<template>
  <div class="huggingface-tab">
    <el-alert v-if="error" :title="error" type="error" :closable="false" style="margin-bottom: 16px" />

    <el-alert
      v-if="success"
      :title="$t('export.uploadSuccess', '上传成功')"
      type="success"
      :closable="false"
      style="margin-bottom: 16px"
    >
      <template v-if="datasetUrl">
        <el-link :href="datasetUrl" target="_blank" type="primary">
          {{ $t('export.viewOnHuggingFace', '在 Hugging Face 上查看') }}
        </el-link>
      </template>
    </el-alert>

    <el-alert
      v-if="!hasToken"
      :title="$t('export.noTokenWarning', '未配置 HuggingFace Token')"
      type="warning"
      :closable="false"
      style="margin-bottom: 16px"
    >
      <el-button
        size="small"
        @click="$router.push(`/projects/${projectId}/settings`)"
      >
        {{ $t('export.goToSettings', '前往设置') }}
      </el-button>
    </el-alert>

    <el-divider />

    <div class="section">
      <div class="section-title">{{ $t('export.datasetSettings', '数据集设置') }}</div>
      <el-input
        v-model="datasetName"
        :placeholder="$t('export.datasetNamePlaceholder', 'username/dataset-name')"
        style="margin-bottom: 16px"
      />
      <div class="form-tip">{{ $t('export.datasetNameHelp', '格式：username/dataset-name') }}</div>
      <el-checkbox v-model="isPrivate">
        {{ $t('export.privateDataset', '私有数据集') }}
      </el-checkbox>
    </div>

    <div class="section">
      <div class="section-title">{{ $t('export.exportOptions', '导出选项') }}</div>
      <div class="sub-section">
        <div class="section-label">{{ $t('export.systemPrompt', '系统提示词') }}</div>
        <el-input
          :model-value="systemPrompt"
          type="textarea"
          :rows="3"
          @input="$emit('system-prompt-change', $event)"
        />
      </div>
      <div v-if="formatType === 'multilingualthinking'" class="sub-section">
        <div class="section-label">{{ $t('export.reasoningLanguage', '推理语言') }}</div>
        <el-input
          :model-value="reasoningLanguage"
          :placeholder="$t('export.reasoningLanguagePlaceholder', '例如：English')"
          @input="$emit('reasoning-language-change', $event)"
        />
      </div>
      <div class="options-checkboxes">
        <el-checkbox :model-value="confirmedOnly" @change="$emit('confirmed-only-change', $event)">
          {{ $t('export.onlyConfirmed', '仅导出已确认数据') }}
        </el-checkbox>
        <el-checkbox :model-value="includeCOT" @change="$emit('include-cot-change', $event)">
          {{ $t('export.includeCOT', '包含思维链') }}
        </el-checkbox>
      </div>
    </div>

    <div class="actions">
      <el-button
        type="primary"
        :loading="uploading"
        :disabled="!hasToken || !datasetName"
        @click="handleUpload"
      >
        {{ uploading ? $t('export.uploading', '上传中...') : $t('export.uploadToHuggingFace', '上传至 Hugging Face') }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import http from '@/api/http';

const props = defineProps({
  projectId: {
    type: String,
    required: true
  },
  systemPrompt: {
    type: String,
    default: ''
  },
  reasoningLanguage: {
    type: String,
    default: 'English'
  },
  confirmedOnly: {
    type: Boolean,
    default: false
  },
  includeCOT: {
    type: Boolean,
    default: true
  },
  formatType: {
    type: String,
    default: 'alpaca'
  },
  fileFormat: {
    type: String,
    default: 'json'
  },
  customFields: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits([
  'system-prompt-change',
  'reasoning-language-change',
  'confirmed-only-change',
  'include-cot-change'
]);

const { t } = useI18n();
const router = useRouter();

const token = ref('');
const datasetName = ref('');
const isPrivate = ref(false);
const uploading = ref(false);
const error = ref('');
const success = ref(false);
const datasetUrl = ref('');
const hasToken = ref(false);
const loading = ref(true);

// 从配置中获取 huggingfaceToken
const fetchToken = async () => {
  try {
    loading.value = true;
    const response = await http.get(`/projects/${props.projectId}/config`);
    const data = response?.data || response;
    if (data.huggingfaceToken) {
      token.value = data.huggingfaceToken;
      hasToken.value = true;
    }
  } catch (err) {
    console.error('获取 HuggingFace Token 失败:', err);
  } finally {
    loading.value = false;
  }
};

// 处理上传数据集到 HuggingFace
const handleUpload = async () => {
  if (!hasToken.value) {
    return;
  }

  if (!datasetName.value) {
    error.value = t('export.datasetNameRequired', '请输入数据集名称');
    ElMessage.error(error.value);
    return;
  }

  try {
    uploading.value = true;
    error.value = '';
    success.value = false;

    const response = await http.post(`/projects/${props.projectId}/huggingface/upload`, {
      token: token.value,
      datasetName: datasetName.value,
      isPrivate: isPrivate.value,
      formatType: props.formatType,
      systemPrompt: props.systemPrompt,
      reasoningLanguage: props.reasoningLanguage,
      confirmedOnly: props.confirmedOnly,
      includeCOT: props.includeCOT,
      fileFormat: props.fileFormat,
      customFields: props.formatType === 'custom' ? props.customFields : undefined
    });

    const data = response?.data || response;
    success.value = true;
    datasetUrl.value = data.url || '';
    ElMessage.success(t('export.uploadSuccess', '上传成功'));
  } catch (err) {
    error.value = err.message || t('export.uploadFailed', '上传失败');
    ElMessage.error(error.value);
  } finally {
    uploading.value = false;
  }
};

watch(() => props.projectId, () => {
  if (props.projectId) {
    fetchToken();
  }
}, { immediate: true });
</script>

<style scoped>
.huggingface-tab {
  padding: 20px 0;
}

.section {
  margin-bottom: 24px;
}

.section-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
}

.section-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
}

.sub-section {
  margin-bottom: 16px;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  margin-bottom: 12px;
}

.options-checkboxes {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}
</style>

