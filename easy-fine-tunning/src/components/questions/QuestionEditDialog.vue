<template>
  <el-dialog
    :model-value="modelValue"
    :title="mode === 'create' ? $t('questions.createQuestion') : $t('questions.editQuestion')"
    width="600px"
    @update:model-value="$emit('update:modelValue', $event)"
    @close="$emit('close')"
  >
    <el-form :model="formData" label-width="120px">
      <!-- 数据源类型选择 -->
      <el-form-item :label="$t('questions.sourceType')">
        <el-select v-model="formData.sourceType" @change="handleSourceTypeChange">
          <el-option :label="$t('questions.template.sourceType.text')" value="text" />
          <el-option :label="$t('questions.template.sourceType.image')" value="image" />
        </el-select>
      </el-form-item>

      <!-- 问题内容 -->
      <el-form-item :label="$t('questions.questionContent')" required>
        <el-input
          v-model="formData.question"
          type="textarea"
          :rows="4"
          :placeholder="$t('questions.questionPlaceholder')"
        />
      </el-form-item>

      <!-- 文本块选择（仅当数据源为文本时显示） -->
      <el-form-item v-if="formData.sourceType === 'text'" :label="$t('questions.chunkId')" required>
        <el-select
          v-model="formData.chunkId"
          :placeholder="$t('questions.searchChunk')"
          clearable
          filterable
          style="width: 100%"
        >
          <el-option
            v-for="chunk in chunks"
            :key="chunk.id"
            :label="chunk.name || chunk.id"
            :value="chunk.id"
          />
        </el-select>
      </el-form-item>

      <!-- 图片选择（仅当数据源为图片时显示） -->
      <el-form-item v-if="formData.sourceType === 'image'" :label="$t('questions.imageId')" required>
        <el-select
          v-model="formData.imageId"
          :placeholder="$t('questions.searchImage')"
          clearable
          filterable
          style="width: 100%"
        >
          <el-option
            v-for="image in images"
            :key="image.id"
            :label="image.imageName || image.name || image.id"
            :value="image.id"
          />
        </el-select>
      </el-form-item>

      <!-- 标签选择（仅当数据源为文本时显示） -->
      <el-form-item v-if="formData.sourceType === 'text'" :label="$t('questions.label')">
        <el-select
          v-model="formData.label"
          :placeholder="$t('questions.searchTag')"
          clearable
          filterable
          style="width: 100%"
        >
          <el-option
            v-for="tag in flattenedTags"
            :key="tag.id"
            :label="tag.label"
            :value="tag.id"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('close')">{{ $t('common.cancel') }}</el-button>
      <el-button
        type="primary"
        :disabled="!formData.question || (formData.sourceType === 'text' ? !formData.chunkId : !formData.imageId)"
        @click="handleSubmit"
      >
        {{ mode === 'create' ? $t('common.create') : $t('common.save') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import http from '@/api/http';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  initialData: {
    type: Object,
    default: null
  },
  tags: {
    type: Array,
    default: () => []
  },
  mode: {
    type: String,
    default: 'create'
  },
  projectId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['update:modelValue', 'submit', 'close']);

const { t } = useI18n();

const formData = ref({
  id: '',
  question: '',
  sourceType: 'text',
  chunkId: '',
  imageId: '',
  label: ''
});

const chunks = ref([]);
const images = ref([]);

// 扁平化标签树
const flattenTags = (tags = [], prefix = '') => {
  let flatTags = [];
  const traverse = (node) => {
    flatTags.push({
      id: node.label,
      label: node.label,
      originalLabel: node.label
    });
    if (node.child && node.child.length > 0) {
      node.child.forEach((child) => traverse(child));
    }
  };
  tags.forEach((tag) => traverse(tag));
  flatTags.push({
    id: 'other',
    label: t('datasets.uncategorized') || '未分类',
    originalLabel: 'other'
  });
  return flatTags;
};

const flattenedTags = computed(() => flattenTags(props.tags));

const loadChunks = async () => {
  try {
    const response = await http.get(`/projects/${props.projectId}/split/`);
    // HTTP 拦截器已经解包了 { code: 0, data: {...} } 格式，返回的是 data 部分
    // 所以 response 应该是 { chunks: [...], fileName: ..., totalChunks: ..., toc: ..., tags: [...] }
    chunks.value = response?.chunks || [];
    console.log('加载的文本块数量:', chunks.value.length);
    if (chunks.value.length > 0) {
      console.log('文本块列表:', chunks.value.map(c => ({ id: c.id, name: c.name })));
    }
  } catch (error) {
    console.error('获取文本块列表失败:', error);
    chunks.value = [];
  }
};

const loadImages = async () => {
  try {
    const response = await http.get(`/projects/${props.projectId}/images/`, {
      params: { page: 1, pageSize: 10000, simple: true }
    });
    images.value = response?.data?.data || response?.data || [];
  } catch (error) {
    console.error('获取图片列表失败:', error);
  }
};

const handleSourceTypeChange = () => {
  // 切换数据源类型时清空相关字段
  formData.value.chunkId = '';
  formData.value.imageId = '';
};


watch(
  () => props.initialData,
  (data) => {
    if (data) {
      const sourceType = data.imageId || data.image_id ? 'image' : 'text';
      const chunkId = data.chunkId || data.chunk_id || '';
      const imageId = data.imageId || data.image_id || '';
      const label = data.label || 'other';
      
      formData.value = {
        id: data.id || '',
        question: data.question || '',
        sourceType,
        chunkId,
        imageId,
        label
      };
    } else {
      formData.value = {
        id: '',
        question: '',
        sourceType: 'text',
        chunkId: '',
        imageId: '',
        label: ''
      };
    }
  },
  { immediate: true }
);


const handleSubmit = () => {
  emit('submit', formData.value);
};

// 监听对话框打开状态，确保数据已加载
watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      // 对话框打开时重新加载数据
      loadChunks();
      loadImages();
    }
  },
  { immediate: true }
);

onMounted(() => {
  loadChunks();
  loadImages();
});
</script>
