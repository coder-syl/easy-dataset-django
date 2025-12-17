<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('datasets.optimizeTitle', 'AI优化')"
    width="600px"
    @close="handleClose"
  >
    <el-form label-width="100px">
      <el-form-item :label="$t('datasets.optimizeAdvice', '优化建议')" required>
        <el-input
          v-model="advice"
          type="textarea"
          :rows="6"
          :placeholder="$t('datasets.optimizePlaceholder', '请输入优化建议，AI将根据您的建议优化答案和思维链')"
          autofocus
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">{{ $t('common.cancel', '取消') }}</el-button>
      <el-button type="primary" :disabled="!advice.trim()" @click="handleConfirm">
        {{ $t('common.confirm', '确认') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:open', 'confirm', 'close']);

const dialogVisible = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val)
});

const advice = ref('');

watch(
  () => props.open,
  (newVal) => {
    if (!newVal) {
      advice.value = '';
    }
  }
);

const handleClose = () => {
  advice.value = '';
  emit('close');
};

const handleConfirm = () => {
  if (advice.value.trim()) {
    emit('confirm', advice.value.trim());
    advice.value = '';
  }
};
</script>

<style scoped>
:deep(.el-form-item) {
  margin-bottom: 20px;
}
</style>

