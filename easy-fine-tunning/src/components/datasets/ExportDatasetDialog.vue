<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('export.title', '导出数据集')"
    width="800px"
    @close="handleClose"
  >
    <el-form label-width="120px">
      <el-form-item :label="$t('export.formatType', '格式类型')">
        <el-radio-group v-model="exportOptions.formatType">
          <el-radio label="alpaca">Alpaca</el-radio>
          <el-radio label="sharegpt">ShareGPT</el-radio>
          <el-radio label="multilingualthinking">Multilingual Thinking</el-radio>
          <el-radio label="custom">{{ $t('export.custom', '自定义') }}</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item :label="$t('export.fileFormat', '文件格式')">
        <el-radio-group v-model="exportOptions.fileFormat">
          <el-radio label="json">JSON</el-radio>
          <el-radio label="jsonl">JSONL</el-radio>
          <el-radio label="csv">CSV</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item :label="$t('export.includeCOT', '包含思维链')">
        <el-switch v-model="exportOptions.includeCOT" />
      </el-form-item>

      <el-form-item :label="$t('export.systemPrompt', '系统提示词')">
        <el-input
          v-model="exportOptions.systemPrompt"
          type="textarea"
          :rows="3"
          :placeholder="$t('export.systemPromptPlaceholder', '可选，输入系统提示词')"
        />
      </el-form-item>

      <el-form-item v-if="exportOptions.formatType === 'alpaca'" :label="$t('export.alpacaFieldType', '字段类型')">
        <el-radio-group v-model="exportOptions.alpacaFieldType">
          <el-radio label="instruction">{{ $t('export.instruction', 'Instruction') }}</el-radio>
          <el-radio label="input">{{ $t('export.input', 'Input') }}</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item
        v-if="exportOptions.formatType === 'alpaca' && exportOptions.alpacaFieldType === 'input'"
        :label="$t('export.customInstruction', '自定义 Instruction')"
      >
        <el-input
          v-model="exportOptions.customInstruction"
          :placeholder="$t('export.customInstructionPlaceholder', '输入自定义 instruction')"
        />
      </el-form-item>

      <el-form-item
        v-if="exportOptions.formatType === 'multilingualthinking'"
        :label="$t('export.reasoningLanguage', '推理语言')"
      >
        <el-input
          v-model="exportOptions.reasoningLanguage"
          :placeholder="$t('export.reasoningLanguagePlaceholder', '例如：English')"
        />
      </el-form-item>

      <el-form-item v-if="exportOptions.formatType === 'custom'" :label="$t('export.customFields', '自定义字段')">
        <el-form :inline="true" label-width="100px">
          <el-form-item :label="$t('export.questionField', '问题字段')">
            <el-input v-model="exportOptions.customFields.questionField" style="width: 150px" />
          </el-form-item>
          <el-form-item :label="$t('export.answerField', '答案字段')">
            <el-input v-model="exportOptions.customFields.answerField" style="width: 150px" />
          </el-form-item>
          <el-form-item :label="$t('export.cotField', '思维链字段')">
            <el-input v-model="exportOptions.customFields.cotField" style="width: 150px" />
          </el-form-item>
        </el-form>
        <el-checkbox v-model="exportOptions.customFields.includeLabels">
          {{ $t('export.includeLabels', '包含标签') }}
        </el-checkbox>
        <el-checkbox v-model="exportOptions.customFields.includeChunk">
          {{ $t('export.includeChunk', '包含文本块内容') }}
        </el-checkbox>
        <el-checkbox v-model="exportOptions.customFields.questionOnly">
          {{ $t('export.questionOnly', '仅导出问题') }}
        </el-checkbox>
      </el-form-item>

      <el-form-item :label="$t('export.confirmedOnly', '仅导出已确认')">
        <el-switch v-model="exportOptions.confirmedOnly" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">{{ $t('common.cancel', '取消') }}</el-button>
      <el-button type="primary" @click="handleExport">{{ $t('export.export', '导出') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

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

const handleExport = () => {
  emit('export', { ...exportOptions.value });
};
</script>

<style scoped>
:deep(.el-form-item) {
  margin-bottom: 20px;
}
</style>

