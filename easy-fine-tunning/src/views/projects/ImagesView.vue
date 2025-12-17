<template>
  <div class="images-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>{{ $t('images.title') }}</h3>
        </div>
      </template>
      <p>{{ $t('images.description') }}</p>
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
.images-view {
  padding: 20px;
}
</style>

