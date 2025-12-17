<template>
  <div class="dataset-square-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>{{ $t('datasetSquare.title') }}</h3>
        </div>
      </template>
      <p>{{ $t('datasetSquare.description') }}</p>
    </el-card>
  </div>
</template>

<script setup></script>

<style scoped>
.dataset-square-view {
  padding: 20px;
}
</style>

