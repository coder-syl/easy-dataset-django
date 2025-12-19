<template>
  <el-dialog
    v-model="localOpen"
    :title="$t('images.generateQuestions', '生成问题')"
    width="480px"
    @close="handleClose"
  >
    <div v-if="image" class="info">
      <div class="label">{{ $t('images.imageName', '图片名称') }}:</div>
      <div class="value">{{ image.imageName }}</div>
    </div>
    <el-form label-width="120px">
      <el-form-item :label="$t('images.questionCount', '问题数量')">
        <el-input-number
          v-model="count"
          :min="1"
          :max="10"
        />
        <div class="form-tip">
          {{ $t('images.questionCountHelp', '建议 1~10 避免过多消耗') }}
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">
        {{ $t('common.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :loading="loading"
        @click="handleGenerate"
      >
        {{ $t('images.generateQuestions', '生成问题') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { useI18n } from 'vue-i18n';
import { useModelStore } from '@/stores/model';
import { generateImageQuestions } from '@/api/images';

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
  },
);
watch(localOpen, val => emit('update:open', val));

const count = ref(3);
const loading = ref(false);

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
  if (count.value < 1 || count.value > 10) {
    ElMessage.error(t('images.countRange', '问题数量必须在 1~10 之间'));
    return;
  }
  if (!props.image) return;

  loading.value = true;
  try {
    const language = locale.value || 'zh-CN';
    await generateImageQuestions(props.projectId, {
      imageId: props.image.id,
      model,
      language,
      count: count.value,
    });
    ElMessage.success(t('images.questionsGenerated', '问题生成成功'));
    emit('success');
    handleClose();
  } catch (e) {
    console.error('生成问题失败:', e);
    ElMessage.error(t('images.generateFailed', '生成失败'));
  } finally {
    loading.value = false;
  }
};

const handleClose = () => {
  if (loading.value) return;
  localOpen.value = false;
};
</script>

<style scoped>
.info {
  margin-bottom: 16px;
  font-size: 14px;
}
.label {
  font-weight: 500;
  color: var(--el-text-color-secondary);
}
.value {
  margin-top: 4px;
}
.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>


