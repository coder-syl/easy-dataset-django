<template>
  <div class="image-dataset-detail-view">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
    </div>

    <!-- 无数据状态 -->
    <el-alert
      v-else-if="!currentDataset"
      :title="$t('imageDatasets.notFound', '数据集不存在')"
      type="error"
      :closable="false"
    />

    <!-- 主要内容 -->
    <template v-else>
      <!-- 顶部导航栏（内联，避免多层 props 传递） -->
      <el-card class="header-card" style="margin-bottom:24px;">
        <div class="header-row" style="display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;">
          <div style="display:flex;align-items:center;gap:16px;">
            <el-button :icon="ArrowLeft" @click="handleBack">
              {{ $t('imageDatasets.title', '图像数据集') }}
            </el-button>
            <el-divider direction="vertical" />
            <span class="stats-text">
              {{ $t('datasets.stats', { total: datasets_all_count, confirmed: datasets_confirm_count, percentage: datasets_all_count>0?((datasets_confirm_count/datasets_all_count)*100).toFixed(2):'0.00' }) }}
            </span>
          </div>
          <div style="display:flex;align-items:center;gap:8px;">
            <el-button :icon="ArrowLeft" circle @click="() => handleNavigate('prev')" />
            <el-button :icon="ArrowRight" circle @click="() => handleNavigate('next')" />
            <el-divider direction="vertical" />
            <el-button :loading="confirming" type="primary" @click="handleConfirm">{{ confirming ? $t('common.confirming','确认中...') : $t('datasets.confirmSave','确认并保存') }}</el-button>
            <el-button type="danger" :icon="Delete" @click="handleDelete">{{ $t('common.delete','删除') }}</el-button>
          </div>
        </div>
      </el-card>

      <!-- 主要布局：左右分栏（内容与侧栏内联） -->
      <div class="content-layout">
        <!-- 左侧主要内容区域 -->
        <div class="dataset-content" style="flex:1;min-width:0;">
          <el-card>
            <div class="question-row" style="display:flex;align-items:center;gap:16px;margin-bottom:24px;">
              <div class="question-text" style="flex:1;font-size:16px;line-height:1.7;font-weight:600;background-color:var(--el-fill-color-lighter);padding:16px;border-radius:8px;color:var(--el-text-color-primary);">
                {{ currentDataset?.question }}
              </div>
            </div>

            <AnswerInput
              :answer-type="currentDataset?.answer_type || currentDataset?.answerType || 'text'"
              :answer="currentDataset?.answer"
              :labels="currentDataset?.available_labels || currentDataset?.availableLabels || []"
              :custom-format="currentDataset?.custom_format || currentDataset?.customFormat"
              :project-id="projectId"
              :dataset-id="currentDataset?.id"
              :image-name="currentDataset?.image_name || currentDataset?.imageName"
              :question="currentDataset?.questionData || { question: currentDataset?.question }"
              @answer-change="handleAnswerChange"
            />

            <div class="image-section" style="margin-top:24px;">
              <div class="image-wrapper" style="position:relative;width:100%;max-width:800px;margin:0 auto;padding-top:56.25%;border-radius:8px;overflow:hidden;background-color:var(--el-fill-color-lighter);border:1px solid var(--el-border-color);">
                <el-image v-if="currentDataset?.base64" :src="currentDataset.base64" fit="contain" style="position:absolute;top:0;left:0;width:100%;height:100%;" />
                <div v-else class="image-placeholder" style="position:absolute;top:0;left:0;width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:var(--el-text-color-placeholder);"><el-icon :size="60"><Picture /></el-icon></div>
              </div>
              <div class="image-name" style="margin-top:8px;font-size:12px;color:var(--el-text-color-secondary);text-align:center;">{{ currentDataset?.image_name || currentDataset?.imageName }}</div>
            </div>
          </el-card>
        </div>

        <!-- 右侧完整侧边栏（合并 MetadataInfo 与 MetadataEditor） -->
        <div class="sidebar" :key="currentDataset?.id || 'sidebar'" style="width:360px;position:sticky;top:24px;max-height:calc(100vh - 48px);overflow:auto;">
          <!-- MetadataInfo (inlined) -->
          <div class="metadata-info">
            <div class="section-title">{{ $t('common.detailInfo', '详细信息') }}</div>
            <div class="chips-container">
              <div v-if="currentDataset?.model" class="meta-badge meta-badge--plain">
                <strong>{{ $t('imageDatasets.modelInfo', '使用模型') }}:</strong> {{ currentDataset.model }}
              </div>

              <div v-if="parsedTags.length > 0" class="meta-badge meta-badge--primary">
                <strong>{{ $t('imageDatasets.tags', '标签') }}:</strong> {{ parsedTags.length }} {{ $t('common.items', '项') }}
              </div>

              <div class="meta-badge meta-badge--plain">
                <strong>{{ $t('imageDatasets.createdAt', '创建时间') }}:</strong> {{ formatDate(currentDataset?.create_at || currentDataset?.createAt) }}
              </div>

              <div v-if="currentDataset?.questionTemplate?.description" class="meta-badge meta-badge--plain description-tag">
                <strong>{{ $t('imageDatasets.description', '描述') }}:</strong> {{ currentDataset.questionTemplate.description }}
              </div>

              <div v-if="currentDataset?.confirmed" class="meta-badge meta-badge--success">
                {{ $t('datasets.confirmed', '已确认') }}
              </div>
            </div>

            <template v-if="currentDataset?.image || currentDataset?.image_name">
              <el-divider />
              <div class="section-title">{{ $t('images.imageInfo', '图片信息') }}</div>
              <div class="chips-container">
                <div v-if="(currentDataset?.image && currentDataset.image.width && currentDataset.image.height) || (currentDataset?.width && currentDataset?.height)" class="meta-badge meta-badge--plain">
                  {{ $t('images.resolution', '分辨率') }}: {{ (currentDataset?.image && currentDataset.image.width) || currentDataset?.width }}×{{ (currentDataset?.image && currentDataset.image.height) || currentDataset?.height }}
                </div>

                <div v-if="(currentDataset?.image && currentDataset.image.size) || currentDataset?.size" class="meta-badge meta-badge--plain">
                  {{ $t('images.fileSize', '文件大小') }}: {{ formatFileSize((currentDataset?.image && currentDataset.image.size) || currentDataset?.size) }}
                </div>

                <div v-if="(currentDataset?.image && (currentDataset.image.createAt || currentDataset.image.create_at)) || currentDataset?.image_create_at" class="meta-badge meta-badge--plain">
                  {{ $t('images.uploadTime', '上传时间') }}: {{ formatDate((currentDataset?.image && (currentDataset.image.createAt || currentDataset.image.create_at)) || currentDataset?.image_create_at) }}
                </div>

                <div v-if="currentDataset?.image?.imageName || currentDataset?.image_name" class="meta-badge meta-badge--plain description-tag">
                  <strong>{{ $t('images.fileName', '文件名') }}:</strong> {{ currentDataset?.image?.imageName || currentDataset?.image_name }}
                </div>
              </div>
            </template>
          </div>

          <!-- MetadataEditor (inlined) -->
          <el-card class="metadata-editor" style="margin-top:12px;">
            <div class="section">
              <div class="section-title">{{ $t('datasets.rating', '评分') }}</div>
              <StarRating
                :model-value="localScore"
                @update:model-value="handleScoreChange"
                :read-only="editorLoading"
              />
            </div>

            <el-divider />

            <div class="section">
              <div class="section-title">{{ $t('datasets.customTags', '自定义标签') }}</div>
              <TagSelector
                :model-value="localTags"
                :available-tags="availableTags"
                @update:model-value="handleTagsChange"
              />
            </div>

            <el-divider />

            <div class="section">
              <NoteInput
                :model-value="localNote"
                @update:model-value="handleNoteChange"
              />
            </div>
          </el-card>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref , computed , watch } from 'vue';
import { useRoute , useRouter } from 'vue-router';
import { Loading, Picture } from '@element-plus/icons-vue';
import { useImageDatasetDetails } from '@/composables/useImageDatasetDetails';
import AnswerInput from '@/components/images/AnswerInput.vue';
import { ArrowLeft, ArrowRight, Delete } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useI18n } from 'vue-i18n';
import { onMounted } from 'vue';
import { fetchImageDatasetTags } from '@/api/imageDatasets';
import StarRating from '@/components/datasets/StarRating.vue';
import TagSelector from '@/components/datasets/TagSelector.vue';
import NoteInput from '@/components/datasets/NoteInput.vue';
 

const route = useRoute();
const router = useRouter();
// 使用与 DatasetDetailView 相同的参数处理方式，确保路由参数类型稳定为字符串
const projectId = computed(() =>
  typeof route.params.projectId === 'string' ? route.params.projectId : String(route.params.projectId)
);
const datasetId = computed(() =>
  typeof route.params.datasetId === 'string' ? route.params.datasetId : String(route.params.datasetId)
);

const {
  currentDataset,
  loading,
  confirming,
  unconfirming,
  datasets_all_count,
  datasets_confirm_count,
  updateDataset,
  handleNavigate,
  handleConfirm,
  handleUnconfirm,
  handleDelete,
  regenerateDataset,
  regenerating
} = useImageDatasetDetails(projectId, datasetId);

// 处理答案变化
const handleAnswerChange = async (newAnswer) => {
  await updateDataset({ answer: newAnswer });
};

// 安全返回处理：优先跳回项目的 image-datasets 列表，若 projectId 无效则回退历史
const handleBack = () => {
  try {
    const pid = projectId.value;
    if (pid && pid !== 'undefined') {
      router.push(`/projects/${pid}/image-datasets`);
    } else {
      router.back();
    }
  } catch (e) {
    router.back();
  }
};

// 处理元数据更新（供内联编辑器调用）
const { t } = useI18n();
const editorLoading = ref(false);
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

// 本地编辑状态
const localScore = ref(0);
const localTags = ref([]);
const localNote = ref('');

// 解析用于 MetadataInfo 的标签计数
const parsedTags = computed(() => {
  try {
    if (!currentDataset.value) return [];
    if (typeof currentDataset.value.tags === 'string' && currentDataset.value.tags) {
      return JSON.parse(currentDataset.value.tags);
    }
    return Array.isArray(currentDataset.value.tags) ? currentDataset.value.tags : [];
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

// 获取项目中已使用的标签
onMounted(async () => {
  try {
    const response = await fetchImageDatasetTags(projectId.value);
    const data = response?.data || response;
    availableTags.value = data.tags?.map((t) => t.tag) || [];
  } catch (error) {
    console.error('获取可用标签失败:', error);
  }
});

// 同步 currentDataset 到本地状态
watch(
  () => currentDataset.value,
  (newDataset) => {
    if (newDataset) {
      localScore.value = newDataset.score || 0;
      const tags = parseDatasetTags(newDataset.tags);
      localTags.value = Array.isArray(tags) ? tags : [];
      localNote.value = newDataset.note || '';
    } else {
      localScore.value = 0;
      localTags.value = [];
      localNote.value = '';
    }
  },
  { deep: true }
);

// 更新数据集元数据
const updateMetadata = async (updates) => {
  if (editorLoading.value) return;

  if (updates.score !== undefined) {
    localScore.value = updates.score;
  }
  if (updates.note !== undefined) {
    localNote.value = updates.note;
  }

  editorLoading.value = true;
  try {
    await handleUpdate(updates);
    ElMessage.success(t('imageDatasets.updateSuccess', '更新成功'));
  } catch (error) {
    console.error('更新数据集元数据失败:', error);
    ElMessage.error(t('imageDatasets.updateFailed', '更新失败'));
    // 恢复本地状态
    if (updates.score !== undefined) {
      localScore.value = currentDataset.value?.score || 0;
    }
    if (updates.tags !== undefined) {
      const tags = parseDatasetTags(currentDataset.value?.tags);
      localTags.value = Array.isArray(tags) ? tags : [];
    }
    if (updates.note !== undefined) {
      localNote.value = currentDataset.value?.note || '';
    }
  } finally {
    editorLoading.value = false;
  }
};

const handleScoreChange = (newScore) => {
  updateMetadata({ score: newScore });
};

const handleTagsChange = (newTags) => {
  localTags.value = newTags;
  updateMetadata({ tags: JSON.stringify(newTags) });
};

const handleNoteChange = (newNote) => {
  updateMetadata({ note: newNote });
};
</script>

<style scoped>
.image-dataset-detail-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 70vh;
}

.content-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

/* MetadataInfo styles */
.metadata-info {
  margin-bottom: 24px;
}
.metadata-info .section-title {
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
  /* Allow wrapping of long filenames, break words when necessary */
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.image-name {
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  display: block;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
  padding: 4px 0;
}

/* MetadataEditor styles */
.metadata-editor {
  margin-bottom: 24px;
}
.metadata-editor .section {
  margin-bottom: 16px;
}
.metadata-editor .section:last-child {
  margin-bottom: 0;
}
.metadata-editor .section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

/* meta-badge replacements for el-tag */
.meta-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  background: var(--el-fill-color-2);
  color: var(--el-text-color-regular);
  border: 1px solid var(--el-border-color);
  font-size: 13px;
}
.meta-badge--primary {
  background: var(--el-color-primary-light,#eef6ff);
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}
.meta-badge--success {
  background: #f0f9eb;
  border-color: #b7eb8f;
  color: #67c23a;
}
.meta-badge strong {
  font-weight: 600;
  margin-right: 6px;
}
</style>

