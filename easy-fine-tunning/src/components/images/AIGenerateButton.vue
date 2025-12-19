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
import { useModelStore } from '@/stores/model';
import { generateImageDataset } from '@/api/images';
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
});

const emit = defineEmits(['success']);

const { t, locale } = useI18n();
const modelStore = useModelStore();

const loading = ref(false);

const handleGenerate = async () => {
  if (!props.projectId || !props.imageName || !props.question) {
    ElMessage.error(t('images.missingParameters', '缺少必要参数'));
    return;
  }

  const model = modelStore.selectedModelInfo;
  if (!model || model.type !== 'vision') {
    ElMessage.error(t('images.visionModelRequired', '请选择支持视觉的模型'));
    return;
  }

  loading.value = true;
  try {
    const questionText = typeof props.question === 'string' ? props.question : props.question?.question || '';
    
    const response = await generateImageDataset(props.projectId, {
      imageName: props.imageName,
      question: questionText,
      model,
      language: locale.value === 'zh-CN' ? 'zh' : 'en',
      previewOnly: props.previewOnly
    });

    const data = response?.data || response;
    if (data.success && data.answer) {
      let answerData = data.answer;
      if (props.answerType === 'label') {
        try {
          answerData = JSON.parse(data.answer);
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

