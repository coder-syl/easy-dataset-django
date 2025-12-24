<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('datasets.multiTurnExport', '导出多轮对话')"
    width="900px"
    @close="handleClose"
  >
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
          @export="onLocalExport"
          @balanced-export="onBalancedExport"
        />
      </el-tab-pane>
      <el-tab-pane :label="$t('export.llamaFactoryTab', '在 LLaMA Factory 中使用')" name="llamaFactory">
        <LlamaFactoryTab
          :project-id="projectId"
          dataset-type="multi"
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
import { ref, computed, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { exportConversations } from '../../api/conversation';
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
  },
  selectedIds: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['update:open', 'exported']);
const { t } = useI18n();

// Use a local ref synced with prop to avoid v-model computed issues
const dialogVisible = ref(props.open);

watch(() => props.open, (v) => {
  dialogVisible.value = v;
});

watch(dialogVisible, (v) => {
  emit('update:open', v);
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

const onLocalExport = (options) => {
  // LocalExportTab emits export with options — forward to parent along with selectedIds
  emit('export', { ...exportOptions.value, ...options, selectedIds: props.selectedIds });
  dialogVisible.value = false;
};

const onBalancedExport = (options) => {
  emit('export', { ...options, selectedIds: props.selectedIds });
  dialogVisible.value = false;
};
// debug logs
onMounted(() => {
  console.log('[MultiTurnExportDialog] mounted, open=', props.open);
});

watch(() => props.open, (v) => {
  console.log('[MultiTurnExportDialog] prop open changed:', v);
  // debug: after prop becomes true, check DOM for dialog/overlay
  if (v) {
    setTimeout(() => {
      try {
        const wrappers = document.querySelectorAll('.el-dialog__wrapper');
        const dialogs = document.querySelectorAll('.el-dialog');
        const overlays = document.querySelectorAll('.v-overlay, .el-overlay, .el-overlay-mask, .el-overlay__mask');
        console.log('[MultiTurnExportDialog] DOM counts -> wrappers:', wrappers.length, 'dialogs:', dialogs.length, 'overlays:', overlays.length);
        // print titles of existing dialogs for inspection
        const titles = Array.from(document.querySelectorAll('.el-dialog__header')).map(h => h.textContent && h.textContent.trim());
        console.log('[MultiTurnExportDialog] existing dialog titles:', titles);
        // print last overlay's inner text snippet for clues
        if (overlays.length > 0) {
          const last = overlays[overlays.length - 1];
          console.log('[MultiTurnExportDialog] last overlay HTML snippet:', last.innerHTML.slice(0, 200));
        }
      } catch (e) {
        console.warn('DOM check failed', e);
      }
    }, 50);
  }
});
// ensure local dialogVisible logs also
watch(dialogVisible, (v) => {
  console.log('[MultiTurnExportDialog] local dialogVisible changed:', v);
});
</script>

<style scoped>
/* simple styles */
</style>


