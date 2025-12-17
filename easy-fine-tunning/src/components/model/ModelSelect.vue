<template>
  <div class="model-select-wrapper" @mouseenter="isHovered = true" @mouseleave="handleMouseLeave">
    <!-- 默认显示的图标按钮 -->
    <el-tooltip
      v-if="!shouldShowFullSelect"
      :content="selectedModelName || $t('playground.selectModelFirst', '请先选择模型')"
      placement="bottom"
    >
      <el-button
        :class="{ 'error-state': error }"
        circle
        :size="size"
        :icon="currentModelIcon ? undefined : SmartToy"
      >
        <img v-if="currentModelIcon" :src="currentModelIcon" :alt="selectedModelName" @error="handleImageError" />
      </el-button>
    </el-tooltip>

    <!-- 悬浮时显示的完整 Select -->
    <el-select
      v-model="selectedModel"
      :size="size"
      :placeholder="error ? $t('models.pleaseSelectModel', '请选择模型') : $t('playground.selectModelFirst', '请先选择模型')"
      :class="{ 'full-select': shouldShowFullSelect, 'hidden-select': !shouldShowFullSelect }"
      @change="handleModelChange"
      @blur="validateModel"
      @visible-change="handleVisibleChange"
    >
      <el-option :value="" disabled>
        {{ error ? $t('models.pleaseSelectModel', '请选择模型') : $t('playground.selectModelFirst', '请先选择模型') }}
      </el-option>
      <template v-for="provider in groupedProviders" :key="provider.name">
        <el-option-group :label="provider.name || 'Other'">
          <el-option
            v-for="model in provider.models"
            :key="model.id"
            :value="model.id"
            :label="model.modelName"
          >
            <div class="model-option">
              <img
                :src="getModelIcon(model.modelName)"
                :alt="model.modelName"
                @error="handleImageError"
                class="model-icon"
              />
              <span>{{ model.modelName }}</span>
            </div>
          </el-option>
        </el-option-group>
      </template>
    </el-select>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { SmartToy } from '@element-plus/icons-vue';
import { useModelStore } from '../../stores/model';
import { updateProject } from '../../api/project';

const props = defineProps({
  projectId: {
    type: String,
    required: true,
  },
  size: {
    type: String,
    default: 'small',
  },
  required: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['error']);

const modelStore = useModelStore();
const isHovered = ref(false);
const isOpen = ref(false);
const error = ref(false);
const selectedModel = ref('');

const shouldShowFullSelect = computed(() => isHovered.value || isOpen.value);

const selectedModelName = computed(() => {
  const model = modelStore.modelConfigList.find((m) => m.id === selectedModel.value);
  return model?.modelName || '';
});

const currentModelIcon = computed(() => {
  const model = modelStore.modelConfigList.find((m) => m.id === selectedModel.value);
  return model ? getModelIcon(model.modelName) : null;
});

// 按提供商分组模型（只显示已配置且激活的模型）
const groupedProviders = computed(() => {
  const filteredModels = modelStore.modelConfigList.filter((m) => {
    // 检查模型是否激活
    if (m.status !== 1) {
      return false;
    }
    
    // 检查模型名称和 endpoint
    if (!m.modelName || !m.endpoint) {
      return false;
    }
    
    // Ollama 提供商只需要 endpoint，其他提供商需要 apiKey
    if (m.providerId?.toLowerCase() === 'ollama') {
      return true;
    } else {
      return !!(m.apiKey && m.apiKey.trim().length > 0);
    }
  });

  const providers = [...new Set(filteredModels.map((m) => m.providerName || 'Other'))];
  return providers.map((provider) => ({
    name: provider,
    models: filteredModels.filter((m) => (m.providerName || 'Other') === provider),
  }));
});

// 获取模型图标
const getModelIcon = (modelName) => {
  if (!modelName) return '/imgs/models/default.svg';
  const lowerModelName = modelName.toLowerCase();
  const modelPrefixes = [
    { prefix: 'doubao', icon: 'doubao.svg' },
    { prefix: 'qwen', icon: 'qwen.svg' },
    { prefix: 'gpt', icon: 'gpt.svg' },
    { prefix: 'gemini', icon: 'gemini.svg' },
    { prefix: 'claude', icon: 'claude.svg' },
    { prefix: 'llama', icon: 'llama.svg' },
    { prefix: 'mistral', icon: 'mistral.svg' },
    { prefix: 'yi', icon: 'yi.svg' },
    { prefix: 'deepseek', icon: 'deepseek.svg' },
    { prefix: 'chatglm', icon: 'chatglm.svg' },
    { prefix: 'wenxin', icon: 'wenxin.svg' },
    { prefix: 'glm', icon: 'glm.svg' },
    { prefix: 'hunyuan', icon: 'hunyuan.svg' },
  ];
  const matchedPrefix = modelPrefixes.find(({ prefix }) => lowerModelName.includes(prefix));
  return `/imgs/models/${matchedPrefix ? matchedPrefix.icon : 'default.svg'}`;
};

const handleImageError = (e) => {
  e.target.src = '/imgs/models/default.svg';
};

const handleMouseLeave = () => {
  if (!isOpen.value) {
    isHovered.value = false;
  }
};

const handleVisibleChange = (visible) => {
  isOpen.value = visible;
  if (!visible) {
    setTimeout(() => {
      if (!isHovered.value) {
        isHovered.value = false;
      }
    }, 200);
  }
};

const handleModelChange = async (modelId) => {
  if (!modelId) return;

  if (error.value) {
    error.value = false;
    emit('error', false);
  }

  const selectedModelObj = modelStore.modelConfigList.find((m) => m.id === modelId);
  if (selectedModelObj) {
    selectedModel.value = modelId;
    modelStore.setSelectedModel(selectedModelObj);
    await updateDefaultModel(modelId);
  }

  setTimeout(() => {
    isHovered.value = false;
    isOpen.value = false;
  }, 200);
};

const updateDefaultModel = async (modelId) => {
  if (!props.projectId || !modelId) {
    ElMessage.error('项目ID或模型ID缺失');
    return;
  }

  try {
    await updateProject(props.projectId, { default_model_config_id: modelId });
    ElMessage.success('默认模型配置已更新');
  } catch (error) {
    console.error('更新默认模型配置失败:', error);
    ElMessage.error(`更新默认模型配置失败: ${error.message || '未知错误'}`);
  }
};

const validateModel = () => {
  if (props.required && (!selectedModel.value || selectedModel.value === '')) {
    error.value = true;
    emit('error', true);
    return false;
  }
  return true;
};

// 监听选中的模型信息变化
watch(
  () => modelStore.selectedModelInfo,
  (newModel) => {
    if (newModel && newModel.id) {
      selectedModel.value = newModel.id;
    } else {
      selectedModel.value = '';
    }
  },
  { immediate: true },
);

// 初始化选中模型
onMounted(() => {
  if (modelStore.selectedModelInfo?.id) {
    selectedModel.value = modelStore.selectedModelInfo.id;
  } else if (modelStore.modelConfigList.length > 0 && modelStore.modelConfigList[0]?.id) {
    selectedModel.value = modelStore.modelConfigList[0].id;
    modelStore.setSelectedModel(modelStore.modelConfigList[0]);
  }
});
</script>

<style scoped>
.model-select-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.full-select {
  min-width: 200px;
  opacity: 1;
  width: auto;
}

.hidden-select {
  min-width: 0;
  opacity: 0;
  width: 0;
  position: absolute;
  pointer-events: none;
}

.model-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
  flex-shrink: 0;
}

.error-state {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>

