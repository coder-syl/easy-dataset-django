<template>
  <div class="dataset-content">
    <el-card>
      <!-- 问题和保存按钮 -->
      <div class="question-row">
        <div class="question-text">{{ dataset.question }}</div>
        <!-- 保存按钮 - 只在有变化时显示 -->
        <el-button
          v-if="hasChanges"
          type="primary"
          :icon="Save"
          :loading="saving"
          @click="handleSave"
        >
          {{ saving ? $t('common.saving', '保存中...') : $t('common.save', '保存') }}
        </el-button>
      </div>

      <!-- 答案编辑器 -->
      <AnswerInput
        :answer-type="dataset.answerType || 'text'"
        :answer="currentAnswer"
        :labels="dataset.availableLabels || []"
        :custom-format="dataset.customFormat"
        :project-id="projectId"
        :image-name="dataset.imageName"
        :question="dataset.questionData || { question: dataset.question }"
        @answer-change="handleAnswerChange"
      />

      <!-- 图片 -->
      <div class="image-section">
        <div class="image-wrapper">
          <el-image
            v-if="dataset.base64"
            :src="dataset.base64"
            :alt="dataset.imageName"
            fit="contain"
            class="image-media"
          />
          <div v-else class="image-placeholder">
            <el-icon :size="60"><Picture /></el-icon>
          </div>
        </div>
        <div class="image-name">{{ dataset.imageName }}</div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { Save, Picture } from '@element-plus/icons-vue';
import AnswerInput from '@/components/images/AnswerInput.vue';

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

const emit = defineEmits(['answer-change']);

const currentAnswer = ref(handleAnswer(props.dataset));
const hasChanges = ref(false);
const saving = ref(false);

// 处理答案格式
function handleAnswer(dataset) {
  const { answer, answerType } = dataset;
  if (answerType === 'label' || answerType === 'custom_format') {
    try {
      return JSON.parse(answer);
    } catch (e) {
      return answer;
    }
  }
  return answer;
}

// 当 dataset 变化时，重置状态
watch(
  [() => props.dataset.id, () => props.dataset.answer],
  () => {
    currentAnswer.value = handleAnswer(props.dataset);
    hasChanges.value = false;
  }
);

// 处理答案变化
const handleAnswerChange = (newAnswer) => {
  currentAnswer.value = newAnswer;

  // 检测是否有变化
  const originalAnswer = handleAnswer(props.dataset);
  const hasChanged = JSON.stringify(newAnswer) !== JSON.stringify(originalAnswer);
  hasChanges.value = hasChanged;
};

// 保存答案
const handleSave = async () => {
  saving.value = true;
  try {
    let answerToSave = currentAnswer.value;
    if (typeof answerToSave !== 'string') {
      answerToSave = JSON.stringify(answerToSave, null, 2);
    }
    emit('answer-change', answerToSave);
    hasChanges.value = false;
  } catch (error) {
    console.error('保存失败:', error);
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
.dataset-content {
  flex: 1;
  min-width: 0;
}

.question-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.question-text {
  flex: 1;
  font-size: 16px;
  line-height: 1.7;
  font-weight: 600;
  background-color: var(--el-fill-color-lighter);
  padding: 16px;
  border-radius: 8px;
  color: var(--el-text-color-primary);
}

.image-section {
  margin-top: 24px;
}

.image-wrapper {
  position: relative;
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding-top: 56.25%; /* 16:9 比例 */
  border-radius: 8px;
  overflow: hidden;
  background-color: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color);
}

.image-media {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.image-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
}

.image-name {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
}
</style>

