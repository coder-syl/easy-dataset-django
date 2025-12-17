<template>
  <div class="question-tree-view">
    <el-empty description="树视图功能开发中..." />
  </div>
</template>

<script setup>
defineProps({
  questions: {
    type: Array,
    default: () => []
  },
  tags: {
    type: Array,
    default: () => []
  },
  selectedQuestions: {
    type: Array,
    default: () => []
  },
  searchTerm: {
    type: String,
    default: ''
  },
  projectId: {
    type: String,
    required: true
  }
});

defineEmits(['select-question', 'delete-question', 'edit-question']);
</script>

<style scoped>
.question-tree-view {
  padding: 16px;
}
</style>

