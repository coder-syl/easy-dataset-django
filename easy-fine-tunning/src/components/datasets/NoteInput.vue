<template>
  <div class="note-input">
    <el-input
      v-model="localNote"
      type="textarea"
      :rows="4"
      :placeholder="$t('datasets.notePlaceholder', '输入备注信息...')"
      :maxlength="500"
      show-word-limit
      @input="handleInput"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:model-value']);

const localNote = ref(props.modelValue);

watch(
  () => props.modelValue,
  (newVal) => {
    localNote.value = newVal;
  }
);

const handleInput = (value) => {
  emit('update:model-value', value);
};
</script>

<style scoped>
.note-input {
  width: 100%;
}
</style>

