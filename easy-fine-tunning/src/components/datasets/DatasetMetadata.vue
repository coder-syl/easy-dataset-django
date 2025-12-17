<template>
  <el-card class="dataset-metadata">
    <template #header>
      <h4>{{ $t('datasets.metadata', '元数据') }}</h4>
    </template>
    <div class="metadata-content">
      <el-tag type="info" style="margin-bottom: 8px">
        {{ $t('datasets.model', '模型') }}: {{ currentDataset?.model || '' }}
      </el-tag>
      <el-tag v-if="currentDataset?.question_label" type="primary" style="margin-bottom: 8px">
        {{ $t('common.label', '标签') }}: {{ currentDataset.question_label }}
      </el-tag>
      <el-tag style="margin-bottom: 8px">
        {{ $t('datasets.createdAt', '创建时间') }}:
        {{ formatDate(currentDataset?.create_at) }}
      </el-tag>
      <el-tag
        v-if="currentDataset?.chunk_name"
        type="info"
        style="cursor: pointer; margin-bottom: 8px"
        @click="handleViewChunk"
      >
        {{ $t('datasets.chunkId', '文本块') }}: {{ currentDataset.chunk_name }}
      </el-tag>
    </div>
  </el-card>
</template>

<script setup>
import { useI18n } from 'vue-i18n';
import http from '@/api/http';

const props = defineProps({
  currentDataset: {
    type: Object,
    default: () => ({})
  },
  projectId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['view-chunk']);

const { t } = useI18n();

const formatDate = (dateStr) => {
  if (!dateStr) return t('datasets.invalidDate', '无效日期');
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
  } catch {
    return t('datasets.invalidDate', '无效日期');
  }
};

const handleViewChunk = async () => {
  try {
    const chunkName = props.currentDataset?.chunk_name;
    if (!chunkName) return;

    const response = await http.get(`/projects/${props.projectId}/chunks/name/`, {
      params: { chunkName }
    });

    // Django 返回格式: {code: 0, data: {...}}
    const data = response?.data || response;
    const chunk = data?.data || data;

    emit('view-chunk', chunk);
  } catch (error) {
    console.error('获取文本块失败:', error);
  }
};
</script>

<style scoped>
.dataset-metadata {
  margin-bottom: 16px;
}

.metadata-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metadata-content :deep(.el-tag) {
  width: 100%;
  justify-content: flex-start;
}
</style>

