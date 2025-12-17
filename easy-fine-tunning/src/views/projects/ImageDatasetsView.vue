<template>
  <div class="image-datasets-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>{{ $t('datasets.imageQA') }}</h3>
        </div>
      </template>
      <p>{{ $t('datasets.imageQADescription') }}</p>
      <p>项目ID: {{ projectId }}</p>
    </el-card>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router';

const route = useRoute();
const projectId = route.params.projectId;
</script>

<style scoped>
.image-datasets-view {
  padding: 20px;
}
</style>

