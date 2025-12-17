<template>
  <div class="chat-area">
    <div v-if="selectedModels.length === 0" class="empty-state">
      <el-empty :description="$t('playground.selectModelFirst', '请先选择模型')" />
    </div>

    <el-row v-else :gutter="16" class="chat-container">
      <el-col
        v-for="(modelId, index) in selectedModels"
        :key="modelId"
        :span="selectedModels.length > 1 ? 24 / selectedModels.length : 24"
      >
        <el-card class="model-card" shadow="hover">
          <template #header>
            <div class="model-header">
              <span class="model-name">{{ getModelName(modelId) }}</span>
              <el-icon v-if="isLoading(modelId)" class="is-loading">
                <Loading />
              </el-icon>
            </div>
          </template>

          <div ref="chatContainerRefs" class="chat-messages" :data-model-id="modelId">
            <el-empty
              v-if="getModelConversation(modelId).length === 0"
              :description="$t('playground.sendFirstMessage', '发送第一条消息')"
              :image-size="80"
            />
            <ChatMessage
              v-for="(message, msgIndex) in getModelConversation(modelId)"
              :key="`${modelId}-${msgIndex}-${message.role}`"
              :message="message"
              :model-name="getModelName(modelId)"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import { Loading } from '@element-plus/icons-vue';
import ChatMessage from './ChatMessage.vue';

const props = defineProps({
  selectedModels: {
    type: Array,
    default: () => [],
  },
  conversations: {
    type: Object,
    default: () => ({}),
  },
  loading: {
    type: Object,
    default: () => ({}),
  },
  getModelName: {
    type: Function,
    required: true,
  },
});

const chatContainerRefs = ref({});

const isLoading = (modelId) => {
  return props.loading[modelId] || false;
};

const getModelConversation = (modelId) => {
  return props.conversations[modelId] || [];
};

const getModelName = (modelId) => {
  return props.getModelName(modelId);
};

// 自动滚动到底部
watch(
  () => props.conversations,
  () => {
    nextTick(() => {
      props.selectedModels.forEach((modelId) => {
        const container = document.querySelector(`[data-model-id="${modelId}"]`);
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    });
  },
  { deep: true },
);
</script>

<style scoped>
.chat-area {
  min-height: 400px;
  max-height: calc(100vh - 400px);
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.chat-container {
  margin: 0;
}

.model-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-name {
  font-weight: 600;
  font-size: 14px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - 350px);
  padding: 16px;
}

.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>

