<template>
  <el-dialog
    v-model="localOpen"
    :title="$t('images.batchGenerateDatasets', '批量生成数据集')"
    width="600px"
    @close="handleClose"
  >
    <div v-loading="loadingStats" class="dialog-content">
      <!-- 统计信息 -->
      <div class="stats-section">
        <h4 class="section-title">{{ $t('images.statistics', '统计信息') }}</h4>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-label">{{ $t('images.totalImages', '总图片数') }}</div>
            <div class="stat-value">{{ stats.totalImages }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">{{ $t('images.imagesWithQuestions', '有问题图片') }}</div>
            <div class="stat-value">{{ stats.imagesWithQuestions }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">{{ $t('images.unansweredQuestions', '未生成数据集的问题') }}</div>
            <div class="stat-value highlight">{{ stats.unansweredQuestions }}</div>
          </div>
        </div>
      </div>

      <!-- 筛选条件 -->
      <div class="filter-section">
        <h4 class="section-title">{{ $t('images.filterConditions', '筛选条件') }}</h4>
        <el-form label-width="140px">
          <el-form-item :label="$t('images.onlyImagesWithQuestions', '仅处理有问题的图片')">
            <el-switch v-model="filters.onlyWithQuestions" />
            <div class="form-tip">
              {{ $t('images.onlyImagesWithQuestionsTip', '只处理已生成问题的图片') }}
            </div>
          </el-form-item>
          <el-form-item :label="$t('images.onlyUnanswered', '仅处理未生成数据集的问题')">
            <el-switch v-model="filters.onlyUnanswered" :disabled="!filters.onlyWithQuestions" />
            <div class="form-tip">
              {{ $t('images.onlyUnansweredTip', '跳过已生成数据集的问题，只处理未生成的问题') }}
            </div>
          </el-form-item>
        </el-form>
      </div>

      <!-- 生成模式 -->
      <div class="mode-section">
        <h4 class="section-title">{{ $t('images.generationMode', '生成模式') }}</h4>
        <el-radio-group v-model="generationMode">
          <el-radio value="all">
            {{ $t('images.generateAllQuestions', '为每张图片的所有问题生成数据集') }}
          </el-radio>
          <el-radio value="unanswered">
            {{ $t('images.generateUnansweredOnly', '仅生成未生成数据集的问题') }}
          </el-radio>
        </el-radio-group>
      </div>

      <!-- 模型信息 -->
      <div class="model-section">
        <div class="model-info">
          <span class="model-label">{{ $t('images.currentModel', '当前模型') }}:</span>
          <span class="model-name">{{ modelName }}</span>
        </div>
      </div>

      <!-- 提示信息 -->
      <el-alert
        v-if="stats.unansweredQuestions === 0"
        type="info"
        :closable="false"
        class="alert"
      >
        {{ $t('images.noUnansweredQuestions', '当前没有未生成数据集的图片问题') }}
      </el-alert>
      <el-alert
        v-else
        type="info"
        :closable="false"
        class="alert"
      >
        {{ $t('images.batchGenerateTip', '将创建后台任务，自动为符合条件的图片问题生成数据集。任务将在后台运行，您可以在任务管理页面查看进度。') }}
      </el-alert>
    </div>

    <template #footer>
      <el-button @click="handleClose">
        {{ $t('common.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :loading="creating"
        :disabled="stats.unansweredQuestions === 0"
        @click="handleCreateTask"
      >
        {{ $t('images.createBatchTask', '创建批量生成任务') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { fetchQuestions } from '@/api/question';
import { fetchImages } from '@/api/images';

const props = defineProps({
  open: { type: Boolean, default: false },
  projectId: { type: [String, Number], required: true },
  modelName: { type: String, default: '' },
});

const emit = defineEmits(['update:open', 'create-task']);

const { t } = useI18n();

const localOpen = ref(props.open);
watch(() => props.open, val => { localOpen.value = val; });
watch(localOpen, val => emit('update:open', val));

const loadingStats = ref(false);
const creating = ref(false);
const stats = ref({
  totalImages: 0,
  imagesWithQuestions: 0,
  unansweredQuestions: 0,
});

const filters = ref({
  onlyWithQuestions: true,
  onlyUnanswered: true,
});

const generationMode = ref('unanswered');

// 当对话框打开时，获取统计信息
watch(localOpen, async (val) => {
  if (val) {
    await fetchStatistics();
  }
});

const fetchStatistics = async () => {
  try {
    loadingStats.value = true;
    
    // 获取所有图片
    const imagesResponse = await fetchImages(props.projectId, {
      page: 1,
      pageSize: 10000,
    });
    
    let images = [];
    if (imagesResponse && typeof imagesResponse === 'object' && 'data' in imagesResponse) {
      images = Array.isArray(imagesResponse.data) ? imagesResponse.data : [];
    } else if (Array.isArray(imagesResponse)) {
      images = imagesResponse;
    }
    
    const totalImages = images.length;
    const imagesWithQuestions = images.filter(img => (img.questionCount || 0) > 0).length;
    
    // 获取所有图片问题（未生成数据集的）
    const questionsResponse = await fetchQuestions(props.projectId, {
      source_type: 'image',
      status: 'unanswered', // 未回答的问题
      all: true, // 获取所有数据
    });
    
    let unansweredQuestions = 0;
    if (questionsResponse && typeof questionsResponse === 'object' && 'data' in questionsResponse) {
      const questions = Array.isArray(questionsResponse.data) ? questionsResponse.data : [];
      unansweredQuestions = questions.length;
    } else if (Array.isArray(questionsResponse)) {
      unansweredQuestions = questionsResponse.length;
    }
    
    stats.value = {
      totalImages,
      imagesWithQuestions,
      unansweredQuestions,
    };
  } catch (e) {
    console.error('获取统计信息失败:', e);
    ElMessage.error(t('images.fetchStatsFailed', '获取统计信息失败'));
  } finally {
    loadingStats.value = false;
  }
};

const handleCreateTask = () => {
  emit('create-task', {
    filters: filters.value,
    generationMode: generationMode.value,
  });
};

const handleClose = () => {
  if (creating.value) return;
  localOpen.value = false;
};
</script>

<style scoped>
.dialog-content {
  padding: 8px 0;
}

.section-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.stats-section {
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-item {
  padding: 12px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.stat-value.highlight {
  color: var(--el-color-primary);
}

.filter-section {
  margin-bottom: 24px;
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.mode-section {
  margin-bottom: 24px;
}

.mode-section .el-radio-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.model-section {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
}

.model-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.model-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.alert {
  margin-top: 16px;
}
</style>

