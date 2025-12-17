<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    width="80%"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form label-width="120px" label-position="left">
      <el-form-item :label="$t('settings.prompts.promptType', '提示词类型')">
        <el-text>{{ promptType }}</el-text>
      </el-form-item>

      <el-form-item :label="$t('settings.prompts.keyName', '键名')">
        <el-text>{{ promptKey }}</el-text>
      </el-form-item>

      <el-form-item :label="$t('settings.prompts.contentPlaceholder', '提示词内容')">
        <el-input
          v-model="localContent"
          type="textarea"
          :rows="15"
          :placeholder="$t('settings.prompts.contentPlaceholder', '请输入提示词内容...')"
        />
      </el-form-item>

      <el-form-item>
        <el-button :icon="RefreshLeft" @click="handleRestore">
          {{ $t('settings.prompts.restoreDefaultContent', '恢复默认内容') }}
        </el-button>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">{{ $t('common.cancel', '取消') }}</el-button>
      <el-button type="primary" :icon="Document" :loading="loading" @click="handleSave">
        {{ $t('common.save', '保存') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue';
import { Document, RefreshLeft } from '@element-plus/icons-vue';

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
  promptType: {
    type: String,
    default: '',
  },
  promptKey: {
    type: String,
    default: '',
  },
  content: {
    type: String,
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['close', 'save', 'restore', 'content-change']);

const dialogVisible = ref(false);
const localContent = ref('');

watch(
  () => props.open,
  (newVal) => {
    dialogVisible.value = newVal;
    if (newVal) {
      localContent.value = props.content;
    }
  },
);

watch(
  () => props.content,
  (newVal) => {
    if (dialogVisible.value) {
      localContent.value = newVal;
    }
  },
);

watch(localContent, (newVal) => {
  emit('content-change', newVal);
});

const handleClose = () => {
  dialogVisible.value = false;
  emit('close');
};

const handleSave = () => {
  emit('save');
};

const handleRestore = () => {
  emit('restore');
};
</script>

<style scoped>
:deep(.el-dialog__body) {
  padding: 20px;
}
</style>

