<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('import.title', '导入数据集')"
    width="800px"
    @close="handleClose"
  >
    <el-steps :active="currentStep" align-center>
      <el-step :title="$t('import.fileUpload', '文件上传')" />
      <el-step :title="$t('import.mapFields', '字段映射')" />
      <el-step :title="$t('import.importing', '导入中')" />
    </el-steps>

    <div class="step-content">
      <FileUploadStep
        v-if="currentStep === 0"
        @data-loaded="handleDataLoaded"
        @error="handleError"
      />
      <FieldMappingStep
        v-if="currentStep === 1"
        :preview-data="importData.previewData"
        @mapping-complete="handleFieldMappingComplete"
        @error="handleError"
      />
      <ImportProgressStep
        v-if="currentStep === 2"
        :project-id="projectId"
        :import-data="importData"
        @import-complete="handleImportComplete"
        @error="handleError"
      />
    </div>

    <el-alert v-if="error" :title="error" type="error" :closable="false" style="margin-top: 16px" />

    <template #footer>
      <el-button :disabled="currentStep === 0" @click="handleBack">{{ $t('common.back', '上一步') }}</el-button>
      <el-button @click="handleClose">{{ $t('common.cancel', '取消') }}</el-button>
      <el-button
        v-if="currentStep < 2"
        type="primary"
        :disabled="!canNext"
        @click="handleNext"
      >
        {{ $t('common.next', '下一步') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue';
import FileUploadStep from './import/FileUploadStep.vue';
import FieldMappingStep from './import/FieldMappingStep.vue';
import ImportProgressStep from './import/ImportProgressStep.vue';

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

const emit = defineEmits(['update:open', 'import-success']);

const dialogVisible = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val)
});

const currentStep = ref(0);
const error = ref('');
const importData = ref({
  rawData: null,
  previewData: null,
  fieldMapping: {},
  sourceInfo: null
});

const canNext = computed(() => {
  if (currentStep.value === 0) {
    return !!importData.value.rawData;
  }
  if (currentStep.value === 1) {
    return Object.keys(importData.value.fieldMapping).length > 0;
  }
  return false;
});

const handleNext = () => {
  if (currentStep.value < 2) {
    currentStep.value++;
  }
};

const handleBack = () => {
  if (currentStep.value > 0) {
    currentStep.value--;
  }
};

const handleClose = () => {
  currentStep.value = 0;
  importData.value = {
    rawData: null,
    previewData: null,
    fieldMapping: {},
    sourceInfo: null
  };
  error.value = '';
  dialogVisible.value = false;
};

const handleDataLoaded = (data, preview, source) => {
  importData.value = {
    ...importData.value,
    rawData: data,
    previewData: preview,
    sourceInfo: source
  };
  error.value = '';
  handleNext();
};

const handleFieldMappingComplete = (mapping) => {
  importData.value = {
    ...importData.value,
    fieldMapping: mapping
  };
  handleNext();
};

const handleImportComplete = () => {
  handleClose();
  emit('import-success');
};

const handleError = (err) => {
  error.value = err;
};
</script>

<style scoped>
.step-content {
  margin-top: 24px;
  min-height: 300px;
}
</style>

