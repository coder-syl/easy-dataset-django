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

      <div v-if="files.length > 0" class="generated-files" style="margin-top:12px">
        <div style="margin-bottom:8px;font-weight:600">{{ $t('export.generatedFiles', '已生成文件') }}</div>
        <el-tag
          v-for="(f, idx) in files"
          :key="idx"
      style="margin-right:8px; margin-bottom:8px; cursor: pointer"
          type="info"
        >
          <span style="margin-right:8px; text-decoration: underline; color: #2b8cf6; cursor: pointer" @click="previewFile(f.path)">{{ fileNameFromPath(f.path) }}</span>
          <el-button type="text" size="small" @click="downloadFile(f.path)">{{ $t('common.download', '下载') }}</el-button>
        </el-tag>
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
 
  <el-dialog :title="previewFileName" v-model:visible="previewVisible" width="70%" :destroy-on-close="false">
    <div style="max-height:60vh; overflow:auto; background:#f7f7f7; padding:12px; border-radius:4px">
      <pre style="white-space:pre-wrap; word-break:break-word; font-size:13px; line-height:1.4">{{ previewContent }}</pre>
    </div>
    <template #footer>
      <el-button @click="previewVisible = false">{{ $t('common.close', '关闭') }}</el-button>
      <el-button type="primary" @click="downloadFile(previewFileName)">{{ $t('common.download', '下载') }}</el-button>
    </template>
  </el-dialog>
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
  datasetType: {
    type: String,
    default: 'single'
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
const files = ref([]);
const previewVisible = ref(false);
const previewContent = ref('');
const previewFileName = ref('');
const previewFilePath = ref('');

const configPathDisplay = computed(() => {
  return configPath.value.replace('dataset_info.json', '');
});

// 检查配置文件是否存在
const checkConfig = async () => {
  try {
    const response = await http.get(`/projects/${props.projectId}/llamaFactory/checkConfig/`, {
      params: { datasetType: props.datasetType }
    });
    const data = response || {};
    configExists.value = data.exists || false;
    if (data.exists && data.configPath) {
      configPath.value = data.configPath;
    }
    files.value = data.files || [];
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
      includeCOT: props.includeCOT,
      datasetType: props.datasetType
    });
    // response is expected to be the data object returned from backend (files, configPath, etc.)
    const data = response || {};
    configExists.value = true;
    if (data.configPath) {
      configPath.value = data.configPath;
    }
    files.value = data.files || [];

    ElMessage.success(t('export.configGenerated', '配置生成成功'));

    // 自动触发下载已生成的文件
    if (files.value.length > 0) {
      for (const f of files.value) {
        // 从服务器下载每个文件（后台会返回相对文件名或完整路径）
        downloadFile(f.path);
      }
    }
  } catch (err) {
    error.value = err.message || t('export.configGenerateFailed', '配置生成失败');
    ElMessage.error(error.value);
  } finally {
    generating.value = false;
  }
};

// 从后端返回的路径中提取文件名
const fileNameFromPath = (p) => {
  if (!p) return '';
  const parts = p.split(/[\\/]/);
  return parts[parts.length - 1];
};

// 下载指定文件（向后端 download 接口请求 blob）
const downloadFile = async (path) => {
  try {
    // pass the full relative path returned by backend (may include subdir)
    const resp = await http.get(`/projects/${props.projectId}/llamaFactory/download/`, {
      params: { file: path },
      responseType: 'blob'
    });
    // resp is a Blob (http interceptor will return blob directly)
    const url = window.URL.createObjectURL(resp);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileNameFromPath(path);
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (e) {
    console.error('下载失败', e);
    ElMessage.error(t('export.downloadFailed', '文件下载失败'));
  }
};

// 预览指定文件内容（优先以文本形式获取）
const previewFile = async (path) => {
  try {
    const fileName = fileNameFromPath(path);
    previewFileName.value = fileName;
    previewFilePath.value = path;
    previewContent.value = '';
    // 获取文本内容
    const resp = await http.get(`/projects/${props.projectId}/llamaFactory/download/`, {
      params: { file: fileName },
      responseType: 'text'
    });
    let text = resp || '';
    // 如果是 JSON 文件，尝试格式化
    try {
      if (fileName.endsWith('.json') || fileName.endsWith('.jsonl')) {
        // 对于 jsonl 尝试逐行格式化
        if (fileName.endsWith('.jsonl')) {
          const lines = text.split(/\r?\n/).filter(Boolean);
          const pretty = lines.map(l => {
            try {
              return JSON.stringify(JSON.parse(l), null, 2);
            } catch (e) {
              return l;
            }
          }).join('\n\n');
          text = pretty;
        } else {
          try {
            text = JSON.stringify(JSON.parse(text), null, 2);
          } catch (e) {
            // 如果不是标准 JSON，尝试把它当作 jsonl（多个 JSON 对象按行或连续对象）来解析
            const lines = text.split(/\r?\n/).filter(Boolean);
            const parsedItems = [];
            for (const l of lines) {
              try {
                parsedItems.push(JSON.parse(l));
              } catch (err) {
                // 忽略不能解析的行
              }
            }
            if (parsedItems.length > 0) {
              text = JSON.stringify(parsedItems, null, 2);
            } else {
              // 尝试提取第一个完整的 JSON 对象（匹配大括号深度）
              const extractFirstJsonObject = (s) => {
                const start = s.indexOf('{');
                if (start === -1) return null;
                let depth = 0;
                for (let i = start; i < s.length; i++) {
                  const ch = s[i];
                  if (ch === '{') depth++;
                  else if (ch === '}') depth--;
                  if (depth === 0) {
                    return s.slice(start, i + 1);
                  }
                }
                return null;
              };
              const firstObj = extractFirstJsonObject(text);
              if (firstObj) {
                try {
                  text = JSON.stringify(JSON.parse(firstObj), null, 2);
                } catch (err2) {
                  // 最终回退到原始文本
                  console.warn('preview format fallback parse failed', err2);
                }
              } else {
                console.warn('preview format error', e);
              }
            }
          }
        }
      }
    } catch (e) {
      // ignore format errors, keep raw text
      console.warn('preview format error', e);
    }
    previewContent.value = text;
    previewVisible.value = true;
  } catch (e) {
    console.error('预览失败', e);
    ElMessage.error(t('export.previewFailed', '文件预览失败'));
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

