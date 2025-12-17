<template>
  <el-result icon="warning" title="404" sub-title="Page not found">
    <template #extra>
      <el-button type="primary" @click="$router.push('/')">Back Home</el-button>
    </template>
  </el-result>
</template>

