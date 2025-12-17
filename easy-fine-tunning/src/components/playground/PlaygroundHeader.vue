<template>
  <div class="playground-header">
    <el-row :gutter="16">
      <el-col :span="12">
        <ModelSelector
          :models="availableModels"
          :selected-models="selectedModels"
          @change="handleModelChange"
        />
      </el-col>
      <el-col :span="6">
        <el-select
          v-model="localOutputMode"
          :placeholder="$t('playground.outputMode', '输出模式')"
          style="width: 100%"
          @change="handleOutputModeChange"
        >
          <el-option
            :label="$t('playground.normalOutput', '普通输出')"
            value="normal"
          />
          <el-option
            :label="$t('playground.streamingOutput', '流式输出')"
            value="streaming"
          />
        </el-select>
      </el-col>
      <el-col :span="6">
        <el-button
          type="danger"
          :icon="Delete"
          @click="handleClear"
          :disabled="isClearDisabled"
          style="width: 100%"
        >
          {{ $t('playground.clearConversation', '清空对话') }}
        </el-button>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { Delete } from '@element-plus/icons-vue';
import ModelSelector from './ModelSelector.vue';

const props = defineProps({
  availableModels: {
    type: Array,
    default: () => [],
  },
  selectedModels: {
    type: Array,
    default: () => [],
  },
  conversations: {
    type: Object,
    default: () => ({}),
  },
  outputMode: {
    type: String,
    default: 'normal',
  },
});

const emit = defineEmits(['model-selection', 'clear-conversations', 'output-mode-change']);

const localOutputMode = ref(props.outputMode);

watch(
  () => props.outputMode,
  (newVal) => {
    localOutputMode.value = newVal;
  },
);

const isClearDisabled = computed(() => {
  return (
    props.selectedModels.length === 0 ||
    Object.values(props.conversations).every((conv) => conv.length === 0)
  );
});

const handleModelChange = (value) => {
  emit('model-selection', value);
};

const handleClear = () => {
  emit('clear-conversations');
};

const handleOutputModeChange = (value) => {
  emit('output-mode-change', value);
};
</script>

<style scoped>
.playground-header {
  padding: 16px 0;
}
</style>

