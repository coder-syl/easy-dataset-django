<template>
  <div class="editable-field">
    <div class="field-header">
      <label class="field-label">{{ label }}</label>
      <div class="field-actions">
        <span v-if="tokenCount !== undefined" class="token-count">
          {{ $t('datasets.tokens', 'Token数') }}: {{ tokenCount }}
        </span>
        <el-button
          v-if="!editing && !optimizing"
          link
          type="primary"
          :icon="Edit"
          @click="$emit('edit')"
        >
          {{ $t('common.edit', '编辑') }}
        </el-button>
        <el-button
          v-if="!editing && dataset && onOptimize"
          link
          type="warning"
          :icon="MagicStick"
          :loading="optimizing"
          @click="$emit('optimize')"
        >
          {{ $t('datasets.optimize', 'AI优化') }}
        </el-button>
      </div>
    </div>

    <div v-if="editing" class="editing-mode">
      <el-input
        v-model="localValue"
        type="textarea"
        :rows="label.includes('思维链') ? 8 : 6"
        @input="$emit('input', $event)"
      />
      <div class="edit-actions">
        <el-button size="small" @click="$emit('cancel')">
          {{ $t('common.cancel', '取消') }}
        </el-button>
        <el-button type="primary" size="small" @click="$emit('save')">
          {{ $t('common.save', '保存') }}
        </el-button>
      </div>
    </div>

    <div v-else class="display-mode">
      <div v-if="isJson" class="json-content">
        <pre>{{ formattedJson }}</pre>
      </div>
      <div v-else-if="isMarkdown" class="markdown-content" v-html="renderedMarkdown"></div>
      <div v-else class="text-content">{{ value || $t('datasets.empty', '空') }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { Edit, MagicStick } from '@element-plus/icons-vue';

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: String,
    default: ''
  },
  editing: {
    type: Boolean,
    default: false
  },
  dataset: {
    type: Object,
    default: null
  },
  tokenCount: {
    type: Number,
    default: undefined
  },
  optimizing: {
    type: Boolean,
    default: false
  },
  onOptimize: {
    type: Function,
    default: null
  }
});

const emit = defineEmits(['edit', 'input', 'save', 'cancel', 'optimize']);

const localValue = ref(props.value);

watch(
  () => props.value,
  (newVal) => {
    localValue.value = newVal;
  }
);

const isJson = computed(() => {
  if (!props.value) return false;
  try {
    JSON.parse(props.value);
    return true;
  } catch {
    return false;
  }
});

const formattedJson = computed(() => {
  if (!isJson.value) return '';
  try {
    return JSON.stringify(JSON.parse(props.value), null, 2);
  } catch {
    return props.value;
  }
});

const isMarkdown = computed(() => {
  // 简单的 Markdown 检测
  return props.value && (props.value.includes('##') || props.value.includes('**'));
});

const renderedMarkdown = computed(() => {
  // 简单的 Markdown 渲染（实际可以使用 markdown-it 等库）
  if (!isMarkdown.value) return props.value;
  return props.value
    .replace(/## (.*)/g, '<h2>$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
});
</script>

<style scoped>
.editable-field {
  margin-bottom: 24px;
}

.field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.field-label {
  font-weight: 600;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.field-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.token-count {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.editing-mode {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.display-mode {
  min-height: 100px;
  padding: 12px;
  background-color: var(--el-bg-color-page);
  border-radius: 4px;
  border: 1px solid var(--el-border-color-light);
}

.json-content {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

.markdown-content {
  line-height: 1.6;
}

.text-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}
</style>

