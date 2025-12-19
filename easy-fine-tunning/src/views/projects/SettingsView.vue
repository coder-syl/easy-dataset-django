<template>
  <div class="settings-view">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 项目不存在 -->
    <el-alert v-else-if="!projectExists" type="error" :closable="false">
      {{ $t('settings.notExist', '项目不存在') }}
    </el-alert>

    <!-- 错误状态 -->
    <el-alert v-else-if="error" type="error" :closable="false">
      {{ error }}
    </el-alert>

    <!-- 正常显示 -->
    <el-tabs v-else v-model="activeTab" type="border-card" @tab-change="handleTabChange">
      <el-tab-pane :label="$t('settings.basicInfo', '基本信息')" name="basic">
        <BasicSettings :project-id="projectId" />
      </el-tab-pane>
      <el-tab-pane :label="$t('settings.modelConfig', '模型配置')" name="model">
        <ModelConfigSettings :project-id="projectId" />
      </el-tab-pane>
      <el-tab-pane :label="$t('settings.taskConfig', '任务配置')" name="task">
        <TaskSettings :project-id="projectId" />
      </el-tab-pane>
      <el-tab-pane :label="$t('settings.promptConfig', '提示词配置')" name="prompts">
        <PromptSettings :project-id="projectId" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { fetchProjectDetail } from '../../api/project';
import ModelConfigSettings from '../../components/model/ModelConfigSettings.vue';
import BasicSettings from '../../components/settings/BasicSettings.vue';
import TaskSettings from '../../components/settings/TaskSettings.vue';
import PromptSettings from '../../components/settings/PromptSettings.vue';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const projectId = route.params.projectId;

const activeTab = ref('basic');
const projectExists = ref(true);
const loading = ref(true);
const error = ref(null);

// 从 URL 参数中获取当前 tab
onMounted(() => {
  const tab = route.query.tab;
  if (tab && ['basic', 'model', 'task', 'prompts'].includes(tab)) {
    activeTab.value = tab;
  }
  checkProject();
});

// 检查项目是否存在
const checkProject = async () => {
  try {
    loading.value = true;
    await fetchProjectDetail(projectId);
    projectExists.value = true;
  } catch (err) {
    if (err.response?.status === 404) {
      projectExists.value = false;
    } else {
      error.value = err.message || t('settings.fetchFailed', '获取项目详情失败');
    }
  } finally {
    loading.value = false;
  }
};

// 处理 tab 切换
const handleTabChange = (tabName) => {
  router.replace({
    query: { ...route.query, tab: tabName },
  });
};
</script>

<style scoped>
.settings-view {
  padding: 20px;
  /* max-width: 1400px; */
  margin: 0 auto;
}

.loading-container {
  padding: 20px;
}
</style>

