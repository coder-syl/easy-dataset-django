<template>
  <div class="local-export-tab">
    <!-- 文件格式 -->
    <div class="section">
      <div class="section-title">{{ $t('export.fileFormat', '文件格式') }}</div>
      <el-radio-group v-model="localFileFormat" @change="handleFileFormatChange">
        <el-radio label="json">JSON</el-radio>
        <el-radio label="jsonl">JSONL</el-radio>
        <el-radio label="csv" :disabled="formatType === 'multilingualthinking'">CSV</el-radio>
      </el-radio-group>
    </div>

    <!-- 数据集风格 -->
    <div class="section">
      <div class="section-title">{{ $t('export.format', '数据集风格') }}</div>
      <el-radio-group v-model="localFormatType" @change="handleFormatChange">
        <el-radio label="alpaca">Alpaca</el-radio>
        <el-radio label="sharegpt">ShareGPT</el-radio>
        <el-radio label="multilingualthinking" :disabled="fileFormat === 'csv'">
          {{ $t('export.multilingualThinkingFormat', 'Multilingual-Thinking') }}
        </el-radio>
        <el-radio label="custom">{{ $t('export.customFormat', '自定义格式') }}</el-radio>
      </el-radio-group>
    </div>

    <!-- Alpaca 格式设置 -->
    <div v-if="formatType === 'alpaca'" class="section nested">
      <div class="section-subtitle">{{ $t('export.alpacaSettings', 'Alpaca 格式设置') }}</div>
      <div class="section-label">{{ $t('export.questionFieldType', '问题字段类型') }}</div>
      <el-radio-group v-model="localAlpacaFieldType" @change="handleAlpacaFieldTypeChange">
        <el-radio label="instruction">{{ $t('export.useInstruction', '使用 instruction 字段') }}</el-radio>
        <el-radio label="input">{{ $t('export.useInput', '使用 input 字段') }}</el-radio>
      </el-radio-group>
      <el-input
        v-if="alpacaFieldType === 'input'"
        v-model="localCustomInstruction"
        :placeholder="$t('export.instructionPlaceholder', '请输入固定的指令内容')"
        class="custom-instruction-input"
        @input="handleCustomInstructionChange"
      />
      <div v-if="alpacaFieldType === 'input'" class="form-tip">
        {{ $t('export.instructionHelperText', '当使用 input 字段时，可以在这里指定固定的 instruction 内容') }}
      </div>
    </div>

    <!-- 自定义格式选项 -->
    <div v-if="formatType === 'custom'" class="section nested">
      <div class="section-subtitle">{{ $t('export.customFormatSettings', '自定义格式设置') }}</div>
      <div class="custom-fields-row">
        <el-input
          v-model="localCustomFields.questionField"
          :placeholder="$t('export.questionFieldName', '问题字段名')"
          style="width: 200px"
          @input="(val) => handleCustomFieldChange('questionField', val)"
        />
        <el-input
          v-model="localCustomFields.answerField"
          :placeholder="$t('export.answerFieldName', '答案字段名')"
          style="width: 200px"
          @input="(val) => handleCustomFieldChange('answerField', val)"
        />
        <el-input
          v-model="localCustomFields.cotField"
          :placeholder="$t('export.cotFieldName', '思维链字段名')"
          style="width: 200px"
          @input="(val) => handleCustomFieldChange('cotField', val)"
        />
      </div>
      <div class="custom-checkboxes">
        <el-checkbox v-model="localCustomFields.includeLabels" @change="handleIncludeLabelsChange">
          {{ $t('export.includeLabels', '包含标签') }}
        </el-checkbox>
        <el-checkbox v-model="localCustomFields.includeChunk" @change="handleIncludeChunkChange">
          {{ $t('export.includeChunk', '包含文本块内容') }}
        </el-checkbox>
        <el-checkbox v-model="localCustomFields.questionOnly" @change="handleQuestionOnlyChange">
          {{ $t('export.questionOnly', '仅导出问题') }}
        </el-checkbox>
      </div>
    </div>

    <!-- 格式示例 -->
    <div class="section">
      <div class="section-title">{{ $t('export.example', '格式示例') }}</div>
      <el-card class="example-card">
        <pre class="example-code">{{ formatExample }}</pre>
      </el-card>
    </div>

    <!-- 系统提示词 -->
    <div class="section">
      <div class="section-title">{{ $t('export.systemPrompt', '系统提示词') }}</div>
      <el-input
        v-model="localSystemPrompt"
        type="textarea"
        :rows="3"
        :placeholder="$t('export.systemPromptPlaceholder', '请输入系统提示词...')"
        @input="handleSystemPromptChange"
      />
    </div>

    <!-- 推理语言（仅 Multilingual-Thinking） -->
    <div v-if="formatType === 'multilingualthinking'" class="section">
      <div class="section-title">{{ $t('export.Reasoninglanguage', '推理语言') }}</div>
      <el-input
        v-model="localReasoningLanguage"
        :placeholder="$t('export.ReasoninglanguagePlaceholder', '例如：English')"
        @input="handleReasoningLanguageChange"
      />
    </div>

    <!-- 选项 -->
    <div class="section">
      <el-checkbox v-model="localConfirmedOnly" @change="handleConfirmedOnlyChange">
        {{ $t('export.onlyConfirmed', '仅导出已确认数据') }}
      </el-checkbox>
      <el-checkbox v-model="localIncludeCOT" @change="handleIncludeCOTChange">
        {{ $t('export.includeCOT', '包含思维链') }}
      </el-checkbox>
    </div>

    <!-- 操作按钮 -->
    <div class="actions">
      <el-button @click="handleOpenBalanceDialog">{{ $t('exportDialog.balancedExport', '平衡导出') }}</el-button>
      <el-button type="primary" @click="handleExport">{{ $t('export.confirmExport', '确认导出') }}</el-button>
    </div>

    <!-- 平衡导出对话框 -->
    <BalanceExportDialog
      v-model:open="balanceDialogOpen"
      :project-id="projectId"
      :confirmed-only="confirmedOnly"
      @export="handleBalancedExport"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import BalanceExportDialog from './BalanceExportDialog.vue';

const props = defineProps({
  fileFormat: {
    type: String,
    default: 'json'
  },
  formatType: {
    type: String,
    default: 'alpaca'
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
  customFields: {
    type: Object,
    default: () => ({
      questionField: 'instruction',
      answerField: 'output',
      cotField: 'complexCOT',
      includeLabels: false,
      includeChunk: false,
      questionOnly: false
    })
  },
  alpacaFieldType: {
    type: String,
    default: 'instruction'
  },
  customInstruction: {
    type: String,
    default: ''
  },
  projectId: {
    type: String,
    required: true
  }
});

const emit = defineEmits([
  'file-format-change',
  'format-change',
  'system-prompt-change',
  'reasoning-language-change',
  'confirmed-only-change',
  'include-cot-change',
  'custom-field-change',
  'include-labels-change',
  'include-chunk-change',
  'question-only-change',
  'alpaca-field-type-change',
  'custom-instruction-change',
  'export',
  'balanced-export'
]);

const { t } = useI18n();

const localFileFormat = ref(props.fileFormat);
const localFormatType = ref(props.formatType);
const localSystemPrompt = ref(props.systemPrompt);
const localReasoningLanguage = ref(props.reasoningLanguage);
const localConfirmedOnly = ref(props.confirmedOnly);
const localIncludeCOT = ref(props.includeCOT);
const localAlpacaFieldType = ref(props.alpacaFieldType);
const localCustomInstruction = ref(props.customInstruction);
const localCustomFields = ref({ ...props.customFields });
const balanceDialogOpen = ref(false);

watch(() => props.fileFormat, (val) => { localFileFormat.value = val; });
watch(() => props.formatType, (val) => { localFormatType.value = val; });
watch(() => props.systemPrompt, (val) => { localSystemPrompt.value = val; });
watch(() => props.reasoningLanguage, (val) => { localReasoningLanguage.value = val; });
watch(() => props.confirmedOnly, (val) => { localConfirmedOnly.value = val; });
watch(() => props.includeCOT, (val) => { localIncludeCOT.value = val; });
watch(() => props.alpacaFieldType, (val) => { localAlpacaFieldType.value = val; });
watch(() => props.customInstruction, (val) => { localCustomInstruction.value = val; });
watch(() => props.customFields, (val) => { localCustomFields.value = { ...val }; }, { deep: true });

const handleFileFormatChange = (val) => {
  emit('file-format-change', val);
};

const handleFormatChange = (val) => {
  emit('format-change', val);
  // 根据格式类型设置默认字段名
  if (val === 'alpaca') {
    localCustomFields.value = {
      ...localCustomFields.value,
      questionField: 'instruction',
      answerField: 'output'
    };
  } else if (val === 'sharegpt') {
    localCustomFields.value = {
      ...localCustomFields.value,
      questionField: 'content',
      answerField: 'content'
    };
  } else if (val === 'multilingualthinking') {
    localCustomFields.value = {
      ...localCustomFields.value,
      questionField: 'content',
      answerField: 'content'
    };
  }
};

const handleSystemPromptChange = (val) => {
  emit('system-prompt-change', val);
};

const handleReasoningLanguageChange = (val) => {
  emit('reasoning-language-change', val);
};

const handleConfirmedOnlyChange = (val) => {
  emit('confirmed-only-change', val);
};

const handleIncludeCOTChange = (val) => {
  emit('include-cot-change', val);
};

const handleCustomFieldChange = (field, value) => {
  localCustomFields.value[field] = value;
  emit('custom-field-change', field, value);
};

const handleIncludeLabelsChange = (val) => {
  emit('include-labels-change', val);
};

const handleIncludeChunkChange = (val) => {
  emit('include-chunk-change', val);
};

const handleQuestionOnlyChange = (val) => {
  emit('question-only-change', val);
};

const handleAlpacaFieldTypeChange = (val) => {
  emit('alpaca-field-type-change', val);
};

const handleCustomInstructionChange = (val) => {
  emit('custom-instruction-change', val);
};

const handleOpenBalanceDialog = () => {
  balanceDialogOpen.value = true;
};

const handleExport = () => {
  emit('export', {
    formatType: localFormatType.value,
    fileFormat: localFileFormat.value,
    systemPrompt: localSystemPrompt.value,
    reasoningLanguage: localReasoningLanguage.value,
    confirmedOnly: localConfirmedOnly.value,
    includeCOT: localIncludeCOT.value,
    alpacaFieldType: localAlpacaFieldType.value,
    customInstruction: localCustomInstruction.value,
    customFields: localFormatType.value === 'custom' ? localCustomFields.value : undefined
  });
};

const handleBalancedExport = (options) => {
  emit('balanced-export', {
    ...options,
    formatType: localFormatType.value,
    fileFormat: localFileFormat.value,
    systemPrompt: localSystemPrompt.value,
    reasoningLanguage: localReasoningLanguage.value,
    confirmedOnly: localConfirmedOnly.value,
    includeCOT: localIncludeCOT.value,
    alpacaFieldType: localAlpacaFieldType.value,
    customInstruction: localCustomInstruction.value,
    customFields: localFormatType.value === 'custom' ? localCustomFields.value : undefined
  });
};

// 格式示例
const formatExample = computed(() => {
  if (localFormatType.value === 'alpaca') {
    if (localFileFormat.value === 'json') {
      return JSON.stringify(
        [
          {
            instruction: t('export.sampleInstruction', '人类指令（必填）'),
            input:
              localAlpacaFieldType.value === 'input'
                ? t('export.sampleInputOptional', '人类输入（选填）')
                : '',
            output: t('export.sampleOutput', '模型回答（必填）'),
            system: t('export.sampleSystem', '系统提示词（选填）')
          }
        ],
        null,
        2
      );
    } else if (localFileFormat.value === 'jsonl') {
      return JSON.stringify({
        instruction: t('export.sampleInstruction', '人类指令（必填）'),
        input:
          localAlpacaFieldType.value === 'input'
            ? t('export.sampleInputOptional', '人类输入（选填）')
            : '',
        output: t('export.sampleOutput', '模型回答（必填）'),
        system: t('export.sampleSystem', '系统提示词（选填）')
      });
    }
  } else if (localFormatType.value === 'sharegpt') {
    if (localFileFormat.value === 'json') {
      return JSON.stringify(
        [
          {
            messages: [
              {
                role: 'system',
                content: t('export.sampleSystem', '系统提示词（选填）')
              },
              {
                role: 'user',
                content: t('export.sampleUserMessage', '人类指令')
              },
              {
                role: 'assistant',
                content: t('export.sampleAssistantMessage', '模型回答')
              }
            ]
          }
        ],
        null,
        2
      );
    } else if (localFileFormat.value === 'jsonl') {
      return JSON.stringify({
        messages: [
          {
            role: 'system',
            content: t('export.sampleSystem', '系统提示词（选填）')
          },
          {
            role: 'user',
            content: t('export.sampleUserMessage', '人类指令')
          },
          {
            role: 'assistant',
            content: t('export.sampleAssistantMessage', '模型回答')
          }
        ]
      });
    }
  } else if (localFormatType.value === 'multilingualthinking') {
    if (localFileFormat.value === 'json') {
      return JSON.stringify(
        {
          reasoning_language: 'English',
          developer: t('export.sampleSystem', '系统提示词（选填）'),
          user: t('export.sampleUserMessage', '人类指令'),
          analysis: t('export.sampleAnalysis', '模型的思维链内容'),
          final: t('export.sampleFinal', '模型回答'),
          messages: [
            {
              content: t('export.sampleSystem', '系统提示词（选填）'),
              role: 'system',
              thinking: null
            },
            {
              content: t('export.sampleUserMessage', '人类指令'),
              role: 'user',
              thinking: null
            },
            {
              content: t('export.sampleFinal', '模型回答'),
              role: 'assistant',
              thinking: t('export.sampleThinking', '模型的思维链内容')
            }
          ]
        },
        null,
        2
      );
    }
  } else if (localFormatType.value === 'custom') {
    const example = {
      [localCustomFields.value.questionField]: t('sampleData.questionContent', '问题内容'),
      [localCustomFields.value.answerField]: t('sampleData.answerContent', '答案内容')
    };
    if (localIncludeCOT.value) {
      example[localCustomFields.value.cotField] = t('sampleData.cotContent', '思维链内容');
    }
    if (localCustomFields.value.includeLabels) {
      example.label = t('sampleData.domainLabel', '领域标签');
    }
    if (localCustomFields.value.includeChunk) {
      example.chunk = t('sampleData.textChunk', '文本块内容');
    }
    return localFileFormat.value === 'json' ? JSON.stringify([example], null, 2) : JSON.stringify(example);
  }
  return '';
});
</script>

<style scoped>
.local-export-tab {
  padding: 20px 0;
}

.section {
  margin-bottom: 24px;
}

.section.nested {
  padding-left: 20px;
  border-left: 2px solid var(--el-border-color-light);
  margin-left: 10px;
}

.section-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
}

.section-subtitle {
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
}

.section-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
}

.custom-fields-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.custom-checkboxes {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.custom-instruction-input {
  margin-top: 12px;
  max-width: 500px;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
}

.example-card {
  background-color: var(--el-fill-color-light);
}

.example-code {
  margin: 0;
  padding: 12px;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>

