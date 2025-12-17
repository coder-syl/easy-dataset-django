<template>
  <el-card v-if="!currentPromptConfig" class="empty-card">
    <el-empty :description="$t('settings.prompts.selectPromptFirst', '请先选择提示词')" />
  </el-card>

  <el-card v-else>
    <template #header>
      <div class="card-header">
        <div class="header-left">
          <h3>{{ currentPromptConfig.name }}</h3>
          <el-tag v-if="isCustomized(selectedPrompt)" type="primary" size="small">
            {{ $t('settings.prompts.customized', '已自定义') }}
          </el-tag>
        </div>
        <div class="header-right">
          <el-button type="primary" :icon="Edit" @click="handleEditClick">
            {{ $t('settings.prompts.editPrompt', '编辑提示词') }}
          </el-button>
          <el-button
            v-if="isCustomized(selectedPrompt)"
            type="danger"
            :icon="Delete"
            @click="handleDeleteClick"
          >
            {{ $t('settings.prompts.restoreDefault', '恢复默认') }}
          </el-button>
        </div>
      </div>
    </template>

    <div class="prompt-description">
      <el-text type="info">{{ currentPromptConfig.description }}</el-text>
    </div>

    <el-divider />

    <div class="prompt-content">
      <div class="markdown-content" v-html="renderedContent"></div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue';
import { Edit, Delete } from '@element-plus/icons-vue';

const props = defineProps({
  currentPromptConfig: {
    type: Object,
    default: null,
  },
  selectedPrompt: {
    type: String,
    default: null,
  },
  promptContent: {
    type: String,
    default: '',
  },
  isCustomized: {
    type: Function,
    required: true,
  },
});

const emit = defineEmits(['edit-click', 'delete-click']);

// 简单的 Markdown 渲染（不使用外部库）
const renderedContent = computed(() => {
  if (!props.promptContent) {
    return '';
  }
  let content = props.promptContent;
  // 简单的 Markdown 转换
  content = content
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/`([^`]+)`/gim, '<code>$1</code>')
    .replace(/\n/gim, '<br>');
  return content;
});

const handleEditClick = () => {
  emit('edit-click');
};

const handleDeleteClick = () => {
  emit('delete-click');
};
</script>

<style scoped>
.empty-card {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-right {
  display: flex;
  gap: 8px;
}

.prompt-description {
  margin-bottom: 16px;
}

.prompt-content {
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
  min-height: 200px;
}

.markdown-content {
  line-height: 1.6;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  margin-top: 16px;
  margin-bottom: 8px;
}

.markdown-content :deep(p) {
  margin-bottom: 8px;
}

.markdown-content :deep(code) {
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.markdown-content :deep(pre) {
  background: var(--el-fill-color-light);
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin-left: 20px;
  margin-bottom: 8px;
}
</style>

