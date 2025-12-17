<template>
  <el-select
    v-model="localSelected"
    multiple
    :placeholder="$t('playground.selectModelMax3', '选择模型（最多3个）')"
    style="width: 100%"
    @change="handleChange"
  >
    <el-option
      v-for="model in filteredModels"
      :key="model.id"
      :value="model.id"
      :label="getModelName(model.id)"
      :disabled="localSelected.length >= 3 && !localSelected.includes(model.id)"
    >
      <el-checkbox :model-value="localSelected.includes(model.id)" />
      <span style="margin-left: 8px">{{ getModelName(model.id) }}</span>
    </el-option>
  </el-select>
</template>

<script setup>
import { computed, ref, watch } from 'vue';

const props = defineProps({
  models: {
    type: Array,
    default: () => [],
  },
  selectedModels: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['change']);

const localSelected = ref([...props.selectedModels]);

watch(
  () => props.selectedModels,
  (newVal) => {
    localSelected.value = [...newVal];
  },
);

const filteredModels = computed(() => {
  return props.models.filter((m) => {
    const providerId = (m?.providerId || '').toString().toLowerCase();
    if (providerId === 'ollama') {
      return m.modelName && m.endpoint;
    }
    return m.modelName && m.endpoint && m.apiKey;
  });
});

const getModelName = (modelId) => {
  const model = props.models.find((m) => m.id === modelId);
  return model ? `${model.providerName}: ${model.modelName}` : modelId;
};

const handleChange = (value) => {
  // 限制最多选择 3 个
  const limited = value.slice(0, 3);
  localSelected.value = limited;
  emit('change', limited);
};
</script>

