<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('export.title', '导出数据集')"
    width="900px"
    @close="handleClose"
  >
    <!-- 标签页 -->
    <el-tabs v-model="currentTab" class="export-tabs">
      <el-tab-pane :label="$t('export.localTab', '导出到本地')" name="local">
        <LocalExportTab
          :file-format="exportOptions.fileFormat"
          :format-type="exportOptions.formatType"
          :system-prompt="exportOptions.systemPrompt"
          :reasoning-language="exportOptions.reasoningLanguage"
          :confirmed-only="exportOptions.confirmedOnly"
          :include-cot="exportOptions.includeCOT"
          :custom-fields="exportOptions.customFields"
          :alpaca-field-type="exportOptions.alpacaFieldType"
          :custom-instruction="exportOptions.customInstruction"
          :project-id="projectId"
          @file-format-change="exportOptions.fileFormat = $event"
          @format-change="exportOptions.formatType = $event"
          @system-prompt-change="exportOptions.systemPrompt = $event"
          @reasoning-language-change="exportOptions.reasoningLanguage = $event"
          @confirmed-only-change="exportOptions.confirmedOnly = $event"
          @include-cot-change="exportOptions.includeCOT = $event"
          @custom-field-change="handleCustomFieldChange"
          @include-labels-change="exportOptions.customFields.includeLabels = $event"
          @include-chunk-change="exportOptions.customFields.includeChunk = $event"
          @question-only-change="exportOptions.customFields.questionOnly = $event"
          @alpaca-field-type-change="exportOptions.alpacaFieldType = $event"
          @custom-instruction-change="exportOptions.customInstruction = $event"
          @export="handleExport"
          @balanced-export="handleBalancedExport"
        />
      </el-tab-pane>
      <el-tab-pane :label="$t('export.llamaFactoryTab', '在 LLaMA Factory 中使用')" name="llamaFactory">
        <LlamaFactoryTab
          :project-id="projectId"
          dataset-type="single"
          :system-prompt="exportOptions.systemPrompt"
          :reasoning-language="exportOptions.reasoningLanguage"
          :confirmed-only="exportOptions.confirmedOnly"
          :include-cot="exportOptions.includeCOT"
          :format-type="exportOptions.formatType"
          @system-prompt-change="exportOptions.systemPrompt = $event"
          @reasoning-language-change="exportOptions.reasoningLanguage = $event"
          @confirmed-only-change="exportOptions.confirmedOnly = $event"
          @include-cot-change="exportOptions.includeCOT = $event"
        />
      </el-tab-pane>
      <el-tab-pane :label="$t('export.huggingFaceTab', '上传至 Hugging Face')" name="huggingFace">
        <HuggingFaceTab
          :project-id="projectId"
          :system-prompt="exportOptions.systemPrompt"
          :reasoning-language="exportOptions.reasoningLanguage"
          :confirmed-only="exportOptions.confirmedOnly"
          :include-cot="exportOptions.includeCOT"
          :format-type="exportOptions.formatType"
          :file-format="exportOptions.fileFormat"
          :custom-fields="exportOptions.customFields"
          @system-prompt-change="exportOptions.systemPrompt = $event"
          @reasoning-language-change="exportOptions.reasoningLanguage = $event"
          @confirmed-only-change="exportOptions.confirmedOnly = $event"
          @include-cot-change="exportOptions.includeCOT = $event"
        />
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import LocalExportTab from './export/LocalExportTab.vue';
import LlamaFactoryTab from './export/LlamaFactoryTab.vue';
import HuggingFaceTab from './export/HuggingFaceTab.vue';

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  projectId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['update:open', 'export']);

const dialogVisible = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val)
});

// debug logs
onMounted(() => {
  console.log('[ExportDatasetDialog] mounted, open=', props.open);
});
watch(() => props.open, (v) => {
  console.log('[ExportDatasetDialog] prop open changed:', v);
});

const currentTab = ref('local');

const exportOptions = ref({
  formatType: 'alpaca',
  fileFormat: 'json',
  includeCOT: true,
  systemPrompt: '',
  alpacaFieldType: 'instruction',
  customInstruction: '',
  reasoningLanguage: 'English',
  confirmedOnly: false,
  customFields: {
    questionField: 'instruction',
    answerField: 'output',
    cotField: 'complexCOT',
    includeLabels: false,
    includeChunk: false,
    questionOnly: false
  },
  balanceMode: false,
  balanceConfig: []
});

const handleClose = () => {
  dialogVisible.value = false;
};

const handleCustomFieldChange = (field, value) => {
  exportOptions.value.customFields[field] = value;
};

const handleExport = (options) => {
  // 如果 LocalExportTab 传入了完整的导出配置（例如平衡导出），直接使用该配置
  if (options && typeof options === 'object' && options.balanceMode) {
    emit('export', options);
    return;
  }

  // 否则使用当前对话框内的状态组装导出配置
  emit('export', {
    ...exportOptions.value,
    ...options
  });
};

const handleBalancedExport = (options) => {
  emit('export', options);
};
</script>

<style scoped>
:deep(.el-form-item) {
  margin-bottom: 20px;
}
</style>

