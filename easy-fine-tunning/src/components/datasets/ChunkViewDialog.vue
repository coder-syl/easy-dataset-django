<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('textSplit.viewChunk', '查看文本块')"
    width="80%"
    @close="handleClose"
  >
    <div v-if="chunk" class="chunk-content">
      <el-descriptions :column="2" border>
        <el-descriptions-item :label="$t('textSplit.chunkName', '文本块名称')">
          {{ chunk.name || chunk.chunk_name }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('textSplit.chunkSize', '大小')">
          {{ chunk.content?.length || chunk.content?.length || 0 }} {{ $t('common.characters', '字符') }}
        </el-descriptions-item>
      </el-descriptions>
      <el-divider />
      <div class="content-display">
        <pre class="chunk-text">{{ chunk.content || chunk.content || '' }}</pre>
      </div>
    </div>
    <div v-else class="no-chunk">
      {{ $t('textSplit.noChunk', '文本块不存在') }}
    </div>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  chunk: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['update:open', 'close']);

const dialogVisible = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val)
});

const handleClose = () => {
  emit('close');
};
</script>

<style scoped>
.chunk-content {
  padding: 16px 0;
}

.content-display {
  margin-top: 16px;
  max-height: 60vh;
  overflow-y: auto;
}

.chunk-text {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 16px;
  background-color: var(--el-bg-color-page);
  border-radius: 4px;
  border: 1px solid var(--el-border-color-light);
}

.no-chunk {
  text-align: center;
  padding: 40px;
  color: var(--el-text-color-placeholder);
}
</style>

