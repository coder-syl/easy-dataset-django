<template>
  <div class="model-management-view">
    <div class="toolbar">
      <div class="title-block">
        <h2>{{ $t('modelManagement.title') }}</h2>
        <p class="subtitle">{{ $t('modelManagement.description') }}</p>
      </div>
      <div class="toolbar-actions">
        <el-button type="default">{{ $t('modelManagement.test') }}</el-button>
        <el-button type="primary">{{ $t('modelManagement.add') }}</el-button>
      </div>
    </div>

    <el-card class="models-card">
      <el-skeleton v-if="loading" animated :count="4">
        <template #template>
          <div class="model-row-skeleton">
            <el-skeleton-item variant="circle" style="width: 36px; height: 36px" />
            <div class="skeleton-text">
              <el-skeleton-item variant="text" style="width: 160px" />
              <el-skeleton-item variant="text" style="width: 120px; margin-top: 6px" />
            </div>
          </div>
        </template>
      </el-skeleton>

      <template v-else>
        <el-empty v-if="models.length === 0" description="暂无模型" />
        <div v-else class="models-list">
          <div v-for="item in models" :key="item.id" class="model-row">
            <div class="model-main">
              <div class="model-avatar">
                <span>{{ item.modelName?.[0]?.toUpperCase() || 'M' }}</span>
              </div>
              <div class="model-text">
                <div class="model-name">{{ item.modelName || item.modelId }}</div>
                <div class="model-provider">{{ item.providerId }}</div>
              </div>
            </div>
            <div class="model-endpoint">
              <el-tag type="success" v-if="item.endpoint">{{ item.endpoint }}</el-tag>
              <el-tag type="warning" v-else>未配置 Endpoint / API Key</el-tag>
            </div>
            <div class="model-actions">
              <el-button link type="primary" size="small">{{ $t('common.edit', '编辑') }}</el-button>
              <el-button link type="danger" size="small">{{ $t('common.delete', '删除') }}</el-button>
            </div>
          </div>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { fetchGlobalModels } from '../api/model';
import { ElMessage } from 'element-plus';

const loading = ref(true);
const models = ref([]);

const loadModels = async () => {
  try {
    loading.value = true;
    const data = await fetchGlobalModels();
    models.value = Array.isArray(data) ? data : data?.data || [];
  } catch (err) {
    console.error(err);
    ElMessage.error('获取模型列表失败');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadModels();
});
</script>

<style scoped>
.model-management-view {
  padding: 20px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.title-block h2 {
  margin: 0;
  font-size: 20px;
}
.subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: #6b7280;
}
.toolbar-actions {
  display: flex;
  gap: 8px;
}
.models-card {
  border-radius: 12px;
}
.models-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.model-row {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 2fr) auto;
  align-items: center;
  padding: 10px 4px;
  border-bottom: 1px solid #e5e7eb;
}
.model-row:last-child {
  border-bottom: none;
}
.model-main {
  display: flex;
  align-items: center;
  gap: 10px;
}
.model-avatar {
  width: 36px;
  height: 36px;
  border-radius: 999px;
  background: #eef2ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: #4f46e5;
}
.model-text .model-name {
  font-weight: 600;
}
.model-text .model-provider {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}
.model-endpoint {
  display: flex;
  justify-content: flex-start;
}
.model-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.model-row-skeleton {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
}
.skeleton-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>

