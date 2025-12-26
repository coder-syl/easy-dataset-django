<template>
  <div class="project-overview">
    <el-page-header @back="$router.push('/')" content="Project">
      <template #title>
        <span>{{ project?.name || 'Project' }}</span>
      </template>
    </el-page-header>
    <el-card v-if="project" class="mt">
      <h3>{{ project.name }}</h3>
      <p>{{ project.description }}</p>
      <p>
        {{ $t('projects.lastUpdated') }}:
        {{ formatDate(project.update_at || project.create_at) }}
      </p>
    </el-card>
    <el-skeleton v-else animated />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { fetchProjectDetail } from '../api/project';
import { useModelStore } from '../stores/model';

const route = useRoute();
const router = useRouter();
const project = ref(null);
const modelStore = useModelStore();

const formatDate = (value) => {
  if (!value) return '--';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? '--' : d.toLocaleDateString('zh-CN');
};

onMounted(async () => {
  try {
    const data = await fetchProjectDetail(route.params.projectId);
    project.value = data;
    // 加载模型配置
    await modelStore.loadModelConfigs();
    // 默认重定向到文本分割页面（与 Next.js 保持一致）
    router.push(`/projects/${route.params.projectId}/text-split`);
  } catch (e) {
    project.value = null;
  }
});
</script>

<style scoped>
.project-overview {
  padding: 16px;
}
.mt {
  margin-top: 16px;
}
</style>


