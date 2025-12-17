<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <h3>{{ $t('settings.basicInfo', '基本信息') }}</h3>
      </div>
    </template>

    <el-skeleton v-if="loading" :rows="3" animated />

    <el-form v-else :model="projectInfo" label-width="120px" label-position="left">
      <el-form-item :label="$t('projects.id', '项目ID')">
        <el-input v-model="projectInfo.id" disabled>
          <template #append>
            <el-text type="info" size="small">{{ $t('settings.idNotEditable', '项目ID不可编辑') }}</el-text>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item :label="$t('projects.name', '项目名称')" required>
        <el-input v-model="projectInfo.name" :placeholder="$t('projects.name', '项目名称')" />
      </el-form-item>

      <el-form-item :label="$t('projects.description', '项目描述')">
        <el-input
          v-model="projectInfo.description"
          type="textarea"
          :rows="3"
          :placeholder="$t('projects.description', '项目描述')"
        />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :icon="Document" :loading="saving" @click="handleSave">
          {{ $t('settings.saveBasicInfo', '保存基本信息') }}
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { Document } from '@element-plus/icons-vue';
import { fetchProjectDetail, updateProject } from '../../api/project';

const props = defineProps({
  projectId: {
    type: String,
    required: true,
  },
});

const { t } = useI18n();

const projectInfo = ref({
  id: '',
  name: '',
  description: '',
});

const loading = ref(true);
const saving = ref(false);

// 加载项目信息
const loadProjectInfo = async () => {
  try {
    loading.value = true;
    const response = await fetchProjectDetail(props.projectId);
    const data = response?.data || response;
    const project = data?.data || data || {};

    projectInfo.value = {
      id: project.id || '',
      name: project.name || '',
      description: project.description || '',
    };
  } catch (error) {
    console.error('获取项目信息出错:', error);
    ElMessage.error(t('settings.fetchFailed', '获取项目详情失败'));
  } finally {
    loading.value = false;
  }
};

// 保存项目信息
const handleSave = async () => {
  if (!projectInfo.value.name?.trim()) {
    ElMessage.warning(t('projects.nameRequired', '项目名称不能为空'));
    return;
  }

  try {
    saving.value = true;
    await updateProject(props.projectId, {
      name: projectInfo.value.name,
      description: projectInfo.value.description,
    });
    ElMessage.success(t('settings.saveSuccess', '保存成功'));
  } catch (error) {
    console.error('保存项目信息出错:', error);
    ElMessage.error(t('settings.saveFailed', '保存失败'));
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  loadProjectInfo();
});
</script>

<style scoped>
.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}
</style>

