<template>
  <div class="model-config-settings">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="header-title">{{ $t('models.title', '模型配置') }}</span>
          <div class="header-actions">
            
            <el-button
              type="primary"
              :icon="Plus"
              @click="handleOpenModelDialog"
              
            >
              {{ $t('models.add', '添加模型') }}
            </el-button>
          </div>
        </div>
      </template>

      <el-skeleton v-if="loading" animated :count="3" />
      <el-empty v-else-if="modelConfigList.length === 0" description="暂无模型配置" />

      <div v-else class="model-list">
        <div
          v-for="model in modelConfigList"
          :key="model.id"
          class="model-item"
        >
          <div class="model-info">
            <div class="model-icon">
              <span>{{ getModelIconText(model) }}</span>
            </div>
            <div class="model-details">
              <div class="model-name">
                {{ model.modelName || $t('models.unselectedModel', '未选择模型') }}
              </div>
              <div class="model-provider">
                {{ model.providerName }}
              </div>
            </div>
          </div>

          <div class="model-status">
            <el-tag
              :type="getStatusType(model)"
              :icon="getStatusIcon(model)"
              size="small"
              effect="plain"
            >
              {{ formatEndpoint(model) }}
              <span v-if="needsApiKeyNotice(model)">
                ({{ $t('models.unconfiguredAPIKey', '未配置 API Key') }})
              </span>
            </el-tag>
            <el-tag
              :type="model.type === 'vision' ? 'warning' : 'info'"
              size="small"
              effect="plain"
              style="margin-left: 8px"
            >
              {{ $t(`models.${model.type || 'text'}`, model.type || 'text') }}
            </el-tag>
          </div>

          <div class="model-actions">
            <el-switch
              v-model="model.status"
              :active-value="1"
              :inactive-value="0"
              @change="handleToggleStatus(model)"
              style="margin-right: 8px"
            />
            <!-- per-model quick test button removed -->
            <el-tooltip :content="$t('common.edit', '编辑')" placement="top">
              <el-button
                link
                type="primary"
                :icon="Edit"
                @click="handleOpenModelDialog(model)"
                size="small"
              />
            </el-tooltip>
            <el-tooltip :content="$t('common.delete', '删除')" placement="top">
              <el-button
                link
                type="danger"
                :icon="Delete"
                @click="handleDeleteModel(model.id)"
                :disabled="modelConfigList.length <= 1"
                size="small"
              />
            </el-tooltip>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 模型编辑对话框 -->
    <el-dialog
      v-model="openModelDialog"
      :title="editingModel ? $t('models.edit', '编辑模型') : $t('models.add', '添加模型')"
      width="600px"
      @close="handleCloseModelDialog"
    >
      <el-form :model="modelConfigForm" label-width="120px" label-position="left">
        <!-- 提供商选择 -->
        <el-form-item :label="$t('models.provider', 'AI提供商')" required>
          <el-autocomplete
            v-model="modelConfigForm.providerName"
            :fetch-suggestions="searchProviders"
            :placeholder="$t('models.selectProvider', '选择或输入提供商')"
            value-key="name"
            style="width: 100%"
            @select="onChangeProvider"
            @input="onProviderInput"
          >
            <template #default="{ item }">
              <div style="display: flex; align-items: center; gap: 8px">
                <span>{{ item.name }}</span>
              </div>
            </template>
          </el-autocomplete>
        </el-form-item>

        <!-- 接口地址 -->
        <el-form-item :label="$t('models.endpoint', '接口地址')" required>
          <el-input
            v-model="modelConfigForm.endpoint"
            :placeholder="$t('models.endpointPlaceholder', '例如: https://api.openai.com/v1')"
          />
        </el-form-item>

        <!-- API密钥 -->
        <el-form-item :label="$t('models.apiKey', 'API密钥')">
          <el-input
            v-model="modelConfigForm.apiKey"
            type="password"
            show-password
            :placeholder="$t('models.apiKeyPlaceholder', '例如: sk-...')"
          />
        </el-form-item>

        <!-- 模型名称 -->
        <el-form-item :label="$t('models.modelName', '模型名称')" required>
          <div style="display: flex; gap: 8px; width: 100%">
            <el-autocomplete
              v-model="modelConfigForm.modelName"
              :fetch-suggestions="searchModels"
              :placeholder="$t('models.selectModel', '选择或输入模型名称')"
              value-key="modelName"
              style="flex: 1"
              @select="onModelSelect"
              @input="onModelInput"
            />
            <el-button @click="refreshProviderModels" :loading="refreshing">
              {{ $t('models.refresh', '刷新') }}
            </el-button>
          </div>
        </el-form-item>

        <!-- 模型类型 -->
        <el-form-item :label="$t('models.type', '模型类型')">
          <el-select v-model="modelConfigForm.type" style="width: 100%">
            <el-option :label="$t('models.text', '文本模型')" value="text" />
            <el-option :label="$t('models.vision', '视觉模型')" value="vision" />
          </el-select>
        </el-form-item>

        <!-- Temperature -->
        <el-form-item :label="$t('models.temperature', 'Temperature')">
          <div style="display: flex; align-items: center; gap: 12px; width: 100%">
            <el-slider
              v-model="modelConfigForm.temperature"
              :min="0"
              :max="2"
              :step="0.1"
              show-input
              style="flex: 1"
            />
          </div>
        </el-form-item>

        <!-- Max Tokens -->
        <el-form-item :label="$t('models.maxTokens', 'Max Tokens')">
          <div style="display: flex; align-items: center; gap: 12px; width: 100%">
            <el-slider
              v-model="modelConfigForm.maxTokens"
              :min="1024"
              :max="16384"
              :step="1"
              show-input
              style="flex: 1"
            />
          </div>
        </el-form-item>

        <!-- Top P -->
        <el-form-item :label="$t('models.topP', 'Top P')">
          <div style="display: flex; align-items: center; gap: 12px; width: 100%">
            <el-slider
              v-model="modelConfigForm.topP"
              :min="0"
              :max="1"
              :step="0.1"
              show-input
              style="flex: 1"
            />
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="handleCloseModelDialog">{{ $t('common.cancel', '取消') }}</el-button>
        <el-button
          type="primary"
          @click="handleSaveModel"
          :disabled="!canSave"
          :loading="saving"
        >
          {{ $t('common.save', '保存') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Edit, Delete, Promotion, Check, Warning, ArrowDown } from '@element-plus/icons-vue';
import {
  fetchModelConfigs,
  saveModelConfig,
  updateModelConfig,
  deleteModelConfig,
  fetchProviders,
  fetchGlobalModels,
  syncModels,
  fetchModelsFromProvider,
} from '../../api/model';

const props = defineProps({
  projectId: {
    type: String,
    required: false,
  },
});

const router = useRouter();

const DEFAULT_MODEL_SETTINGS = {
  temperature: 0.7,
  maxTokens: 8192,
  topP: 0.9,
  topK: 0,
};

const MAX_ENDPOINT_DISPLAY = 80;

const loading = ref(true);
const saving = ref(false);
const refreshing = ref(false);
const openModelDialog = ref(false);
const editingModel = ref(null);
const modelConfigList = ref([]);
const providerList = ref([]);
const providerAutocompleteRef = ref(null);
const models = ref([]);
const selectedProvider = ref(null);

const modelConfigForm = reactive({
  id: '',
  providerId: '',
  providerName: '',
  endpoint: '',
  apiKey: '',
  modelId: '',
  modelName: '',
  type: 'text',
  temperature: DEFAULT_MODEL_SETTINGS.temperature,
  maxTokens: DEFAULT_MODEL_SETTINGS.maxTokens,
  topP: DEFAULT_MODEL_SETTINGS.topP,
  topK: DEFAULT_MODEL_SETTINGS.topK,
  status: 1,
});

const canSave = computed(() => {
  return (
    modelConfigForm.providerId &&
    modelConfigForm.providerName &&
    modelConfigForm.endpoint
  );
});

onMounted(() => {
  getProvidersList();
  getModelConfigList();
});

// 获取提供商列表
const getProvidersList = async () => {
  try {
    const data = await fetchProviders();
    const providersData = Array.isArray(data) ? data : data?.data || [];
    providerList.value = Array.isArray(providersData) ? providersData : [];
    if (providerList.value.length > 0) {
      selectedProvider.value = providerList.value[0];
      if (selectedProvider.value?.id) {
        getProviderModels(selectedProvider.value.id);
      }
    }
  } catch (error) {
    console.error('获取提供商列表失败:', error);
  }
};

const openProviderDropdown = () => {
  // focus the autocomplete to trigger suggestions (trigger-on-focus must be true)
  try {
    providerAutocompleteRef.value && providerAutocompleteRef.value.focus && providerAutocompleteRef.value.focus();
  } catch (e) {
    console.error('openProviderDropdown error', e);
  }
};

// 获取提供商的模型列表
const getProviderModels = async (providerId) => {
  try {
    const data = await fetchGlobalModels({ providerId });
    models.value = Array.isArray(data) ? data : data?.data || [];
  } catch (error) {
    console.error('获取模型列表失败:', error);
    models.value = [];
  }
};

// 获取模型配置列表
const getModelConfigList = async () => {
  try {
    loading.value = true;
    const response = await fetchModelConfigs();
    const responseData = response?.data || response;
    const configList = responseData?.data || responseData || [];
    
    // 规范化字段
    modelConfigList.value = Array.isArray(configList)
      ? configList.map((item) => ({
          ...item,
          id: item.id,
          providerId: item.providerId || item.provider_id,
          providerName: item.providerName || item.provider_name,
          endpoint: item.endpoint,
          apiKey: item.apiKey || item.api_key,
          modelId: item.modelId || item.model_id,
          modelName: item.modelName || item.model_name,
          type: item.type,
          temperature: item.temperature,
          maxTokens: item.maxTokens || item.max_tokens,
          topP: item.topP || item.top_p,
          topK: item.topK || item.top_k,
          status: item.status,
        }))
      : [];
  } catch (error) {
    console.error('获取模型配置列表失败:', error);
    ElMessage.error('获取模型配置列表失败');
  } finally {
    loading.value = false;
  }
};

// 格式化端点显示
const formatEndpoint = (model) => {
  if (!model?.endpoint) return '';
  const base = model.endpoint.replace(/^https?:\/\//, '');
  if (base.length > MAX_ENDPOINT_DISPLAY) {
    return base.slice(0, MAX_ENDPOINT_DISPLAY) + '…';
  }
  return base;
};

// 获取模型状态
const getStatusType = (model) => {
  const providerId = (model?.providerId || '').toString().toLowerCase();
  const hasApiKey = model?.apiKey;
  if (providerId === 'ollama') {
    return 'success';
  } else if (hasApiKey) {
    return 'success';
  }
  return 'warning';
};

const getStatusIcon = (model) => {
  const providerId = (model?.providerId || '').toString().toLowerCase();
  const hasApiKey = model?.apiKey;
  if (providerId === 'ollama' || hasApiKey) {
    return Check;
  }
  return Warning;
};

const needsApiKeyNotice = (model) => {
  const providerId = (model?.providerId || '').toString().toLowerCase();
  return providerId !== 'ollama' && !model?.apiKey;
};

const getModelIconText = (model) => {
  return model.modelName?.[0]?.toUpperCase() || model.providerName?.[0]?.toUpperCase() || 'M';
};

// 提供商搜索
const searchProviders = (queryString, cb) => {
  const results = queryString
    ? providerList.value.filter((p) =>
        p.name.toLowerCase().includes(queryString.toLowerCase())
      )
    : providerList.value;
  cb(results.map((p) => ({ ...p, value: p.name })));
};

// 提供商输入变化
const onProviderInput = (value) => {
  if (typeof value === 'string') {
    modelConfigForm.providerId = 'custom';
    modelConfigForm.providerName = value;
    modelConfigForm.endpoint = '';
  }
};

// 提供商选择
const onChangeProvider = (item) => {
  if (item && item.id) {
    const provider = providerList.value.find((p) => p.id === item.id);
    if (provider) {
      selectedProvider.value = provider;
      modelConfigForm.providerId = provider.id;
      modelConfigForm.providerName = provider.name;
      modelConfigForm.endpoint = provider.apiUrl || provider.defaultEndpoint || '';
      modelConfigForm.modelName = '';
      getProviderModels(provider.id);
    }
  }
};

// 模型搜索
const searchModels = (queryString, cb) => {
  const safeModels = Array.isArray(models.value) ? models.value : [];
  const results = queryString
    ? safeModels.filter((m) =>
        m.modelName?.toLowerCase().includes(queryString.toLowerCase())
      )
    : safeModels;
  cb(results.map((m) => ({ ...m, value: m.modelName })));
};

// 模型输入变化
const onModelInput = (value) => {
  if (typeof value === 'string') {
    modelConfigForm.modelName = value;
    modelConfigForm.modelId = value;
  }
};

// 模型选择
const onModelSelect = (item) => {
  if (item) {
    modelConfigForm.modelName = item.modelName;
    modelConfigForm.modelId = item.modelId || item.modelName;
  }
};

// 刷新提供商模型
const refreshProviderModels = async () => {
  if (!modelConfigForm.endpoint) {
    ElMessage.warning('请先填写接口地址');
    return;
  }
  try {
    refreshing.value = true;
    const data = await fetchModelsFromProvider({
      endpoint: modelConfigForm.endpoint,
      providerId: modelConfigForm.providerId,
      apiKey: modelConfigForm.apiKey,
    });
    if (data && data.length > 0) {
      models.value = data;
      await syncModels({
        newModels: data,
        providerId: modelConfigForm.providerId,
      });
      ElMessage.success('刷新成功');
    } else {
      ElMessage.info('没有需要刷新的模型');
    }
  } catch (error) {
    console.error('刷新模型失败:', error);
    if (error.response?.status === 401) {
      ElMessage.error('API Key 无效');
    } else {
      ElMessage.error('获取模型列表失败');
    }
  } finally {
    refreshing.value = false;
  }
};

// 打开模型对话框
const handleOpenModelDialog = (model = null) => {
  if (model) {
    editingModel.value = model;
    Object.assign(modelConfigForm, {
      ...model,
      temperature: model.temperature !== undefined ? model.temperature : DEFAULT_MODEL_SETTINGS.temperature,
      maxTokens: model.maxTokens !== undefined ? model.maxTokens : DEFAULT_MODEL_SETTINGS.maxTokens,
      topP: model.topP !== undefined && model.topP !== 0 ? model.topP : DEFAULT_MODEL_SETTINGS.topP,
    });
    getProviderModels(model.providerId);
  } else {
    editingModel.value = null;
    Object.assign(modelConfigForm, {
      id: '',
      providerId: '',
      providerName: '',
      endpoint: '',
      apiKey: '',
      modelId: '',
      modelName: '',
      type: 'text',
      ...DEFAULT_MODEL_SETTINGS,
      status: 1,
    });
  }
  openModelDialog.value = true;
};

// 关闭模型对话框
const handleCloseModelDialog = () => {
  openModelDialog.value = false;
  editingModel.value = null;
  // 清空表单，确保下次“添加模型”不会残留上次编辑的数据
  Object.assign(modelConfigForm, {
    id: '',
    providerId: '',
    providerName: '',
    endpoint: '',
    apiKey: '',
    modelId: '',
    modelName: '',
    type: 'text',
    ...DEFAULT_MODEL_SETTINGS,
    status: 1,
  });
  // 清空临时模型列表和选择的 provider
  models.value = [];
  selectedProvider.value = null;
};

// 保存模型
const handleSaveModel = async () => {
  try {
    saving.value = true;
    const payload = {
      providerId: modelConfigForm.providerId,
      providerName: modelConfigForm.providerName || '',
      endpoint: modelConfigForm.endpoint,
      apiKey: modelConfigForm.apiKey,
      modelId: modelConfigForm.modelId || modelConfigForm.modelName,
      modelName: modelConfigForm.modelName,
      type: modelConfigForm.type || 'text',
      temperature: modelConfigForm.temperature ?? 0.7,
      maxTokens: modelConfigForm.maxTokens ?? 8192,
      topP: modelConfigForm.topP ?? 0.9,
      topK: modelConfigForm.topK ?? 0,
      status: modelConfigForm.status ?? 1,
    };
    // 如果是编辑已有配置，调用更新接口；否则新建
    if (editingModel.value && editingModel.value.id) {
      await updateModelConfig(editingModel.value.id, payload);
    } else if (modelConfigForm.id) {
      await updateModelConfig(modelConfigForm.id, payload);
    } else {
      await saveModelConfig(payload);
    }
    ElMessage.success('保存成功');
    getModelConfigList();
    handleCloseModelDialog();
  } catch (error) {
    console.error('保存模型失败:', error);
    ElMessage.error('保存失败');
  } finally {
    saving.value = false;
  }
};

// 删除模型
const handleDeleteModel = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个模型配置吗？', '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    });
    await deleteModelConfig(id);
    ElMessage.success('删除成功');
    getModelConfigList();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除模型失败:', error);
      ElMessage.error('删除失败');
    }
  }
};

// 切换模型状态
const handleToggleStatus = async (model) => {
  try {
    const payload = {
      providerId: model.providerId,
      providerName: model.providerName,
      endpoint: model.endpoint,
      apiKey: model.apiKey,
      modelId: model.modelId,
      modelName: model.modelName,
      type: model.type,
      temperature: model.temperature,
      maxTokens: model.maxTokens,
      topP: model.topP,
      topK: model.topK,
      status: model.status,
    };
    // 更新已存在的配置，否则创建
    if (model.id) {
      await updateModelConfig(model.id, payload);
    } else {
      await saveModelConfig(payload);
    }
    ElMessage.success(model.status === 1 ? '模型已启用' : '模型已禁用');
    getModelConfigList();
  } catch (error) {
    console.error('切换模型状态失败:', error);
    ElMessage.error('操作失败');
    // 恢复原状态
    model.status = model.status === 1 ? 0 : 1;
  }
};

// 跳转到模型测试
const goToPlayground = () => {
  // 导航到模型管理页的测试 tab
  router.push({ path: '/model-management', query: { tab: 'play' } });
};

// per-model navigation removed
</script>

<style scoped>
.model-config-settings {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.model-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  transition: all 0.2s;
}

.model-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.model-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.model-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--el-color-primary-light-9);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.model-details {
  flex: 1;
  min-width: 0;
}

.model-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.model-provider {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  background: var(--el-color-primary-light-9);
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
}

.model-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 16px;
}

.model-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
</style>

