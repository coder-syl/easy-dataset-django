<template>
  <div class="message-input">
    <div v-if="uploadedImage" class="image-preview">
      <el-image
        :src="uploadedImage"
        fit="cover"
        style="max-width: 200px; max-height: 200px; border-radius: 4px"
      >
        <template #error>
          <div class="image-slot">加载失败</div>
        </template>
      </el-image>
      <el-button
        circle
        :icon="Close"
        size="small"
        @click="handleRemove"
        class="remove-image-btn"
      />
    </div>

    <div class="input-container">
      <el-input
        v-model="localInput"
        type="textarea"
        :placeholder="$t('playground.inputMessage', '输入消息...')"
        :rows="3"
        :disabled="isDisabled"
        @keydown.enter.exact.prevent="handleSend"
        @keydown.enter.shift.exact="handleShiftEnter"
        @input="handleInput"
      />
      <el-tooltip
        v-if="hasVisionModel"
        :content="$t('playground.uploadImage', '上传图片')"
        placement="top"
      >
        <el-upload
          :show-file-list="false"
          :before-upload="handleUpload"
          accept="image/*"
          class="upload-btn"
        >
          <el-button :icon="Picture" :disabled="isDisabled" circle />
        </el-upload>
      </el-tooltip>
      <el-button
        type="primary"
        :icon="Promotion"
        :loading="isLoading"
        :disabled="isSendDisabled"
        @click="handleSend"
      >
        {{ $t('playground.send', '发送') }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { Close, Picture, Promotion } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const props = defineProps({
  userInput: {
    type: String,
    default: '',
  },
  loading: {
    type: Object,
    default: () => ({}),
  },
  selectedModels: {
    type: Array,
    default: () => [],
  },
  uploadedImage: {
    type: String,
    default: null,
  },
  availableModels: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['input-change', 'send-message', 'image-upload', 'remove-image']);

const localInput = ref(props.userInput);

watch(
  () => props.userInput,
  (newVal) => {
    localInput.value = newVal;
  },
);

const isDisabled = computed(() => {
  return Object.values(props.loading).some((v) => v) || props.selectedModels.length === 0;
});

const isLoading = computed(() => {
  return Object.values(props.loading).some((v) => v);
});

const isSendDisabled = computed(() => {
  return isDisabled.value || (!localInput.value.trim() && !props.uploadedImage);
});

const hasVisionModel = computed(() => {
  return props.selectedModels.some((modelId) => {
    const model = props.availableModels.find((m) => m.id === modelId);
    return model && model.type === 'vision';
  });
});

const handleInput = (value) => {
  emit('input-change', value);
};

const handleSend = () => {
  if (!isSendDisabled.value) {
    emit('send-message');
  }
};

const handleShiftEnter = () => {
  // Shift+Enter 换行，不做任何处理
};

const handleUpload = (file) => {
  if (!file.type.startsWith('image/')) {
    ElMessage.error('只能上传图片文件');
    return false;
  }
  const reader = new FileReader();
  reader.onloadend = () => {
    emit('image-upload', reader.result);
  };
  reader.readAsDataURL(file);
  return false; // 阻止自动上传
};

const handleRemove = () => {
  emit('remove-image');
};
</script>

<style scoped>
.message-input {
  padding: 16px 0;
}

.image-preview {
  position: relative;
  display: inline-block;
  margin-bottom: 12px;
}

.remove-image-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
}

.remove-image-btn:hover {
  background: rgba(0, 0, 0, 0.8);
}

.input-container {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.upload-btn {
  flex-shrink: 0;
}
</style>

