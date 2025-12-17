<template>
  <el-card class="dataset-rating-section">
    <template #header>
      <h4>{{ $t('datasets.ratingAndTags', '评分与标签') }}</h4>
    </template>
    <div class="rating-content">
      <!-- 评分 -->
      <div class="rating-item">
        <label class="item-label">{{ $t('datasets.score', '评分') }}</label>
        <StarRating
          :model-value="localScore"
          @update:model-value="handleScoreChange"
          :read-only="false"
        />
      </div>

      <!-- 标签 -->
      <div class="rating-item">
        <label class="item-label">{{ $t('datasets.tags', '标签') }}</label>
        <TagSelector
          :model-value="localTags"
          :available-tags="availableTags"
          @update:model-value="handleTagsChange"
        />
      </div>

      <!-- 备注 -->
      <div class="rating-item">
        <label class="item-label">{{ $t('datasets.note', '备注') }}</label>
        <NoteInput
          :model-value="localNote"
          @update:model-value="handleNoteChange"
        />
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { updateDataset } from '@/api/dataset';
import { fetchDatasetTags } from '@/api/dataset';
import StarRating from './StarRating.vue';
import TagSelector from './TagSelector.vue';
import NoteInput from './NoteInput.vue';

const props = defineProps({
  dataset: {
    type: Object,
    required: true
  },
  projectId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['update']);

const { t } = useI18n();

const availableTags = ref([]);
const loading = ref(false);

const parseDatasetTags = (tagsString) => {
  try {
    return JSON.parse(tagsString || '[]');
  } catch (e) {
    return [];
  }
};

const localScore = ref(props.dataset?.score || 0);
const localTags = ref(parseDatasetTags(props.dataset?.tags));
const localNote = ref(props.dataset?.note || '');

// 获取可用标签
onMounted(async () => {
  try {
    const response = await fetchDatasetTags(props.projectId);
    // Django 返回格式: {code: 0, data: {tags: [...]}}
    const data = response?.data || response;
    availableTags.value = data?.tags?.map((tag) => tag.tag) || [];
  } catch (error) {
    console.error('获取可用标签失败:', error);
  }
});

// 同步 props 中的 dataset 到本地状态
watch(
  () => props.dataset,
  (newDataset) => {
    if (newDataset) {
      localScore.value = newDataset.score || 0;
      localTags.value = parseDatasetTags(newDataset.tags);
      localNote.value = newDataset.note || '';
    }
  },
  { deep: true, immediate: true }
);

// 更新数据集元数据
const updateMetadata = async (updates) => {
  if (loading.value) return;

  // 立即更新本地状态
  if (updates.score !== undefined) {
    localScore.value = updates.score;
  }
  if (updates.tags !== undefined) {
    localTags.value = updates.tags;
  }
  if (updates.note !== undefined) {
    localNote.value = updates.note;
  }

  loading.value = true;
  try {
    const updateData = {};
    if (updates.score !== undefined) {
      updateData.score = updates.score;
    }
    if (updates.tags !== undefined) {
      updateData.tags = Array.isArray(updates.tags) ? JSON.stringify(updates.tags) : updates.tags;
    }
    if (updates.note !== undefined) {
      updateData.note = updates.note;
    }

    await updateDataset(props.projectId, props.dataset.id, updateData);

    ElMessage.success(t('datasets.updateSuccess', '更新成功'));

    if (emit('update')) {
      emit('update');
    }
  } catch (error) {
    console.error('更新数据集元数据失败:', error);
    ElMessage.error(t('datasets.updateFailed', '更新失败'));
  } finally {
    loading.value = false;
  }
};

const handleScoreChange = (score) => {
  updateMetadata({ score });
};

const handleTagsChange = (tags) => {
  updateMetadata({ tags });
};

const handleNoteChange = (note) => {
  updateMetadata({ note });
};
</script>

<style scoped>
.dataset-rating-section {
  margin-bottom: 16px;
}

.rating-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.rating-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.item-label {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
}
</style>

