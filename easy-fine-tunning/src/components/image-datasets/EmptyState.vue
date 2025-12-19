<template>
  <div class="empty-state">
    <div class="empty-icon">
      <el-icon :size="60" color="var(--el-color-primary)">
        <Picture />
      </el-icon>
    </div>
    <h3 class="empty-title">{{ $t('imageDatasets.noImageDatasets', '还没有图像数据集') }}</h3>
    <p class="empty-description">
      {{ $t('imageDatasets.noImageDatasetsDescription', '通过图片管理页面生成图像数据集') }}
    </p>
  </div>
</template>

<script setup>
import { Picture } from '@element-plus/icons-vue';
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.empty-icon {
  margin-bottom: 24px;
}

.empty-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 8px 0;
}

.empty-description {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin: 0;
}
</style>

