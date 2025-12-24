<template>
  <el-button
    :icon="loading ? Loading : MagicStick"
    :loading="loading"
    :disabled="loading"
    size="small"
    @click="handleGenerate"
  >
    {{ loading ? $t('common.generating', '生成中...') : $t('images.aiGenerate', 'AI 识别') }}
  </el-button>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { useModelStore } from '@/stores/model';
import { generateImageDataset } from '@/api/images';
import { regenerateImageDataset } from '@/api/imageDatasets';
import { Loading, MagicStick } from '@element-plus/icons-vue';

const props = defineProps({
  projectId: {
    type: [String, Number],
    required: true
  },
  imageName: {
    type: String,
    required: true
  },
  question: {
    type: [String, Object],
    required: true
  },
  answerType: {
    type: String,
    default: 'text'
  },
  previewOnly: {
    type: Boolean,
    default: true
  }
,
  datasetId: {
    type: [String, Number],
    default: null
  }
});

const emit = defineEmits(['success']);

const { t, locale } = useI18n();
const modelStore = useModelStore();

const loading = ref(false);

const route = useRoute();

const handleGenerate = async () => {
  // 尝试从多个来源解析必要参数，增加容错性
  const projectIdVal = props.projectId || route?.params?.projectId || null;
  const imageNameVal = props.imageName || null;
  const questionProp = props.question || null;
  const questionText = typeof questionProp === 'string' ? questionProp : questionProp?.question || '';

  const missing = [];
  if (!projectIdVal) missing.push('projectId');
  if (!imageNameVal) missing.push('imageName');
  if (!questionText) missing.push('question');
  if (missing.length > 0) {
    console.error('AIGenerateButton missing params:', { projectIdVal, imageNameVal, questionProp });
    ElMessage.error(`${t('images.missingParameters', '缺少必要参数')}: ${missing.join(', ')}`);
    return;
  }

  const model = modelStore.selectedModelInfo;
  if (!model || model.type !== 'vision') {
    ElMessage.error(t('images.visionModelRequired', '请选择支持视觉的模型'));
    return;
  }

  loading.value = true;
  try {
    const payload = {
      imageName: imageNameVal,
      question: questionText,
      model,
      language: locale.value === 'zh-CN' ? 'zh' : 'en',
      previewOnly: props.previewOnly
    };

    let response;
    if (props.datasetId) {
      // 如果传入 datasetId，则视为对已保存数据集重新识别（regenerate）
      response = await regenerateImageDataset(projectIdVal, props.datasetId, payload);
    } else {
      response = await generateImageDataset(projectIdVal, payload);
    }

    const data = response?.data || response;
    // 支持多种后端返回格式： { success: true, answer: '...' } 或 { data: { answer: '...' } } 或 直接返回 serializer
    let answerRaw = null;
    if (data && typeof data === 'object') {
      if (data.answer) answerRaw = data.answer;
      else if (data.data && data.data.answer) answerRaw = data.data.answer;
      else if (data.dataset && data.dataset.answer) answerRaw = data.dataset.answer;
      else if (data.data && data.data.dataset && data.data.dataset.answer) answerRaw = data.data.dataset.answer;
      else if (data.data && data.data.answer === undefined && data.data.id && data.data.answer) answerRaw = data.data.answer;
      // fallback: if top-level contains fields of ImageDataset serializer
      else if (data.id && data.answer) answerRaw = data.answer;
    } else if (typeof data === 'string') {
      answerRaw = data;
    }

    if (answerRaw) {
      let answerData = answerRaw;
      if (props.answerType === 'label') {
        try {
          answerData = JSON.parse(answerRaw);
        } catch {}
      }
      emit('success', answerData);
      ElMessage.success(t('images.aiGenerateSuccess', 'AI 生成成功'));
    }
  } catch (error) {
    console.error('AI 生成失败:', error);
    const errorMsg = error?.response?.data?.error || t('images.aiGenerateFailed', 'AI 生成失败');
    ElMessage.error(errorMsg);
  } finally {
    loading.value = false;
  }
};
</script>

