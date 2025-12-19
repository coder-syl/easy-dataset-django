<template>
  <div class="tasks-view">
    <el-card shadow="never" class="tasks-header">
      <div class="header-content">
        <div class="header-title">
          <el-icon class="title-icon"><List /></el-icon>
          <h2>{{ $t('tasks.title', '任务管理') }}</h2>
        </div>
        <TaskFilters
          :status-filter="statusFilter"
          :type-filter="typeFilter"
          :loading="loading"
          @update:status-filter="statusFilter = $event"
          @update:type-filter="typeFilter = $event"
          @refresh="fetchTasks"
        />
      </div>
    </el-card>

    <TasksTable
      :tasks="tasks"
      :loading="loading"
      :page="page"
      :rows-per-page="rowsPerPage"
      :total-count="totalCount"
      @abort-task="handleAbortTask"
      @delete-task="handleDeleteTask"
      @page-change="handlePageChange"
      @size-change="handleSizeChange"
    />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ElMessage, ElMessageBox } from 'element-plus';
import { List } from '@element-plus/icons-vue';
import { fetchTaskList, deleteTask, updateTask } from '@/api/task';
import TaskFilters from '@/components/tasks/TaskFilters.vue';
import TasksTable from '@/components/tasks/TasksTable.vue';

const route = useRoute();
const { t } = useI18n();

const projectId = route.params.projectId;

// 状态管理
const loading = ref(false);
const tasks = ref([]);
const statusFilter = ref('all');
const typeFilter = ref('all');

// 分页相关状态
const page = ref(0);
const rowsPerPage = ref(10);
const totalCount = ref(0);

let refreshIntervalId = null;

// 获取任务列表
const fetchTasks = async () => {
  if (!projectId) return;

  try {
    loading.value = true;
    
    // 构建查询参数
    const params = {
      page: page.value + 1, // Django 使用 1-based 分页
      pageSize: rowsPerPage.value, // Django 使用 pageSize 参数
    };

    if (statusFilter.value !== 'all') {
      params.status = statusFilter.value;
    }

    if (typeFilter.value !== 'all') {
      params.taskType = typeFilter.value;
    }

    const response = await fetchTaskList(projectId, params);
    
    // HTTP 拦截器已经返回了 res.data，所以 response 就是 data 对象
    // Django格式: {code: 0, data: {data: [...], total: ...}}
    // HTTP 拦截器处理后: {data: [...], total: ...}
    let tasksList = [];
    let total = 0;
    
    // response 已经是 data 对象（HTTP 拦截器处理后的结果）
    if (response) {
      // 如果 response.data 是数组，说明是嵌套的数据结构 {data: [...], total: ...}
      if (Array.isArray(response.data)) {
        tasksList = response.data;
        total = response.total || 0;
      }
      // 如果 response 本身是数组（不太可能，但兼容处理）
      else if (Array.isArray(response)) {
        tasksList = response;
        total = response.length;
      }
      // 如果 response.data.data 是数组，说明是更深层的嵌套
      else if (response.data && Array.isArray(response.data.data)) {
        tasksList = response.data.data;
        total = response.data.total || response.total || 0;
      }
    }
    
    tasks.value = tasksList;
    totalCount.value = total;
    
    console.log('任务列表数据:', { 
      response, 
      tasksList: tasksList.length, 
      total, 
      firstTask: tasksList[0] 
    });
  } catch (error) {
    console.error('获取任务列表失败:', error);
    ElMessage.error(t('tasks.fetchFailed', '获取任务列表失败'));
    tasks.value = [];
  } finally {
    loading.value = false;
  }
};

// 初始化和过滤器变更时获取任务列表
onMounted(() => {
  fetchTasks();

  // 定时刷新处理中的任务（每5秒）
  refreshIntervalId = setInterval(() => {
    if (statusFilter.value === 'all' || statusFilter.value === '0') {
      fetchTasks();
    }
  }, 5000);
});

onUnmounted(() => {
  if (refreshIntervalId) {
    clearInterval(refreshIntervalId);
  }
});

// 监听过滤器和分页变化
watch([statusFilter, typeFilter, page, rowsPerPage], () => {
  fetchTasks();
}, { immediate: false });

// 删除任务
const handleDeleteTask = async (taskId) => {
  try {
    await ElMessageBox.confirm(
      t('tasks.confirmDelete', '确定要删除该任务吗？'),
      t('common.confirmDelete', '确认删除'),
      {
        confirmButtonText: t('common.confirm', '确认'),
        cancelButtonText: t('common.cancel', '取消'),
        type: 'warning',
      }
    );

    await deleteTask(projectId, taskId);
    ElMessage.success(t('tasks.deleteSuccess', '删除成功'));
    fetchTasks();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error);
      ElMessage.error(error?.message || t('tasks.deleteFailed', '删除失败'));
    }
  }
};

// 中断任务
const handleAbortTask = async (taskId) => {
  try {
    await ElMessageBox.confirm(
      t('tasks.confirmAbort', '确定要中断该任务吗？'),
      t('common.confirm', '确认'),
      {
        confirmButtonText: t('common.confirm', '确认'),
        cancelButtonText: t('common.cancel', '取消'),
        type: 'warning',
      }
    );

    await updateTask(projectId, taskId, {
      status: 3, // 3 表示已中断
      detail: t('tasks.status.aborted', '任务已中断'),
      note: t('tasks.status.aborted', '任务已中断'),
    });

    ElMessage.success(t('tasks.abortSuccess', '任务已中断'));
    fetchTasks();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('中断任务失败:', error);
      ElMessage.error(error?.message || t('tasks.abortFailed', '中断失败'));
    }
  }
};

// 分页参数更改处理
const handlePageChange = (newPage) => {
  page.value = newPage;
};

const handleSizeChange = (newSize) => {
  rowsPerPage.value = newSize;
  page.value = 0;
};
</script>

<style scoped>
.tasks-view {
  padding: 20px;
  /* max-width: 1400px; */
  margin: 0 auto;
}

.tasks-header {
  margin-bottom: 16px;
}

.tasks-header :deep(.el-card__body) {
  padding: 16px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 24px;
}

.header-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
</style>

