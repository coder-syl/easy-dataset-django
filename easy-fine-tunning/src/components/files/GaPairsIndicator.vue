<template>
  <div class="ga-pairs-indicator">
    <el-tooltip v-if="loading" :content="$t('common.loading', '加载中...')" placement="top">
      <el-icon class="is-loading"><Loading /></el-icon>
    </el-tooltip>
    <el-tag
      v-else-if="hasGaPairs"
      :type="activePairs.length > 0 ? 'primary' : 'info'"
      size="small"
      @click="handleOpenDialog"
      class="ga-pairs-tag"
    >
      <el-icon class="ga-tag-icon"><MagicStick /></el-icon>
      <span class="ga-tag-text">{{ activePairs.length }}/{{ gaPairs.length }} {{ $t('gaPairs.pairs', 'GA对') }}</span>
    </el-tag>
    <el-tooltip v-else :content="$t('gaPairs.generateGaPairs', '生成GA对')" placement="top">
      <el-button size="small" text circle @click="handleOpenDialog">
        <el-icon><MagicStick /></el-icon>
      </el-button>
    </el-tooltip>

    <!-- GA对管理对话框 -->
    <el-dialog
      v-model="detailsOpen"
      :title="$t('gaPairs.manageGaPairs', { fileName }, `管理GA对 - ${fileName}`)"
      width="80%"
      :close-on-click-modal="false"
    >
      <div v-loading="loading">
        <div v-if="gaPairs.length === 0" class="no-ga-pairs">
          <el-empty :description="$t('gaPairs.noGaPairs', '暂无GA对')" />
          <el-button type="primary" @click="handleGenerate" :loading="generating">
            {{ $t('gaPairs.generateGaPairs', '生成GA对') }}
          </el-button>
        </div>
        <div v-else class="ga-pairs-list">
          <div v-for="pair in gaPairs" :key="pair.id" class="ga-pair-item">
            <el-card shadow="hover">
              <div class="pair-header">
                <el-tag  :type="pair.isActive ? 'success' : 'info'">
                  {{ $t('gaPairs.pair', '对') }} {{ pair.pairNumber }}
                </el-tag>
                <el-switch
                  v-model="pair.isActive"
                  @change="handleToggleActive(pair.id, pair.isActive)"
                  :loading="pair.toggling"
                />
              </div>
              <div class="pair-content">
                <div class="pair-genre">
                  <strong>{{ $t('gaPairs.genre', '体裁') }}:</strong> {{ pair.genreTitle }}
                  <br />
                  <span class="pair-desc">{{ pair.genreDesc }}</span>
                </div>
                <div class="pair-audience">
                  <strong>{{ $t('gaPairs.audience', '受众') }}:</strong> {{ pair.audienceTitle }}
                  <br />
                  <span class="pair-desc">{{ pair.audienceDesc }}</span>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailsOpen = false">{{ $t('common.close', '关闭') }}</el-button>
        <el-button v-if="gaPairs.length === 0" type="primary" @click="handleGenerate" :loading="generating">
          {{ $t('gaPairs.generateGaPairs', '生成GA对') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { MagicStick, Loading } from '@element-plus/icons-vue';
import { useI18n } from 'vue-i18n';
import { fetchGaPairs, generateGaPairsForFile, toggleGaPairActive } from '@/api/gaPairs';
import { useModelStore } from '@/stores/model';

const props = defineProps({
  projectId: {
    type: String,
    required: true,
  },
  fileId: {
    type: String,
    required: true,
  },
  fileName: {
    type: String,
    default: '',
  },
});

const { t, locale } = useI18n();
const modelStore = useModelStore();

const gaPairs = ref([]);
const loading = ref(false);
const generating = ref(false);
const detailsOpen = ref(false);

const hasGaPairs = computed(() => gaPairs.value.length > 0);
const activePairs = computed(() => gaPairs.value.filter((pair) => pair.isActive));

// 获取GA对状态
const fetchGaPairsStatus = async () => {
  try {
    loading.value = true;
    const response = await fetchGaPairs(props.projectId, props.fileId);
    gaPairs.value = Array.isArray(response) ? response : response?.data || [];
  } catch (error) {
    console.error('获取GA对状态失败:', error);
    gaPairs.value = [];
    // 404 表示没有GA对，不显示错误
    if (error?.response?.status !== 404) {
      ElMessage.error(error?.message || t('gaPairs.fetchFailed', '获取GA对失败'));
    }
  } finally {
    loading.value = false;
  }
};

// 生成GA对
const handleGenerate = async () => {
  if (!modelStore.selectedModelInfo) {
    ElMessage.warning(t('gaPairs.selectModelFirst', '请先选择模型'));
    return;
  }

  try {
    generating.value = true;
    const payload = {
      modelConfig: {
        id: modelStore.selectedModelInfo.id,
        providerId: modelStore.selectedModelInfo.providerId,
        endpoint: modelStore.selectedModelInfo.endpoint,
        apiKey: modelStore.selectedModelInfo.apiKey,
        modelName: modelStore.selectedModelInfo.modelName,
        modelId: modelStore.selectedModelInfo.modelId,
      },
      language: locale.value === 'zh' || locale.value === 'zh-CN' ? '中文' : 'en',
      appendMode: false,
    };

    await generateGaPairsForFile(props.projectId, props.fileId, payload);
    ElMessage.success(t('gaPairs.generateSuccess', '生成GA对成功'));
    await fetchGaPairsStatus();
  } catch (error) {
    console.error('生成GA对失败:', error);
    ElMessage.error(error?.message || t('gaPairs.generateFailed', '生成GA对失败'));
  } finally {
    generating.value = false;
  }
};

// 切换GA对激活状态
const handleToggleActive = async (pairId, isActive) => {
  const pair = gaPairs.value.find((p) => p.id === pairId);
  if (!pair) return;

  const originalValue = !isActive;
  pair.toggling = true;

  try {
    await toggleGaPairActive(props.projectId, props.fileId, pairId, isActive);
    ElMessage.success(t('gaPairs.updateSuccess', '更新成功'));
  } catch (error) {
    console.error('更新GA对状态失败:', error);
    ElMessage.error(error?.message || t('gaPairs.updateFailed', '更新失败'));
    // 恢复原值
    pair.isActive = originalValue;
  } finally {
    pair.toggling = false;
  }
};

// 打开对话框
const handleOpenDialog = () => {
  detailsOpen.value = true;
  if (!hasGaPairs.value) {
    fetchGaPairsStatus();
  }
};

// 监听刷新事件
const handleRefresh = (event) => {
  const { projectId: eventProjectId, fileIds } = event.detail || {};
  if (eventProjectId === props.projectId && fileIds?.includes(String(props.fileId))) {
    fetchGaPairsStatus();
  }
};

onMounted(() => {
  fetchGaPairsStatus();
  window.addEventListener('refreshGaPairsIndicators', handleRefresh);
});

onUnmounted(() => {
  window.removeEventListener('refreshGaPairsIndicators', handleRefresh);
});
</script>

<style scoped>
.ga-pairs-indicator {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

.ga-pairs-indicator :deep(.el-tag) {
  white-space: nowrap !important;
  flex-shrink: 0;
  display: inline-flex !important;
  align-items: center;
  gap: 4px;
  line-height: 1.5;
  height: auto;
  min-height: 24px;
  padding: 2px 8px;
  max-width: none;
  overflow: visible;
  flex-wrap: nowrap !important;
}

.ga-pairs-indicator :deep(.el-tag *) {
  white-space: nowrap !important;
  flex-shrink: 0;
  flex-wrap: nowrap !important;
}

.ga-pairs-indicator :deep(.ga-tag-icon) {
  flex-shrink: 0 !important;
  margin-right: 0;
  display: inline-flex !important;
  align-items: center;
  white-space: nowrap !important;
}

.ga-pairs-indicator :deep(.ga-tag-text) {
  white-space: nowrap !important;
  display: inline !important;
  flex-shrink: 0;
  flex-wrap: nowrap !important;
}

.no-ga-pairs {
  text-align: center;
  padding: 20px;
}

.ga-pairs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ga-pair-item {
  width: 100%;
}

.pair-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.pair-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.pair-genre,
.pair-audience {
  padding: 8px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
}

.pair-desc {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-top: 4px;
  display: block;
}
</style>

