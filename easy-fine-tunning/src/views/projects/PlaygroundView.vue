<template>
  <div class="playground-view">
    <h2 class="page-title">{{ $t('playground.title', '模型测试') }}</h2>

    <el-alert v-if="error" :title="error" type="error" :closable="false" style="margin-bottom: 16px" />

    <el-card class="playground-card">
      <PlaygroundHeader
        :available-models="availableModels"
        :selected-models="selectedModels"
        :conversations="conversations"
        :output-mode="outputMode"
        @model-selection="handleModelSelection"
        @clear-conversations="handleClearConversations"
        @output-mode-change="handleOutputModeChange"
      />

      <el-divider />

      <ChatArea
        :selected-models="selectedModels"
        :conversations="conversations"
        :loading="loading"
        :get-model-name="getModelName"
      />

      <el-divider />

      <MessageInput
        :user-input="userInput"
        :loading="loading"
        :selected-models="selectedModels"
        :uploaded-image="uploadedImage"
        :available-models="availableModels"
        @input-change="handleInputChange"
        @send-message="handleSendMessage"
        @image-upload="handleImageUpload"
        @remove-image="handleRemoveImage"
      />
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useModelPlayground } from '../../composables/useModelPlayground';
import { useModelStore } from '../../stores/model';
import PlaygroundHeader from '../../components/playground/PlaygroundHeader.vue';
import ChatArea from '../../components/playground/ChatArea.vue';
import MessageInput from '../../components/playground/MessageInput.vue';

const route = useRoute();
const projectId = route.params.projectId;
const modelId = route.query.modelId || null;

const modelStore = useModelStore();

// 确保模型配置已加载
onMounted(async () => {
  if (modelStore.modelConfigList.length === 0) {
    await modelStore.loadModelConfigs(projectId);
  }
});

const {
  availableModels,
  selectedModels,
  loading,
  userInput,
  conversations,
  error,
  outputMode,
  uploadedImage,
  handleModelSelection,
  handleInputChange,
  handleImageUpload,
  handleRemoveImage,
  handleSendMessage,
  handleClearConversations,
  handleOutputModeChange,
  getModelName,
} = useModelPlayground(projectId, modelId);
</script>

<style scoped>
.playground-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  margin: 0 0 20px 0;
  font-size: 24px;
  font-weight: 600;
}

.playground-card {
  border-radius: 12px;
}
</style>
