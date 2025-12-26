<template>
  <div class="model-management-view">
    <el-card>
      <template #header>
        <div style="display:flex; align-items:center; justify-content:space-between">
          <div>
            <h2 style="margin:0">{{ $t('modelManagement.title') }}</h2>
            <p style="margin:4px 0 0; color: #6b7280">{{ $t('modelManagement.description') }}</p>
          </div>
        </div>
      </template>

    <el-tabs v-model="activeTab" style="margin-top: 12px">
        <el-tab-pane label="模型配置" name="config">
          <ModelConfigSettings />
        </el-tab-pane>
        <el-tab-pane label="模型测试" name="play">
          <div style="padding: 12px">
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
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import ModelConfigSettings from '../components/model/ModelConfigSettings.vue';
import PlaygroundHeader from '../components/playground/PlaygroundHeader.vue';
import ChatArea from '../components/playground/ChatArea.vue';
import MessageInput from '../components/playground/MessageInput.vue';
import { useModelPlayground } from '../composables/useModelPlayground';
import { useModelStore } from '../stores/model';

const route = useRoute();
const activeTab = ref(route.query.tab || 'config');
const router = useRouter();

// 路由变化时同步 tab 与 modelId
watch(
  () => route.query.tab,
  (newTab) => {
    activeTab.value = newTab || 'config';
  }
);

watch(
  () => route.query.modelId,
  (newModelId) => {
    if (newModelId && selectedModels) {
      selectedModels.value = [newModelId];
    }
  }
);
const modelStore = useModelStore();

// 初始化时确保模型配置已加载（全局）
onMounted(async () => {
  if (modelStore.modelConfigList.length === 0) {
    await modelStore.loadModelConfigs();
  }
});

// 使用无项目上下文的 playground（传入 null）
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
} = useModelPlayground(null, null);

const goToProjectPlayground = () => {
  router.push('/projects');
};
</script>

<style scoped>
.model-management-view {
  padding: 20px;
}
</style>

