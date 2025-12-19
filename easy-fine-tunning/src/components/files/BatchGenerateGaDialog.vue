<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('gaPairs.batchGenerate', '批量生成GA对')"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-loading="generating">
      <el-alert
        v-if="genError"
        :title="genError"
        type="error"
        :closable="true"
        @close="genError = null"
        style="margin-bottom: 16px"
      />
      <el-alert
        v-if="genResult"
        :title="$t('gaPairs.batchGenCompleted', { success: genResult.success, total: genResult.total }, `成功生成 ${genResult.success}/${genResult.total} 个文件的GA对`)"
        type="success"
        :closable="true"
        @close="genResult = null"
        style="margin-bottom: 16px"
      />

      <div v-if="!genResult">
        <p>{{ $t('gaPairs.batchGenerateDescription', { count: fileIds.length }, `将为 ${fileIds.length} 个文件生成GA对`) }}</p>

        <!-- 追加模式选择 -->
        <el-form-item :label="$t('gaPairs.appendMode', '追加模式')" style="margin-top: 16px">
          <el-switch v-model="appendMode" />
          <div class="el-form-item__help">
            {{ $t('gaPairs.appendModeDescription', '追加模式：如果文件已有GA对，将追加新的GA对而不是覆盖') }}
          </div>
        </el-form-item>

        <!-- 模型信息 -->
        <div v-if="loadingModel" style="margin-top: 16px">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>{{ $t('gaPairs.loadingProjectModel', '加载项目模型...') }}</span>
        </div>
        <div v-else-if="projectModel || selectedModelInfo" style="margin-top: 16px">
          <p>
            {{ $t('gaPairs.usingModel', '使用模型') }}:
            <strong>
              {{ (projectModel || selectedModelInfo).providerName }}:
              {{ (projectModel || selectedModelInfo).modelName }}
            </strong>
          </p>
        </div>
        <div v-else style="margin-top: 16px">
          <el-alert
            :title="$t('gaPairs.noDefaultModel', '未找到默认模型')"
            type="warning"
            :closable="false"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">{{ genResult ? $t('common.close', '关闭') : $t('common.cancel', '取消') }}</el-button>
      <el-button
        v-if="!genResult"
        type="primary"
        @click="handleGenerate"
        :disabled="generating || fileIds.length === 0 || !(projectModel || selectedModelInfo)"
        :loading="generating"
      >
        {{ generating ? $t('gaPairs.generating', '生成中...') : $t('gaPairs.startGeneration', '开始生成') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';
import { useI18n } from 'vue-i18n';
import { batchGenerateGaPairs } from '@/api/gaPairs';
import { useModelStore } from '@/stores/model';
import http from '@/api/http';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  projectId: {
    type: String,
    required: true,
  },
  fileIds: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['update:modelValue', 'success']);

const { t, locale } = useI18n();
const modelStore = useModelStore();

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

const generating = ref(false);
const genError = ref(null);
const genResult = ref(null);
const appendMode = ref(false);
const projectModel = ref(null);
const loadingModel = ref(false);

const selectedModelInfo = computed(() => modelStore.selectedModelInfo);

// 获取项目默认模型
const fetchProjectModel = async () => {
  try {
    loadingModel.value = true;
    // 获取项目信息
    const projectResponse = await http.get(`/projects/${props.projectId}`);
    const projectData = projectResponse?.data || projectResponse;

    // 获取模型配置
    const modelResponse = await http.get(`/projects/${props.projectId}/model-config`);
    const modelConfigData = modelResponse?.data || modelResponse;

    if (modelConfigData && Array.isArray(modelConfigData)) {
      const defaultId = projectData.default_model_config_id || projectData.defaultModelConfigId;
      const targetModel = defaultId
        ? modelConfigData.find((m) => m.id === defaultId)
        : modelConfigData.find(
            (m) => m.model_name && m.endpoint && (m.provider_id === 'ollama' || m.api_key)
          );

      if (targetModel) {
        projectModel.value = {
          id: targetModel.id,
          providerId: targetModel.provider_id || targetModel.providerId,
          providerName: targetModel.provider_name || targetModel.providerName,
          endpoint: targetModel.endpoint,
          apiKey: targetModel.api_key || targetModel.apiKey,
          modelName: targetModel.model_name || targetModel.modelName,
        };
      }
    }
  } catch (error) {
    console.error('获取项目模型失败:', error);
  } finally {
    loadingModel.value = false;
  }
};

// 批量生成GA对
const handleGenerate = async () => {
  if (props.fileIds.length === 0) {
    genError.value = t('gaPairs.selectAtLeastOneFile', '请至少选择一个文件');
    return;
  }

  const modelToUse = projectModel.value || selectedModelInfo.value;

  if (!modelToUse || !modelToUse.id) {
    genError.value = t('gaPairs.noDefaultModel', '未找到默认模型');
    return;
  }

  if (!modelToUse.modelName || !modelToUse.endpoint) {
    genError.value = t('gaPairs.incompleteModelConfig', '模型配置不完整，请检查模型设置');
    return;
  }

  if (modelToUse.providerId !== 'ollama' && !modelToUse.apiKey) {
    genError.value = t('gaPairs.missingApiKey', '缺少API密钥');
    return;
  }

  try {
    generating.value = true;
    genError.value = null;
    genResult.value = null;

    const currentLanguage = locale.value === 'en' ? 'en' : '中文';

    const requestData = {
      fileIds: props.fileIds.map((id) => String(id)),
      modelConfigId: modelToUse.id,
      language: currentLanguage,
      appendMode: appendMode.value,
    };

    const response = await batchGenerateGaPairs(props.projectId, requestData);

    // 处理响应
    const payload = response?.data || response;
    const dataArray = payload?.data || payload;
    const list = Array.isArray(dataArray?.data) ? dataArray.data : Array.isArray(dataArray) ? dataArray : [];
    const summary = payload?.summary || payload?.data?.summary;

    const successCount = summary?.success !== undefined ? summary.success : list.filter((item) => item.success).length;

    genResult.value = {
      total: summary?.total || list.length || 0,
      success: successCount,
    };

    // 发送全局刷新事件
    const successfulFileIds = list.filter((item) => item.success)?.map((item) => String(item.fileId)) || [];

    if (successfulFileIds.length > 0) {
      window.dispatchEvent(
        new CustomEvent('refreshGaPairsIndicators', {
          detail: {
            projectId: props.projectId,
            fileIds: successfulFileIds,
          },
        })
      );
    }

    emit('success', genResult.value);
  } catch (error) {
    console.error('批量生成GA对失败:', error);
    genError.value = error?.message || t('gaPairs.batchGenerationFailed', '批量生成失败');
  } finally {
    generating.value = false;
  }
};

// 关闭对话框
const handleClose = () => {
  dialogVisible.value = false;
  genError.value = null;
  genResult.value = null;
  appendMode.value = false;
};

// 监听对话框打开，自动获取模型
watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      if (selectedModelInfo.value && selectedModelInfo.value.id) {
        projectModel.value = projectModel.value || selectedModelInfo.value;
      }
      fetchProjectModel();
    }
  }
);
</script>

<style scoped>
.el-form-item__help {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
</style>

