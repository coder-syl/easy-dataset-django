<template>
  <el-card class="metadata-editor">
    <!-- 评分区域 -->
    <div class="section">
      <div class="section-title">{{ $t('datasets.rating', '评分') }}</div>
      <StarRating
        :model-value="localScore"
        @update:model-value="handleScoreChange"
        :read-only="loading"
      />
    </div>

    <el-divider />

    <!-- 标签区域 -->
    <div class="section">
      <div class="section-title">{{ $t('datasets.customTags', '自定义标签') }}</div>
      <TagSelector
        :model-value="localTags"
        :available-tags="availableTags"
        @update:model-value="handleTagsChange"
      />
    </div>

    <el-divider />

    <!-- 备注区域 -->
    <div class="section">
      <NoteInput
        :model-value="localNote"
        @update:model-value="handleNoteChange"
      />
    </div>
  </el-card>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useI18n } from 'vue-i18n';
import { fetchImageDatasetTags } from '@/api/imageDatasets';
import StarRating from '@/components/datasets/StarRating.vue';
import TagSelector from '@/components/datasets/TagSelector.vue';
import NoteInput from '@/components/datasets/NoteInput.vue';

const props = defineProps({
  dataset: {
    type: Object,
    required: true
  },
  projectId: {
    type: [String, Number],
    required: true
  }
});

const emit = defineEmits(['update']);

const { t } = useI18n();

const loading = ref(false);
const availableTags = ref([]);

// 解析数据集中的标签
const parseDatasetTags = (tagsString) => {
  try {
    if (typeof tagsString === 'string' && tagsString) {
      const parsed = JSON.parse(tagsString);
      return Array.isArray(parsed) ? parsed : [];
    }
    return Array.isArray(tagsString) ? tagsString : [];
  } catch (e) {
    return [];
  }
};

// 本地状态管理，从 props 初始化
const localScore = ref(props.dataset?.score || 0);
const localTags = ref(() => {
  const tags = parseDatasetTags(props.dataset?.tags);
  return Array.isArray(tags) ? tags : [];
});
const localNote = ref(props.dataset?.note || '');

// 获取项目中已使用的标签
onMounted(async () => {
  try {
    const response = await fetchImageDatasetTags(props.projectId);
    const data = response?.data || response;
    availableTags.value = data.tags?.map((t) => t.tag) || [];
  } catch (error) {
    console.error('获取可用标签失败:', error);
  }
});

// 同步props中的dataset到本地状态
watch(
  () => props.dataset,
  (newDataset) => {
    if (newDataset) {
      localScore.value = newDataset.score || 0;
      const tags = parseDatasetTags(newDataset.tags);
      localTags.value = Array.isArray(tags) ? tags : [];
      localNote.value = newDataset.note || '';
    }
  },
  { deep: true }
);

// 更新数据集元数据
const updateMetadata = async (updates) => {
  if (loading.value) return;

  // 立即更新本地状态，提升响应速度
  if (updates.score !== undefined) {
    localScore.value = updates.score;
  }
  if (updates.note !== undefined) {
    localNote.value = updates.note;
  }

  loading.value = true;
  try {
    emit('update', updates);
    ElMessage.success(t('imageDatasets.updateSuccess', '更新成功'));
  } catch (error) {
    console.error('更新数据集元数据失败:', error);
    ElMessage.error(t('imageDatasets.updateFailed', '更新失败'));

    // 出错时恢复本地状态
    if (updates.score !== undefined) {
      localScore.value = props.dataset?.score || 0;
    }
    if (updates.tags !== undefined) {
      const tags = parseDatasetTags(props.dataset?.tags);
      localTags.value = Array.isArray(tags) ? tags : [];
    }
    if (updates.note !== undefined) {
      localNote.value = props.dataset?.note || '';
    }
  } finally {
    loading.value = false;
  }
};

// 处理评分变更
const handleScoreChange = (newScore) => {
  updateMetadata({ score: newScore });
};

// 处理标签变更
const handleTagsChange = (newTags) => {
  // 立即更新本地状态（保持为数组）
  localTags.value = newTags;
  // 发送给父组件时转换为 JSON 字符串
  updateMetadata({ tags: JSON.stringify(newTags) });
};

// 处理备注变更
const handleNoteChange = (newNote) => {
  updateMetadata({ note: newNote });
};
</script>

<style scoped>
.metadata-editor {
  margin-bottom: 24px;
}

.section {
  margin-bottom: 16px;
}

.section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}
</style>

