<template>
  <div class="tag-selector">
    <el-select
      v-model="localTags"
      multiple
      filterable
      allow-create
      :placeholder="$t('datasets.selectTags', '选择或输入标签')"
      :max-collapse-tags="3"
      @change="handleChange"
    >
      <el-option
        v-for="tag in availableTags"
        :key="tag"
        :label="tag"
        :value="tag"
      />
    </el-select>
    <div v-if="localTags.length > 0" class="selected-tags">
      <el-tag
        v-for="(tag, index) in localTags"
        :key="index"
        closable
        @close="handleRemoveTag(index)"
        style="margin-right: 8px; margin-top: 8px"
      >
        {{ tag }}
      </el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  availableTags: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['update:model-value']);

const localTags = ref(Array.isArray(props.modelValue) ? [...props.modelValue] : []);

watch(
  () => props.modelValue,
  (newVal) => {
    localTags.value = Array.isArray(newVal) ? [...newVal] : [];
  },
  { deep: true }
);

const handleChange = (tags) => {
  localTags.value = tags;
  emit('update:model-value', tags);
};

const handleRemoveTag = (index) => {
  localTags.value.splice(index, 1);
  emit('update:model-value', [...localTags.value]);
};
</script>

<style scoped>
.tag-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>

