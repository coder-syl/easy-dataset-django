<template>
  <el-dialog
    :title="$t('batchEdit.title', '批量编辑')"
    :model-value="visible"
    @update:modelValue="onUpdateModelValue"
    width="720px"
    :close-on-click-modal="!loading"
    :close-on-press-escape="!loading"
  >
    <div>
      <el-alert
        :title="selectedInfo"
        type="info"
        show-icon
        class="mb-4"
      />

      <el-form label-position="top">
        <el-form-item :label="$t('batchEdit.position', '添加位置')">
          <el-radio-group v-model="position" size="small">
            <el-radio label="start">{{ $t('batchEdit.atBeginning', '开头添加') }}</el-radio>
            <el-radio label="end">{{ $t('batchEdit.atEnd', '结尾添加') }}</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item :label="$t('batchEdit.contentToAdd', '添加内容')">
          <el-input
            type="textarea"
            :rows="8"
            v-model="content"
            :placeholder="$t('batchEdit.contentPlaceholder', '输入要添加的内容')"
            :disabled="loading"
          />
          <div class="el-form-item__error" v-if="error">{{ error }}</div>
        </el-form-item>

        <div v-if="content.trim()" class="preview-box">
          <div class="preview-title">{{ $t('batchEdit.preview', '预览') }}:</div>
          <div class="preview-content">
            <pre v-if="position === 'start'"><span class="added">{{ content }}</span>
            
[原始文本块内容...]</pre>
            <pre v-else>[原始文本块内容...]
            
<span class="added">{{ content }}</span></pre>
          </div>
        </div>
      </el-form>
    </div>

    <template #footer>
      <el-button @click="handleClose" :disabled="loading">{{ $t('common.cancel', '取消') }}</el-button>
      <el-button type="primary" :loading="loading" :disabled="!content.trim() || selectedCount === 0" @click="handleConfirm">
        {{ loading ? $t('batchEdit.processing', '处理中') : $t('batchEdit.applyToChunks', { count: selectedCount }, '应用到选中文本块') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  selectedChunkIds: {
    type: Array,
    default: () => [],
  },
  totalChunks: {
    type: Number,
    default: 0,
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emits = defineEmits(['update:visible', 'confirm']);

const { t } = useI18n();

const position = ref('start');
const content = ref('');
const error = ref('');

const selectedCount = computed(() => props.selectedChunkIds.length || 0);

const selectedInfo = computed(() => {
  if (selectedCount.value === props.totalChunks) {
    return t('batchEdit.allChunksSelected', { count: props.totalChunks }, `已选择全部 ${props.totalChunks} 个文本块`);
  }
  return t('batchEdit.selectedChunks', { selected: selectedCount.value, total: props.totalChunks }, `已选择 ${selectedCount.value} 个文本块`);
});

watch(() => props.visible, (v) => {
  if (!v) {
    // reset when closed
    position.value = 'start';
    content.value = '';
    error.value = '';
  }
});

const handleClose = () => {
  if (!props.loading) {
    emits('update:visible', false);
  }
};

const onUpdateModelValue = (val) => {
  emits('update:visible', val);
};

const handleConfirm = () => {
  if (!content.value.trim()) {
    error.value = t('batchEdit.contentRequired', '请输入要添加的内容');
    return;
  }

  emits('confirm', {
    position: position.value,
    content: content.value.trim(),
    chunkIds: props.selectedChunkIds,
  });
};
</script>

<style scoped>
.mb-4 { margin-bottom: 16px; }
.preview-box { margin-top: 8px; padding: 12px; border: 1px solid var(--el-border-color); border-radius: 4px; background: var(--el-bg-color-2); }
.preview-title { font-weight: 600; margin-bottom: 8px; }
.preview-content pre { white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", "Segoe UI Mono", "Noto Mono", monospace; background: transparent; margin: 0; }
.added { background-color: #e3f2fd; padding: 2px 4px; border-radius: 2px; }
</style>


