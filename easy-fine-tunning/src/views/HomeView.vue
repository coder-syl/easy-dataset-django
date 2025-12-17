<template>
  <div class="home">
    <section class="hero">
      <div>
        <h1>{{ $t('home.title') }}</h1>
        <p class="subtitle">{{ $t('home.subtitle') }}</p>
        <div class="actions">
          <el-button type="primary" size="large" @click="openCreate">
            <el-icon><Plus /></el-icon>
            {{ $t('common.createProject') }}
          </el-button>
          <el-button size="large" plain>
            <el-icon><Search /></el-icon>
            {{ $t('common.searchPublic') }}
          </el-button>
        </div>
      </div>
    </section>

    <section class="project-section">
      <!-- <div class="section-header">
        <h3>{{ $t('common.createProject') }}</h3>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          {{ $t('common.createProject') }}
        </el-button>
      </div> -->
      <div v-if="loading" class="project-grid">
        <el-card v-for="n in skeletonCount" :key="n" class="project-card">
          <el-skeleton animated>
            <template #template>
              <el-skeleton-item variant="text" style="width: 60%" />
              <el-skeleton-item variant="p" style="margin-top: 12px" />
            </template>
          </el-skeleton>
        </el-card>
      </div>
      <el-empty v-else-if="projects.length === 0" :description="$t('common.welcome')" />
      <div v-else class="project-grid">
        <el-card v-for="item in projects" :key="item.id" class="project-card" shadow="hover">
          <div class="card-header">
            <div class="title-block">
              <div class="project-title">{{ item.name }}</div>
              <div class="project-desc one-line">
                {{ item.description || '-' }}
              </div>
            </div>
            <div class="chip-group">
              <el-tag size="small" type="info" effect="plain">
                {{ (item._count && item._count.Questions) || 0 }} {{ $t('projects.questions') }}
              </el-tag>
              <el-tag size="small" type="success" effect="plain">
                {{ (item._count && item._count.Datasets) || 0 }} {{ $t('projects.datasets') }}
              </el-tag>
            </div>
          </div>
          <el-divider />
          <div class="card-footer">
            <span class="last-updated">
              {{ $t('projects.lastUpdated') }}：
              {{ formatDate(item.update_at || item.create_at) }}
            </span>
            <div class="actions-icons">
              <el-tooltip :content="$t('projects.viewDetails')" placement="top">
                <el-icon @click="viewProject(item)" class="icon-btn">
                  <View />
                </el-icon>
              </el-tooltip>
              <el-tooltip :content="$t('projects.delete')" placement="top">
                <el-icon @click="confirmDelete(item)" class="icon-btn danger">
                  <Delete />
                </el-icon>
              </el-tooltip>
            </div>
          </div>
        </el-card>
      </div>
    </section>

    <el-dialog v-model="createVisible" :title="$t('common.createProject')" width="460px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item prop="name" :label="$t('common.projectName')">
          <el-input v-model="form.name" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item prop="description" :label="$t('common.projectDesc')">
          <el-input
            v-model="form.description"
            type="textarea"
            rows="3"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item :label="$t('common.reuseConfig')">
          <el-select
            v-model="form.reuseConfigFrom"
            clearable
            filterable
            :placeholder="$t('common.reusePlaceholder')"
          >
            <el-option
              v-for="item in projects"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="creating" @click="submitCreate">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Search, View, Delete } from '@element-plus/icons-vue';
import { createProject, fetchProjects, deleteProject } from '../api/project';

const router = useRouter();
const createVisible = ref(false);
const creating = ref(false);
const projects = ref([]);
const loading = ref(true);
const skeletonCount = 6;
const formRef = ref(null);
const form = reactive({
  name: '',
  description: '',
  reuseConfigFrom: '',
});

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
};

const openCreate = () => {
  createVisible.value = true;
};

const submitCreate = () => {
  formRef.value?.validate(async (valid) => {
    if (!valid) return;
    try {
      creating.value = true;
      const payload = {
        name: form.name,
        description: form.description,
      };
      if (form.reuseConfigFrom) {
        payload.reuseConfigFrom = form.reuseConfigFrom;
      }
      await createProject(payload);
      ElMessage.success('创建成功');
      createVisible.value = false;
      form.name = '';
      form.description = '';
      form.reuseConfigFrom = '';
      loadProjects();
    } catch (error) {
      // 错误已在拦截器提示
    } finally {
      creating.value = false;
    }
  });
};

const loadProjects = async () => {
  try {
    const data = await fetchProjects();
    projects.value = Array.isArray(data) ? data : data?.records || [];
  } catch (error) {
    projects.value = [];
  } finally {
    loading.value = false;
  }
};

const formatDate = (value) => {
  if (!value) return '--';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? '--' : d.toLocaleDateString('zh-CN');
};

const viewProject = (item) => {
  router.push({ name: 'project-overview', params: { projectId: item.id } });
};

const confirmDelete = (item) => {
  ElMessageBox.confirm(
    `${item.name}`,
    '删除项目',
    {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    },
  )
    .then(async () => {
      await deleteProject(item.id);
      ElMessage.success('删除成功');
      loadProjects();
    })
    .catch(() => {});
};
loadProjects();
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 1180px;
  margin: 0 auto;
}

.hero {
  padding: 40px 48px;
  border-radius: 20px;
  background: radial-gradient(circle at top left, #eef2ff 0, #e0f7ff 45%, #ffffff 100%);
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
}

.subtitle {
  margin: 8px 0 20px;
  color: #606266;
}

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.project-section {
  background: var(--el-bg-color-overlay);
  border-radius: 16px;
  padding: 20px 20px 18px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.project-card {
  min-height: 160px;
  border-radius: 14px;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.project-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.title-block {
  flex: 1;
  min-width: 0;
}

.project-title {
  font-weight: 600;
  margin-bottom: 6px;
  font-size: 16px;
}

.project-desc {
  color: #606266;
  font-size: 13px;
}

.project-desc.one-line {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chip-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}

.last-updated {
  font-size: 12px;
  color: #909399;
}

.actions-icons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.icon-btn {
  cursor: pointer;
  color: #409eff;
}

.icon-btn.danger {
  color: #f56c6c;
}

:deep(.el-dialog__body) {
  padding-top: 10px;
}

@media (max-width: 768px) {
  .hero {
    padding: 24px 20px;
  }
  .home {
    padding: 0 10px;
  }
}
</style>

