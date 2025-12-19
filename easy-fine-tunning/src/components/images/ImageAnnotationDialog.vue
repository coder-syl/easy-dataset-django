<template>
  <el-dialog
    v-model="localOpen"
    :title="$t('images.annotateImage', '标注图片')"
    width="960px"
    top="5vh"
    @close="emit('close')"
  >
    <div v-if="!image" class="empty">
      <el-empty :description="$t('images.noImageSelected', '未选择图片')" />
    </div>
    <div v-else class="layout">
      <div class="left">
        <el-image
          :src="image.base64 || image.path"
          :alt="image.imageName"
          fit="contain"
          class="preview"
        />
        <div class="meta">
          <div class="name">{{ image.imageName }}</div>
          <div class="stats">
            <el-tag size="small" type="info">
              {{ image.width }} × {{ image.height }}
            </el-tag>
            <el-tag size="small" type="success">
              {{ image.datasetCount || 0 }} {{ $t('images.questions', '个问题') }}
            </el-tag>
          </div>
        </div>
      </div>
      <div class="right">
        <el-form label-width="100px">
          <el-form-item :label="$t('images.question', '问题')">
            <el-select
              v-model="localSelectedTemplateId"
              filterable
              class="full-width"
              @change="onTemplateSelect"
            >
              <el-option
                v-for="tpl in templates"
                :key="tpl.id"
                :label="tpl.question"
                :value="tpl.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item :label="$t('images.answer', '答案')">
            <el-input
              v-if="!isJsonAnswer"
              v-model="localAnswer"
              type="textarea"
              :rows="6"
            />
            <el-input
              v-else
              v-model="localAnswer"
              type="textarea"
              :rows="8"
            />
          </el-form-item>
        </el-form>
      </div>
    </div>
    <template #footer>
      <el-button @click="handleClose" :disabled="saving">
        {{ $t('common.cancel') }}
      </el-button>
      <el-button
        type="primary"
        plain
        :loading="saving"
        @click="emit('save-and-next')"
      >
        {{ $t('images.saveAndContinue', '保存并继续') }}
      </el-button>
      <el-button
        type="primary"
        :loading="saving"
        @click="emit('save')"
      >
        {{ $t('common.save', '保存') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue';

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  image: {
    type: Object,
    default: null,
  },
  templates: {
    type: Array,
    default: () => [],
  },
  selectedTemplate: {
    type: Object,
    default: null,
  },
  answer: {
    type: [String, Array],
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  saving: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits([
  'update:open',
  'update:selected-template',
  'update:answer',
  'close',
  'save',
  'save-and-next',
]);

const localOpen = ref(props.open);
watch(
  () => props.open,
  val => {
    localOpen.value = val;
  },
);
watch(localOpen, val => emit('update:open', val));

const localSelectedTemplateId = ref(props.selectedTemplate?.id || null);
const localAnswer = ref(props.answer || '');

watch(
  () => props.selectedTemplate,
  tpl => {
    localSelectedTemplateId.value = tpl?.id || null;
  },
);

watch(
  () => props.answer,
  val => {
    localAnswer.value = val || '';
  },
);

watch(localAnswer, val => {
  emit('update:answer', val);
});

const isJsonAnswer = computed(() => {
  return props.selectedTemplate?.answer_type === 'custom_format';
});

const onTemplateSelect = (id) => {
  const tpl = props.templates.find(t => t.id === id) || null;
  emit('update:selected-template', tpl);
};

const handleClose = () => {
  localOpen.value = false;
  emit('close');
};
</script>

<style scoped>
.layout {
  display: flex;
  gap: 16px;
  min-height: 360px;
}

.left {
  flex: 0 0 360px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview {
  width: 100%;
  height: 260px;
  border-radius: 4px;
}

.meta {
  padding: 8px;
  border-radius: 4px;
  background-color: var(--el-fill-color-light);
}

.name {
  font-weight: 500;
  margin-bottom: 4px;
}

.stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.right {
  flex: 1;
}

.full-width {
  width: 100%;
}
</style>


