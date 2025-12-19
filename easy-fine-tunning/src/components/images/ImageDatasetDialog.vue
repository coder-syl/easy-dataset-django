<template>
  <el-dialog
    v-model="localOpen"
    :title="$t('images.generateDataset', '生成数据集')"
    width="600px"
    @close="handleClose"
  >
    <div v-if="image" class="info">
      <div class="label">{{ $t('images.imageName', '图片名称') }}:</div>
      <div class="value">{{ image.imageName }}</div>
    </div>

    <div v-loading="loadingQuestions" class="dialog-content">
      <!-- 已有问题列表 -->
      <div v-if="existingQuestions.length > 0" class="questions-section">
        <div class="section-header">
          <h4 class="section-title">{{ $t('images.existingQuestions', '已有问题') }}</h4>
          <el-checkbox
            v-model="selectAll"
            :indeterminate="isIndeterminate"
            @change="handleSelectAll"
          >
            {{ $t('common.selectAll', '全选') }}
          </el-checkbox>
        </div>
        <div class="questions-list">
          <el-checkbox-group v-model="selectedQuestionIds">
            <div
              v-for="q in existingQuestions"
              :key="q.id"
              class="question-item"
            >
              <el-checkbox :label="q.id">
                <div class="question-text">{{ q.question }}</div>
                <div v-if="q.label" class="question-label">
                  <el-tag size="small" type="primary" effect="plain">
                    {{ q.label }}
                  </el-tag>
                </div>
              </el-checkbox>
            </div>
          </el-checkbox-group>
        </div>
      </div>

      <!-- 自定义问题输入 -->
      <div class="custom-section">
        <div class="section-header">
          <h4 class="section-title">{{ $t('images.customQuestions', '自定义问题') }}</h4>
          <span class="section-tip">{{ $t('images.customQuestionsTip', '（可选）') }}</span>
        </div>
        <el-input
          v-model="customQuestions"
          type="textarea"
          :rows="4"
          :placeholder="$t('images.customQuestionsPlaceholder', '请输入自定义问题，每行一个问题，支持多个问题')"
        />
        <div class="form-tip">
          {{ $t('images.customQuestionsHelp', '每行输入一个问题，支持输入多个问题') }}
        </div>
      </div>

      <!-- 提示信息 -->
      <el-alert
        v-if="selectedQuestionIds.length === 0 && !hasCustomQuestions"
        type="warning"
        :closable="false"
        class="alert"
      >
        {{ $t('images.selectAtLeastOneQuestion', '请至少选择一个已有问题或输入自定义问题') }}
      </el-alert>
    </div>

    <template #footer>
      <el-button @click="handleClose" :disabled="generating">
        {{ $t('common.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :loading="generating"
        :disabled="selectedQuestionIds.length === 0 && !hasCustomQuestions"
        @click="handleGenerate"
      >
        {{ $t('datasets.generateDataset', '生成数据集') }}
        <span v-if="totalToGenerate > 0">({{ totalToGenerate }})</span>
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { useI18n } from 'vue-i18n';
import { useModelStore } from '@/stores/model';
import { generateImageDataset } from '@/api/images';
import { fetchQuestions } from '@/api/question';
import { processInParallel } from '@/utils/processInParallel';

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  projectId: {
    type: [String, Number],
    required: true,
  },
  image: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(['update:open', 'success']);
const { t, locale } = useI18n();
const modelStore = useModelStore();

const localOpen = ref(props.open);
watch(
  () => props.open,
  val => {
    localOpen.value = val;
    if (val) {
      // 对话框打开时重置状态并加载问题
      resetState();
      if (props.image) {
        fetchExistingQuestions();
      }
    }
  },
);
watch(localOpen, val => emit('update:open', val));

const loadingQuestions = ref(false);
const generating = ref(false);
const existingQuestions = ref([]);
const selectedQuestionIds = ref([]);
const customQuestions = ref('');

// 计算属性
const selectAll = computed({
  get: () => existingQuestions.value.length > 0 && selectedQuestionIds.value.length === existingQuestions.value.length,
  set: (val) => {
    if (val) {
      selectedQuestionIds.value = existingQuestions.value.map(q => q.id);
    } else {
      selectedQuestionIds.value = [];
    }
  },
});

const isIndeterminate = computed(() => {
  const selectedCount = selectedQuestionIds.value.length;
  return selectedCount > 0 && selectedCount < existingQuestions.value.length;
});

const hasCustomQuestions = computed(() => {
  return customQuestions.value.trim().length > 0;
});

const totalToGenerate = computed(() => {
  let count = selectedQuestionIds.value.length;
  if (hasCustomQuestions.value) {
    const customLines = customQuestions.value.trim().split('\n').filter(line => line.trim().length > 0);
    count += customLines.length;
  }
  return count;
});

// 重置状态
const resetState = () => {
  existingQuestions.value = [];
  selectedQuestionIds.value = [];
  customQuestions.value = '';
  loadingQuestions.value = false;
  generating.value = false;
};

// 获取已有问题
const fetchExistingQuestions = async () => {
  if (!props.image?.id) return;
  
  try {
    loadingQuestions.value = true;
    const response = await fetchQuestions(props.projectId, {
      imageId: props.image.id,
    });
    
    // 处理响应数据
    let data = response;
    if (data && typeof data === 'object' && !Array.isArray(data) && 'data' in data) {
      existingQuestions.value = Array.isArray(data.data) ? data.data : [];
    } else if (Array.isArray(data)) {
      existingQuestions.value = data;
    } else {
      existingQuestions.value = [];
    }
  } catch (e) {
    console.error('获取问题列表失败:', e);
    ElMessage.error(t('images.fetchQuestionsFailed', '获取问题列表失败'));
    existingQuestions.value = [];
  } finally {
    loadingQuestions.value = false;
  }
};

// 全选/取消全选
const handleSelectAll = (val) => {
  if (val) {
    selectedQuestionIds.value = existingQuestions.value.map(q => q.id);
  } else {
    selectedQuestionIds.value = [];
  }
};

// 生成数据集
const handleGenerate = async () => {
  const model = modelStore.selectedModelInfo;
  if (!model) {
    ElMessage.error(t('images.selectModelFirst', '请先选择模型'));
    return;
  }
  if (model.type !== 'vision') {
    ElMessage.error(t('images.visionModelRequired', '请选择视觉模型'));
    return;
  }
  if (!props.image) return;

  // 检查是否有选择或输入
  if (selectedQuestionIds.value.length === 0 && !hasCustomQuestions.value) {
    ElMessage.error(t('images.selectAtLeastOneQuestion', '请至少选择一个已有问题或输入自定义问题'));
    return;
  }

  generating.value = true;
  const language = locale.value || 'zh-CN';
  let successCount = 0;
  let failCount = 0;

  try {
    // 构建所有要生成的问题列表
    const questionsToGenerate = [];

    // 添加已有问题
    if (selectedQuestionIds.value.length > 0) {
      for (const questionId of selectedQuestionIds.value) {
        const question = existingQuestions.value.find(q => q.id === questionId);
        if (question) {
          questionsToGenerate.push({
            type: 'existing',
            question: {
              id: question.id,
              question: question.question,
            },
            displayText: question.question,
          });
        }
      }
    }

    // 添加自定义问题
    if (hasCustomQuestions.value) {
      const customLines = customQuestions.value.trim().split('\n').filter(line => line.trim().length > 0);
      for (const questionText of customLines) {
        questionsToGenerate.push({
          type: 'custom',
          question: { question: questionText.trim() },
          displayText: questionText.trim(),
        });
      }
    }

    // 批量生成数据集（使用并发控制，避免同时发送过多请求）
    const results = await processInParallel(
      questionsToGenerate,
      async (item) => {
        try {
          await generateImageDataset(props.projectId, {
            imageId: props.image.id,
            imageName: props.image.imageName || props.image.image_name,
            question: item.question,
            model,
            language,
          });
          return { success: true, question: item.displayText };
        } catch (e) {
          console.error(`生成数据集失败 (问题: ${item.displayText}):`, e);
          return { success: false, question: item.displayText, error: e.message };
        }
      },
      3 // 并发数限制为 3
    );

    // 统计结果
    results.forEach(result => {
      if (result.success) {
        successCount++;
      } else {
        failCount++;
      }
    });

    // 显示结果
    if (successCount > 0 && failCount === 0) {
      ElMessage.success(t('images.datasetsGeneratedSuccess', { count: successCount }, `成功生成 ${successCount} 个数据集`));
    } else if (successCount > 0 && failCount > 0) {
      ElMessage.warning(t('images.datasetsGeneratedPartial', { success: successCount, fail: failCount }, `成功生成 ${successCount} 个，失败 ${failCount} 个`));
    } else {
      ElMessage.error(t('images.datasetsGeneratedFailed', '生成数据集失败'));
    }

    emit('success');
    handleClose();
  } catch (e) {
    console.error('生成数据集失败:', e);
    ElMessage.error(t('images.generateFailed', '生成失败'));
  } finally {
    generating.value = false;
  }
};

const handleClose = () => {
  if (generating.value) return;
  localOpen.value = false;
};
</script>

<style scoped>
.dialog-content {
  min-height: 200px;
}

.info {
  margin-bottom: 20px;
  font-size: 14px;
}

.label {
  font-weight: 500;
  color: var(--el-text-color-secondary);
}

.value {
  margin-top: 4px;
  word-break: break-all;
}

.questions-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.section-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.questions-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;
  padding: 8px;
}

.question-item {
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.question-item:last-child {
  border-bottom: none;
}

.question-text {
  margin-left: 8px;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.question-label {
  margin-left: 8px;
  margin-top: 4px;
}

.custom-section {
  margin-bottom: 16px;
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.alert {
  margin-top: 16px;
}
</style>
