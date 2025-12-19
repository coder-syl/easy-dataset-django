<template>
  <div class="llama-factory-tab">
    <el-alert v-if="error" :title="error" type="error" :closable="false" style="margin-bottom: 16px" />

    <div class="section">
      <div class="section-title">{{ $t('export.systemPrompt', '系统提示词') }}</div>
      <el-input
        :model-value="systemPrompt"
        type="textarea"
        :rows="3"
        @input="$emit('system-prompt-change', $event)"
      />
    </div>

    <div v-if="formatType === 'multilingualthinking'" class="section">
      <div class="section-title">{{ $t('export.reasoningLanguage', '推理语言') }}</div>
      <el-input
        :model-value="reasoningLanguage"
        :placeholder="$t('export.reasoningLanguagePlaceholder', '例如：English')"
        @input="$emit('reasoning-language-change', $event)"
      />
    </div>

    <div class="section">
      <el-checkbox :model-value="confirmedOnly" @change="$emit('confirmed-only-change', $event)">
        {{ $t('export.onlyConfirmed', '仅导出已确认数据') }}
      </el-checkbox>
      <el-checkbox :model-value="includeCOT" @change="$emit('include-cot-change', $event)">
        {{ $t('export.includeCOT', '包含思维链') }}
      </el-checkbox>
    </div>

    <div v-if="configExists" class="section">
      <el-alert
        :title="$t('export.configExists', '配置文件已存在')"
        type="success"
        :closable="false"
        style="margin-bottom: 16px"
      />
      <div class="config-path">
        <span>{{ $t('export.configPath', '配置路径') }}: {{ configPathDisplay }}</span>
        <el-button
          :icon="copied ? Check : CopyDocument"
          size="small"
          @click="handleCopyPath"
        >
          {{ copied ? $t('common.copied', '已复制') : $t('common.copy', '复制') }}
        </el-button>
      </div>
    </div>

    <div v-else class="section">
      <div class="no-config-text">
        {{ $t('export.noConfig', '配置文件不存在') }}
      </div>
    </div>

    <div class="actions">
      <el-button
        type="primary"
        :loading="generating"
        @click="handleGenerateConfig"
      >
        {{ generating
          ? $t('export.generating', '生成中...')
          : configExists
            ? $t('export.updateConfig', '更新配置')
            : $t('export.generateConfig', '生成配置')
        }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { CopyDocument, Check } from '@element-plus/icons-vue';
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
  }
});

const emit = defineEmits([
  'system-prompt-change',
  'reasoning-language-change',
  'confirmed-only-change',
  'include-cot-change'
]);

const { t } = useI18n();

const configExists = ref(false);
const configPath = ref('');
const generating = ref(false);
const error = ref('');
const copied = ref(false);

const configPathDisplay = computed(() => {
  return configPath.value.replace('dataset_info.json', '');
});

// 检查配置文件是否存在
const checkConfig = async () => {
  try {
    const response = await http.get(`/projects/${props.projectId}/llamaFactory/checkConfig/`);
    const data = response?.data || response;
    configExists.value = data.exists || false;
    if (data.exists && data.configPath) {
      configPath.value = data.configPath;
    }
  } catch (err) {
    console.error('检查配置失败:', err);
  }
};

// 复制路径到剪贴板
const handleCopyPath = async () => {
  try {
    await navigator.clipboard.writeText(configPathDisplay.value);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
    ElMessage.success(t('common.copied', '已复制'));
  } catch (err) {
    ElMessage.error(t('common.copyFailed', '复制失败'));
  }
};

// 处理生成 Llama Factory 配置
const handleGenerateConfig = async () => {
  try {
    generating.value = true;
    error.value = '';

    const response = await http.post(`/projects/${props.projectId}/llamaFactory/generate/`, {
      formatType: props.formatType,
      systemPrompt: props.systemPrompt,
      reasoningLanguage: props.reasoningLanguage,
      confirmedOnly: props.confirmedOnly,
      includeCOT: props.includeCOT
    });

    configExists.value = true;
    ElMessage.success(t('export.configGenerated', '配置生成成功'));
    await checkConfig();
  } catch (err) {
    error.value = err.message || t('export.configGenerateFailed', '配置生成失败');
    ElMessage.error(error.value);
  } finally {
    generating.value = false;
  }
};

watch(() => props.projectId, () => {
  if (props.projectId) {
    checkConfig();
  }
}, { immediate: true });
</script>

<style scoped>
.llama-factory-tab {
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

.config-path {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.no-config-text {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}
</style>

