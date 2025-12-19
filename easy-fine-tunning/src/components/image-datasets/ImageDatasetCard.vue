<template>
  <el-card class="dataset-card" @click="$emit('click', dataset.id)">
    <!-- 图片区域 -->
    <div class="image-wrapper">
      <el-image
        :src="dataset.base64 || '/placeholder.png'"
        :alt="dataset.imageName"
        fit="cover"
        class="image-media"
      />

      <!-- 悬停遮罩 -->
      <div class="image-overlay" />

      <!-- 问题内容 - 底部，毛玻璃背景 -->
      <div class="question-overlay">
        <div class="question-text">{{ dataset.question }}</div>
      </div>
    </div>

    <!-- 内容区域 - 标签和操作按钮 -->
    <el-tooltip :content="getAnswerText()" placement="top" :show-after="300">
      <div class="card-content">
        <div class="content-row">
          <!-- 左侧：所有标签 -->
          <div class="tags-container">
            <el-tag
              :type="getAnswerTypeColor(dataset.answerType)"
              size="small"
              effect="plain"
              class="tag-item"
            >
              {{ getAnswerTypeLabel(dataset.answerType) }}
            </el-tag>
            <el-tag
              :type="dataset.confirmed ? 'success' : 'info'"
              size="small"
              effect="plain"
              class="tag-item"
            >
              {{ dataset.confirmed ? $t('imageDatasets.confirmed', '已确认') : $t('imageDatasets.unconfirmed', '未确认') }}
            </el-tag>
            <el-tag
              :type="dataset.score && dataset.score > 0 ? 'warning' : 'info'"
              size="small"
              effect="plain"
              class="tag-item"
            >
              ⭐ {{ getScoreLabel() }}
            </el-tag>
          </div>

          <!-- 右侧：操作按钮 -->
          <div class="actions-container">
            <el-tooltip :content="$t('imageDatasets.viewDetails', '查看详情')" placement="top">
              <el-button
                link
                type="primary"
                :icon="View"
                size="small"
                @click.stop="$emit('view', dataset.id)"
              />
            </el-tooltip>

            <el-tooltip :content="$t('imageDatasets.evaluate', '质量评估')" placement="top">
              <el-button
                link
                style="color: #f57c00"
                :icon="DataAnalysis"
                size="small"
                @click.stop="$emit('evaluate', dataset.id)"
              />
            </el-tooltip>

            <el-tooltip :content="$t('common.delete', '删除')" placement="top">
              <el-button
                link
                type="danger"
                :icon="Delete"
                size="small"
                @click.stop="$emit('delete', dataset.id)"
              />
            </el-tooltip>
          </div>
        </div>
      </div>
    </el-tooltip>
  </el-card>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { View, DataAnalysis, Delete } from '@element-plus/icons-vue';

const props = defineProps({
  dataset: {
    type: Object,
    required: true
  }
});

defineEmits(['click', 'view', 'delete', 'evaluate']);

const { t } = useI18n();

const getAnswerText = () => {
  if (!props.dataset.answer) return t('imageDatasets.noAnswer', '暂无答案');
  if (props.dataset.answerType === 'label') {
    try {
      const labels = JSON.parse(props.dataset.answer);
      return `${t('imageDatasets.labels', '标签')}: ${labels.join(', ')}`;
    } catch {
      return props.dataset.answer;
    }
  }
  return props.dataset.answer;
};

const getAnswerTypeLabel = (type) => {
  switch (type) {
    case 'label':
      return t('imageDatasets.typeLabel', '标签');
    case 'custom_format':
      return t('imageDatasets.typeCustom', '自定义');
    default:
      return t('imageDatasets.typeText', '文本');
  }
};

const getAnswerTypeColor = (type) => {
  switch (type) {
    case 'label':
      return 'secondary';
    case 'custom_format':
      return 'info';
    default:
      return 'primary';
  }
};

const getScoreLabel = () => {
  if (!props.dataset.score || props.dataset.score === 0) {
    return t('imageDatasets.unscored', '未评分');
  }
  return props.dataset.score;
};
</script>

<style scoped>
.dataset-card {
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
}

.dataset-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.image-wrapper {
  position: relative;
  width: 100%;
  padding-top: 75%; /* 4:3 比例 */
  overflow: hidden;
  background-color: #f5f5f5;
}

.image-media {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: transparent;
  transition: background 0.3s ease;
  pointer-events: none;
}

.dataset-card:hover .image-overlay {
  background: rgba(0, 0, 0, 0.1);
}

.question-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.6) 70%, transparent 100%);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.question-text {
  color: #fff;
  font-weight: 500;
  line-height: 1.4;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-align: center;
  font-size: 14px;
}

.card-content {
  padding: 12px;
  cursor: help;
}

.content-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.tags-container {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
}

.tag-item {
  font-size: 12px;
  height: 20px;
  line-height: 20px;
}

.actions-container {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
</style>

