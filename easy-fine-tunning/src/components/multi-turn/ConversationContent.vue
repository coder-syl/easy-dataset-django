<template>
  <div class="conversation-content">
    <h3 class="content-title">{{ $t('datasets.conversationContent') }}</h3>

    <div class="messages-container" :class="{ 'edit-mode': editMode }">
      <div v-for="(message, index) in displayMessages" :key="index" class="message-item">
        <div class="message-header">
          <el-tag :type="getRoleTagType(message.role)" size="small">
            {{ getRoleDisplay(message.role) }}
          </el-tag>
          <span v-if="message.role !== 'system'" class="round-label">
            {{ $t('datasets.round', { round: Math.floor((index + 1) / 2) + 1 }) }}
          </span>
        </div>
        <el-card class="message-card" shadow="never">
          <template v-if="editMode">
            <el-input
              v-model="localMessages[index].content"
              type="textarea"
              :rows="3"
              :autosize="{ minRows: 3, maxRows: 10 }"
              @input="handleMessageChange(index, $event)"
            />
          </template>
          <template v-else>
            <pre class="message-text">{{ message.content }}</pre>
          </template>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  editMode: {
    type: Boolean,
    default: false
  },
  conversation: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['message-change']);

const { t } = useI18n();

const localMessages = ref([...props.messages]);

watch(
  () => props.messages,
  (newMessages) => {
    localMessages.value = [...newMessages];
  },
  { deep: true }
);

const displayMessages = computed(() => {
  return props.editMode ? localMessages.value : props.messages;
});

// 获取角色显示信息
const getRoleDisplay = (role) => {
  switch (role) {
    case 'system':
      return t('datasets.system');
    case 'user':
      return props.conversation?.roleA || t('datasets.user');
    case 'assistant':
      return props.conversation?.roleB || t('datasets.assistant');
    default:
      return role;
  }
};

// 获取角色标签类型
const getRoleTagType = (role) => {
  switch (role) {
    case 'system':
      return 'info';
    case 'user':
      return 'primary';
    case 'assistant':
      return 'success';
    default:
      return '';
  }
};

// 处理消息内容变化
const handleMessageChange = (index, newContent) => {
  emit('message-change', index, newContent);
};
</script>

<style scoped>
.conversation-content {
  width: 100%;
}

.content-title {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 16px;
}

.messages-container {
  max-height: 70vh;
  overflow-y: auto;
}

.messages-container.edit-mode {
  max-height: none;
}

.message-item {
  margin-bottom: 16px;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.round-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.message-card {
  border: 1px solid var(--el-border-color);
}

.message-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  line-height: 1.6;
  margin: 0;
  font-size: 14px;
}
</style>

