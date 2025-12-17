<template>
  <div class="distill-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>{{ $t('distill.title') }}</h3>
        </div>
      </template>
      <p>{{ $t('distill.description') }}</p>
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
.distill-view {
  padding: 20px;
}
</style>

