<template>
  <div class="dataset-sidebar">
    <!-- 元数据信息 - Chip 形式 -->
    <MetadataInfo :dataset="dataset" />

    <!-- 操作卡片 -->
    <MetadataEditor :dataset="dataset" :project-id="projectId" @update="handleUpdate" />
  </div>
</template>

<script setup>
import MetadataInfo from './MetadataInfo.vue';
import MetadataEditor from './MetadataEditor.vue';

const props = defineProps({
  dataset: {
    type: Object,
    required: true
  },
  projectId: {
    type: [String, Number],
    required: true
  }
});

const emit = defineEmits(['update']);

const handleUpdate = (updates) => {
  emit('update', updates);
};
</script>

<style scoped>
.dataset-sidebar {
  width: 360px;
  position: sticky;
  top: 24px;
  max-height: calc(100vh - 48px);
  overflow-y: auto;
}
</style>

