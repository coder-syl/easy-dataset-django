<template>
  <el-container class="app-shell">
    <el-header :class="['app-header', { 'is-dark': isDark }]" height="56px">
      <div class="brand">Easy-Fine-Tunning</div>
      <TopNavigation :project-id="projectId" />
      <div class="header-actions">
        <!-- 项目上下文存在时显示模型选择器和任务图标（包括带 projectId 的全局页面） -->
        <template v-if="projectId">
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
          <TaskIcon :project-id="projectId" />
        </template>
 
        <!-- 跳转到模型管理页面 -->
        <el-select
          v-model="selectedProjectId"
          size="small"
          class="project-select"
          @change="handleProjectSwitch"
          filterable
          placeholder="选择项目"
          style="min-width: 160px; margin-right: 8px"
        >
          <el-option
            v-for="p in projects"
            :key="p.id"
            :label="p.name"
            :value="p.id"
          />
        </el-select>

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
import { updateProject, fetchProjectDetail } from '../api/project';
import { ElMessage } from 'element-plus';
import { Cpu } from '@element-plus/icons-vue';
import { House } from '@element-plus/icons-vue';
import { fetchProjects } from '../api/project';
import TopNavigation from '../components/TopNavigation.vue';
import TaskIcon from '../components/tasks/TaskIcon.vue';

const { locale, t } = useI18n();
const appStore = useAppStore();
const modelStore = useModelStore();
const route = useRoute();
const router = useRouter();
appStore.loadPrefs();

const selectedModelId = ref('');
  const projects = ref([]);
  const selectedProjectId = ref(null);

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
  // 优先从路由 params 获取（项目详情页），否则尝试从 query 中读取 projectId（当从项目页面导航到全局页时会带上 query）
  return route.params.projectId || route.query.projectId || null;
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

// 处理项目切换：导航到项目页并设置该项目的默认模型（若存在）
const handleProjectSwitch = async (projectIdVal) => {
  if (!projectIdVal) return;
  // 导航到项目概览页
  await router.push({ name: 'project-overview', params: { projectId: projectIdVal } });

  try {
    // 重新加载全局模型配置列表（store）
    await modelStore.loadModelConfigs();

    // 获取项目详情以找到默认模型 id
    const projectResp = await fetchProjectDetail(projectIdVal);
    const projectData = projectResp?.data || projectResp;
    const defaultModelId = projectData?.default_model_config_id || projectData?.defaultModelConfigId || null;

    if (defaultModelId) {
      // 尝试在 modelStore 中查找该模型并设置为选中
      const found = modelStore.modelConfigList.find((m) => String(m.id) === String(defaultModelId));
      if (found) {
        modelStore.setSelectedModel(found);
      }
    } else {
      // 如果没有默认模型，保持现有行为：选第一个或清空
      if (modelStore.modelConfigList.length > 0) {
        modelStore.setSelectedModel(modelStore.modelConfigList[0]);
      } else {
        modelStore.setSelectedModel(null);
      }
    }
  } catch (e) {
    console.error('切换项目并设置默认模型失败', e);
  }
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
      // 如果 store 中还没有模型配置列表，则加载（改为由 store 自行处理 projectId 提取）
      // 这样可以避免重复加载（路由守卫可能已经加载过了）
      if (modelStore.modelConfigList.length === 0) {
        console.log('[MainLayout] 加载模型配置，项目ID:', newProjectId);
        await modelStore.loadModelConfigs();
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
    // 如果 store 中还没有模型配置列表，则加载（store 会自动从 URL 中提取 projectId）
    // 这样可以避免重复加载（路由守卫可能已经加载过了）
    if (modelStore.modelConfigList.length === 0) {
      console.log('[MainLayout] onMounted 加载模型配置，项目ID:', projectId.value);
      await modelStore.loadModelConfigs();
    }
    // 设置选中的模型ID（从数据库加载的默认模型）
    const selectedModel = modelStore.selectedModelInfo;
    console.log('[MainLayout] onMounted 后的选中模型:', selectedModel);
    selectedModelId.value = selectedModel?.id || '';
    console.log('[MainLayout] onMounted 设置 selectedModelId:', selectedModelId.value);
  }
  // 加载项目列表供右上角切换使用
  try {
    const data = await fetchProjects();
    const list = Array.isArray(data) ? data : data?.records || data?.data || [];
    projects.value = list;
    // 初始化选中的项目id为 route 的 projectId 或第一个项目
    selectedProjectId.value = projectId.value || (list[0] && list[0].id) || null;
  } catch (e) {
    projects.value = [];
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
