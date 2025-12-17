<template>
  <el-dialog
    :model-value="modelValue"
    title="模板管理"
    width="600px"
    @update:model-value="$emit('update:modelValue', $event)"
    @close="$emit('close')"
  >
    <el-form :model="formData" label-width="120px">
      <el-form-item label="模板名称" required>
        <el-input v-model="formData.name" />
      </el-form-item>
      <el-form-item label="类型">
        <el-select v-model="formData.type">
          <el-option label="问题模板" value="question" />
        </el-select>
      </el-form-item>
      <el-form-item label="内容">
        <el-input v-model="formData.content" type="textarea" :rows="6" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('close')">{{ $t('common.cancel') }}</el-button>
      <el-button type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  template: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['update:modelValue', 'submit', 'close']);

const formData = ref({
  name: '',
  type: 'question',
  content: ''
});

watch(
  () => props.template,
  (template) => {
    if (template) {
      formData.value = {
        name: template.name || '',
        type: template.type || 'question',
        content: template.content || ''
      };
    } else {
      formData.value = {
        name: '',
        type: 'question',
        content: ''
      };
    }
  },
  { immediate: true }
);

const handleSubmit = () => {
  emit('submit', formData.value);
};
</script>

