<template>
  <el-tabs
    :model-value="selectedCategory"
    type="border-card"
    @update:model-value="handleCategoryChange"
    class="category-tabs"
  >
    <el-tab-pane
      v-for="[categoryKey, categoryConfig] in categoryEntries"
      :key="categoryKey"
      :label="categoryConfig.displayName[currentLanguage]"
      :name="categoryKey"
    />
  </el-tabs>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  categoryEntries: {
    type: Array,
    required: true,
  },
  selectedCategory: {
    type: String,
    default: '',
  },
  currentLanguage: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['category-change']);

const handleCategoryChange = (categoryKey) => {
  emit('category-change', categoryKey);
};
</script>

<style scoped>
.category-tabs {
  margin-bottom: 20px;
}
</style>

