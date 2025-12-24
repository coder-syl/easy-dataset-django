<template>
  <div class="metadata-info">
    <!-- 数据集信息 -->
    <div class="section-title">{{ $t('common.detailInfo', '详细信息') }}</div>
    <div class="chips-container">
      <!-- 使用模型 -->
      <el-tag v-if="dataset.model" size="small" effect="plain">
        {{ $t('imageDatasets.modelInfo', '使用模型') }}: {{ dataset.model }}
      </el-tag>

      <!-- 标签数量 -->
      <el-tag v-if="parsedTags.length > 0" type="primary" size="small" effect="plain">
        {{ $t('imageDatasets.tags', '标签') }}: {{ parsedTags.length }} {{ $t('common.items', '项') }}
      </el-tag>

      <!-- 创建时间 -->
      <el-tag size="small" effect="plain">
        {{ $t('imageDatasets.createdAt', '创建时间') }}: {{ formatDate(dataset.create_at || dataset.createAt) }}
      </el-tag>

      <!-- 文本块信息 -->
      <el-tag v-if="dataset.questionTemplate?.description" size="small" effect="plain" class="description-tag">
        {{ $t('imageDatasets.description', '描述') }}: {{ dataset.questionTemplate.description }}
      </el-tag>

      <!-- 确认状态 -->
      <el-tag v-if="dataset.confirmed" type="success" size="small" effect="dark">
        {{ $t('datasets.confirmed', '已确认') }}
      </el-tag>
    </div>

    <!-- 图片信息 -->
    <template v-if="dataset.image || dataset.image_name">
      <el-divider />
      <div class="section-title">{{ $t('images.imageInfo', '图片信息') }}</div>
      <div class="chips-container">
        <!-- 图片尺寸 -->
        <el-tag v-if="(dataset.image && dataset.image.width && dataset.image.height) || (dataset.width && dataset.height)" size="small" effect="plain">
          {{ $t('images.resolution', '分辨率') }}: {{ (dataset.image && dataset.image.width) || dataset.width }}×{{ (dataset.image && dataset.image.height) || dataset.height }}
        </el-tag>

        <!-- 文件大小 -->
        <el-tag v-if="(dataset.image && dataset.image.size) || dataset.size" size="small" effect="plain">
          {{ $t('images.fileSize', '文件大小') }}: {{ formatFileSize((dataset.image && dataset.image.size) || dataset.size) }}
        </el-tag>

        <!-- 图片创建时间 -->
        <el-tag v-if="(dataset.image && (dataset.image.createAt || dataset.image.create_at)) || dataset.image_create_at" size="small" effect="plain">
          {{ $t('images.uploadTime', '上传时间') }}: {{ formatDate((dataset.image && (dataset.image.createAt || dataset.image.create_at)) || dataset.image_create_at) }}
        </el-tag>

        <!-- 图片名称 -->
        <el-tag v-if="dataset.image?.imageName || dataset.image_name" size="small" effect="plain" class="description-tag">
          {{ $t('images.fileName', '文件名') }}: {{ dataset.image?.imageName || dataset.image_name }}
        </el-tag>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  dataset: {
    type: Object,
    required: true
  }
});

// 解析标签
const parsedTags = computed(() => {
  try {
    if (typeof props.dataset.tags === 'string' && props.dataset.tags) {
      return JSON.parse(props.dataset.tags);
    }
    return Array.isArray(props.dataset.tags) ? props.dataset.tags : [];
  } catch {
    return [];
  }
});

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};
</script>

<style scoped>
.metadata-info {
  margin-bottom: 24px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.chips-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.description-tag {
  max-width: 100%;
  word-break: break-all;
}
</style>

