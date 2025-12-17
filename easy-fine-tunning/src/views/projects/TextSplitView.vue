<template>
  <div class="text-split-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>{{ $t('textSplit.title') }}</h3>
        </div>
      </template>
      <p>{{ $t('textSplit.description') }}</p>
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
.text-split-view {
  padding: 20px;
}
</style>

