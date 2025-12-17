<template>
  <!-- 用户消息 -->
  <div v-if="message.role === 'user'" class="message user-message">
    <div class="message-content user-content">
      <template v-if="typeof message.content === 'string'">
        <div class="message-text">{{ message.content }}</div>
      </template>
      <template v-else-if="Array.isArray(message.content)">
        <div
          v-for="(item, i) in message.content"
          :key="i"
        >
          <div v-if="item.type === 'text'" class="message-text">{{ item.text }}</div>
          <img
            v-else-if="item.type === 'image_url'"
            :src="item.image_url.url"
            alt="上传图片"
            class="message-image"
          />
        </div>
      </template>
    </div>
  </div>

  <!-- 助手消息 -->
  <div v-else-if="message.role === 'assistant'" class="message assistant-message">
    <div class="message-content assistant-content">
      <div v-if="modelName" class="model-name-label">{{ modelName }}</div>

      <!-- 推理过程 -->
      <div v-if="hasThinking" class="thinking-section">
        <div class="thinking-header" @click="showThinking = !showThinking">
          <div class="thinking-title">
            <el-icon>
              <Promotion v-if="message.isStreaming" />
              <InfoFilled v-else />
            </el-icon>
            <span>{{ $t('playground.reasoningProcess', '推理过程') }}</span>
          </div>
          <el-icon>
            <ArrowUp v-if="showThinking" />
            <ArrowDown v-else />
          </el-icon>
        </div>
        <el-collapse-transition>
          <div v-show="showThinking" class="thinking-content">
            {{ message.thinking }}
          </div>
        </el-collapse-transition>
      </div>

      <!-- 回答内容 -->
      <div class="message-text">
        <template v-if="typeof message.content === 'string'">
          <span v-html="formatContent(message.content)"></span>
          <span v-if="message.isStreaming" class="blinking-cursor">|</span>
        </template>
        <template v-else-if="Array.isArray(message.content)">
          <div
            v-for="(item, i) in message.content"
            :key="i"
          >
            <span v-if="item.type === 'text'" v-html="formatContent(item.text)"></span>
            <img
              v-else-if="item.type === 'image_url'"
              :src="item.image_url.url"
              alt="图片"
              class="message-image"
            />
          </div>
          <span v-if="message.isStreaming" class="blinking-cursor">|</span>
        </template>
      </div>
    </div>
  </div>

  <!-- 错误消息 -->
  <div v-else-if="message.role === 'error'" class="message error-message">
    <el-alert :title="message.content" type="error" :closable="false" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { ArrowUp, ArrowDown, InfoFilled, Promotion } from '@element-plus/icons-vue';

const props = defineProps({
  message: {
    type: Object,
    required: true,
  },
  modelName: {
    type: String,
    default: '',
  },
});

const showThinking = ref(props.message.showThinking !== false && props.message.thinking);

const hasThinking = computed(() => {
  return props.message.thinking && props.message.thinking.trim().length > 0;
});

const formatContent = (content) => {
  if (!content) return '';
  // 简单的换行处理
  return content.replace(/\n/g, '<br>');
};
</script>

<style scoped>
.message {
  margin-bottom: 16px;
  display: flex;
}

.user-message {
  justify-content: flex-end;
}

.assistant-message {
  justify-content: flex-start;
}

.error-message {
  justify-content: flex-start;
}

.message-content {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 12px;
}

.user-content {
  background: var(--el-color-primary);
  color: white;
  border-radius: 16px 16px 0 16px;
}

.assistant-content {
  background: var(--el-bg-color-page);
  border: 1px solid var(--el-border-color);
  border-radius: 16px 16px 16px 0;
}

.model-name-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.message-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.message-image {
  max-width: 100%;
  border-radius: 4px;
  margin-top: 8px;
}

.thinking-section {
  margin-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color);
  padding-bottom: 8px;
}

.thinking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 4px 0;
}

.thinking-title {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-color-primary);
}

.thinking-content {
  padding: 8px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: pre-wrap;
  margin-top: 8px;
}

.blinking-cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%,
  50% {
    opacity: 1;
  }
  51%,
  100% {
    opacity: 0;
  }
}
</style>

