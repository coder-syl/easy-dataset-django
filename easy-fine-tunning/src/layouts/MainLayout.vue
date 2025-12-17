<template>
  <el-container class="app-shell">
    <el-header :class="['app-header', { 'is-dark': isDark }]" height="56px">
      <div class="brand">Easy Dataset</div>
      <TopNavigation v-if="isProjectDetail" :project-id="projectId" />
      <div class="header-actions">
        <!-- 项目详情页：显示模型选择器 -->
        <template v-if="isProjectDetail && projectId">
          <el-select
            v-model="selectedModelId"
            :placeholder="$t('playground.selectModelFirst', '请先选择模型')"
            size="small"
            class="header-model-select"
            @change="handleModelChange"
            filterable
            :teleported="false"
          >
            <el-option-group
              v-for="group in groupedModels"
              :key="group.providerName"
              :label="group.providerName"
            >
              <el-option
                v-for="model in group.models"
                :key="model.id"
                :label="model.modelName"
                :value="model.id"
              >
                <div class="model-option">
                  <img
                    :src="getModelIcon(model.modelName)"
                    :alt="model.modelName"
                    @error="onImageError"
                    class="model-icon"
                  />
                  <span>{{ model.modelName }}</span>
                </div>
              </el-option>
            </el-option-group>
          </el-select>
        </template>
        <!-- 非项目详情页：显示模型管理按钮 -->
        <el-button
          v-else
          :type="isModelManagement ? 'primary' : 'default'"
          class="global-menu-btn"
          @click="navigateToModelManagement"
        >
          <el-icon><Cpu /></el-icon>
          <span>{{ $t('modelManagement.title') }}</span>
        </el-button>
        <el-select
          v-model="localeValue"
          size="small"
          class="lang-select"
          @change="changeLocale"
        >
          <el-option label="中文" value="zh" />
          <el-option label="English" value="en" />
        </el-select>
        <el-switch
          v-model="isDark"
          size="small"
          inline-prompt
          :active-text="$t('common.dark')"
          :inactive-text="$t('common.light')"
        />
      </div>
    </el-header>
    <el-main class="app-main">
      <slot />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed, watch, ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { useAppStore } from '../stores/app';
import { useModelStore } from '../stores/model';
import { updateProject } from '../api/project';
import { ElMessage } from 'element-plus';
import { Cpu } from '@element-plus/icons-vue';
import TopNavigation from '../components/TopNavigation.vue';

const { locale, t } = useI18n();
const appStore = useAppStore();
const modelStore = useModelStore();
const route = useRoute();
const router = useRouter();
appStore.loadPrefs();

const selectedModelId = ref('');

// 获取模型图标
const getModelIcon = (modelName) => {
  if (!modelName) return '/imgs/models/default.svg';
  const lowerModelName = modelName.toLowerCase();
  if (lowerModelName.includes('gpt')) return '/imgs/models/gpt.svg';
  if (lowerModelName.includes('doubao')) return '/imgs/models/doubao.svg';
  if (lowerModelName.includes('qwen')) return '/imgs/models/qwen.svg';
  if (lowerModelName.includes('gemini')) return '/imgs/models/gemini.svg';
  if (lowerModelName.includes('claude')) return '/imgs/models/claude.svg';
  if (lowerModelName.includes('llama')) return '/imgs/models/llama.svg';
  if (lowerModelName.includes('mistral')) return '/imgs/models/mistral.svg';
  if (lowerModelName.includes('yi')) return '/imgs/models/yi.svg';
  if (lowerModelName.includes('deepseek')) return '/imgs/models/deepseek.svg';
  if (lowerModelName.includes('chatglm') || lowerModelName.includes('glm')) return '/imgs/models/glm.svg';
  if (lowerModelName.includes('wenxin')) return '/imgs/models/wenxin.svg';
  if (lowerModelName.includes('hunyuan')) return '/imgs/models/hunyuan.svg';
  return '/imgs/models/default.svg';
};

const onImageError = (e) => {
  const target = e.target;
  const currentSrc = target.src || target.getAttribute('src') || '';
  
  // 如果已经是默认图标，不再处理，避免无限循环
  if (currentSrc.includes('default.svg')) {
    // 隐藏图片，避免显示破损图标
    target.style.display = 'none';
    return;
  }
  
  // 只在开发模式下输出警告
  if (import.meta.env.DEV) {
    console.warn('Model icon load failed, using default:', currentSrc);
  }
  
  // 设置默认图标，并移除错误处理器避免循环
  target.onerror = null;
  target.src = '/imgs/models/default.svg';
};

// 按提供商分组模型（只显示已配置且激活的模型）
const groupedModels = computed(() => {
  const groups = {};
  
  // 过滤模型：只显示已配置且激活的模型
  const filteredModels = (modelStore.modelConfigList || []).filter((m) => {
    // 检查模型是否激活
    if (m.status !== 1) {
      return false;
    }
    
    // 检查模型名称和 endpoint
    if (!m.modelName || !m.endpoint) {
      return false;
    }
    
    // Ollama 提供商只需要 endpoint，其他提供商需要 apiKey
    const providerId = (m.providerId || '').toString().toLowerCase();
    if (providerId === 'ollama') {
      return true; // Ollama 只需要 endpoint
    } else {
      return !!(m.apiKey && m.apiKey.trim().length > 0); // 其他提供商需要 apiKey
    }
  });
  
  // 按提供商分组
  filteredModels.forEach((model) => {
    const providerName = model.providerName || 'Other';
    if (!groups[providerName]) {
      groups[providerName] = { providerName, models: [] };
    }
    groups[providerName].models.push(model);
  });
  
  return Object.values(groups);
});

// 处理模型选择
const handleModelChange = async (modelId) => {
  if (!modelId || !projectId.value) return;
  
  try {
    await updateProject(projectId.value, { default_model_config_id: modelId });
    
    // 更新 store 中的选中模型
    const selectedModel = modelStore.modelConfigList.find((m) => m.id === modelId);
    if (selectedModel) {
      modelStore.setSelectedModel(selectedModel);
    }
    
    ElMessage.success(t('models.saveSuccess', '默认模型配置已更新'));
  } catch (error) {
    console.error('更新默认模型配置失败:', error);
    ElMessage.error(t('models.saveFailed', '更新默认模型配置失败'));
  }
};

const isDark = computed({
  get: () => appStore.isDark,
  set: (val) => appStore.setDark(val),
});

const localeValue = computed({
  get: () => appStore.locale,
  set: (val) => appStore.setLocale(val),
});

const isProjectDetail = computed(() => {
  return route.path.startsWith('/projects/') && route.path.split('/').length > 2;
});

const projectId = computed(() => {
  if (isProjectDetail.value) {
    return route.params.projectId;
  }
  return null;
});

const isModelManagement = computed(() => {
  return route.path === '/model-management';
});

const navigateToModelManagement = () => {
  router.push('/model-management');
};

const changeLocale = (val) => {
  locale.value = val;
};

watch(
  () => appStore.locale,
  (val) => {
    locale.value = val;
  },
  { immediate: true },
);

watch(
  () => appStore.isDark,
  () => {
    appStore.applyTheme();
  },
  { immediate: true },
);

// 监听项目变化，加载模型配置
watch(
  () => projectId.value,
  async (newProjectId) => {
    if (newProjectId) {
      // 如果 store 中还没有模型配置列表，则加载
      // 这样可以避免重复加载（路由守卫可能已经加载过了）
      if (modelStore.modelConfigList.length === 0) {
        console.log('[MainLayout] 加载模型配置，项目ID:', newProjectId);
        await modelStore.loadModelConfigs(newProjectId);
      }
      // 设置选中的模型ID（从数据库加载的默认模型）
      const selectedModel = modelStore.selectedModelInfo;
      console.log('[MainLayout] 项目变化后的选中模型:', selectedModel);
      selectedModelId.value = selectedModel?.id || '';
      console.log('[MainLayout] 设置 selectedModelId:', selectedModelId.value);
    } else {
      selectedModelId.value = '';
    }
  },
  { immediate: true },
);

// 监听选中模型信息变化
watch(
  () => modelStore.selectedModelInfo,
  (newModel) => {
    console.log('[MainLayout] selectedModelInfo 变化:', newModel);
    if (newModel && newModel.id) {
      selectedModelId.value = newModel.id;
      console.log('[MainLayout] 设置 selectedModelId:', newModel.id);
    } else {
      selectedModelId.value = '';
      console.log('[MainLayout] 清空 selectedModelId');
    }
  },
  { immediate: true },
);

// 初始化时加载模型配置（如果路由守卫还没有加载）
onMounted(async () => {
  if (projectId.value) {
    // 如果 store 中还没有模型配置列表，则加载
    // 这样可以避免重复加载（路由守卫可能已经加载过了）
    if (modelStore.modelConfigList.length === 0) {
      console.log('[MainLayout] onMounted 加载模型配置，项目ID:', projectId.value);
      await modelStore.loadModelConfigs(projectId.value);
    }
    // 设置选中的模型ID（从数据库加载的默认模型）
    const selectedModel = modelStore.selectedModelInfo;
    console.log('[MainLayout] onMounted 后的选中模型:', selectedModel);
    selectedModelId.value = selectedModel?.id || '';
    console.log('[MainLayout] onMounted 设置 selectedModelId:', selectedModelId.value);
  }
});
</script>

<style scoped>
.app-shell {
  height: 100vh;
}
.app-header {
  --nav-text: #0f172a;
  --nav-text-hover: #2563eb;
  --nav-text-active: #1d4ed8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid #e5e7eb;
  gap: 12px;
  position: relative;
  background: linear-gradient(135deg, #e6efff, #f4f6fb);
  color: var(--nav-text);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
}
.app-header.is-dark {
  --nav-text: #e5e7eb;
  --nav-text-hover: #93c5fd;
  --nav-text-active: #60a5fa;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: linear-gradient(135deg, #0f172a, #1e293b);
  color: #e5e7eb;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.22);
}
.brand {
  font-weight: 600;
  font-size: 16px;
  color: inherit;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.lang-select {
  width: 120px;
}
.header-model-select {
  min-width: 200px;
  max-width: 300px;
}

/* 使用深度选择器确保样式应用到 el-option 内部 */
:deep(.el-select-dropdown__item) {
  padding: 8px 12px;
  height: auto;
  line-height: normal;
}

:deep(.el-select-dropdown__item) .model-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.el-select-dropdown__item) .model-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
  flex-shrink: 0;
}
.global-menu-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  color: #0f172a;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
  transition: all 0.2s ease;
  font-weight: 500;
}
.app-header.is-dark .global-menu-btn {
  background: rgba(255, 255, 255, 0.12);
  color: #e5e7eb;
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
}
.global-menu-btn:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
  background: #ffffff;
}
.app-header.is-dark .global-menu-btn:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 0.16);
}
.global-menu-btn.active {
  background: #3b82f6;
  color: #ffffff;
  border-color: #60a5fa;
}
.app-main {
  padding: 16px;
  background-color: var(--el-bg-color-page);
}
</style>
