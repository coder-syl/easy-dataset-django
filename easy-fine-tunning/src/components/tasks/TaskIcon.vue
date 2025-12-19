<template>
  <div class="task-icon-wrapper" @click="handleOpenTaskList">
    <el-tooltip :content="tooltipText" placement="bottom" :teleported="false">
      <el-badge :value="pendingTasksCount" :hidden="pendingTasksCount === 0" :max="99">
        <el-button
          :icon="pendingTasksCount > 0 ? Loading : List"
          circle
          size="small"
          :loading="false"
          class="task-icon-button"
          :disabled="false"
        />
      </el-badge>
    </el-tooltip>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { List, Loading } from '@element-plus/icons-vue';
import { fetchTaskList } from '@/api/task';

const props = defineProps({
  projectId: {
    type: String,
    required: true,
  },
});

const router = useRouter();
const { t } = useI18n();

const tasks = ref([]);
const polling = ref(false);
let intervalId = null;

// 获取项目的未完成任务列表
const fetchPendingTasks = async () => {
  if (!props.projectId) return;

  try {
    const response = await fetchTaskList(props.projectId, { status: 0 });
    const data = response?.data || response;
    
    // Django格式: {code: 0, data: {data: [...], total: ...}}
    const tasksList = Array.isArray(data?.data) 
      ? data.data 
      : Array.isArray(data) 
      ? data 
      : [];
    
    tasks.value = tasksList;
    
    // 检查是否有文件处理任务正在进行
    const hasActiveFileTask = tasksList.some(
      task => (task.projectId === props.projectId || task.project_id === props.projectId) && 
              (task.taskType === 'file-processing' || task.task_type === 'file-processing')
    );
    
    // 可以在这里设置全局状态，通知其他组件
    // 例如：emit('file-processing-changed', hasActiveFileTask);
  } catch (error) {
    console.error('获取任务列表失败:', error);
    tasks.value = [];
  }
};

// 初始化时获取任务列表并启动轮询
onMounted(() => {
  if (props.projectId) {
    fetchPendingTasks();

    // 启动轮询，每10秒轮询一次
    intervalId = setInterval(() => {
      fetchPendingTasks();
    }, 10000);

    polling.value = true;
  }
});

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId);
    intervalId = null;
  }
  polling.value = false;
});

// 监听 projectId 变化
watch(() => props.projectId, (newId) => {
  if (intervalId) {
    clearInterval(intervalId);
  }
  
  if (newId) {
    fetchPendingTasks();
    intervalId = setInterval(() => {
      fetchPendingTasks();
    }, 10000);
    polling.value = true;
  } else {
    polling.value = false;
  }
});

// 打开任务列表页面
const handleOpenTaskList = (e) => {
  e?.stopPropagation?.();
  e?.preventDefault?.();
  if (props.projectId) {
    console.log('打开任务列表页面:', props.projectId);
    router.push(`/projects/${props.projectId}/tasks`).catch(err => {
      console.error('路由跳转失败:', err);
    });
  } else {
    console.warn('projectId 为空，无法跳转到任务列表');
  }
};

// 计算待处理任务数量
const pendingTasksCount = computed(() => {
  if (!Array.isArray(tasks.value)) return 0;
  return tasks.value.filter(task => task.status === 0).length;
});

// 悬停提示文本
const tooltipText = computed(() => {
  if (!Array.isArray(tasks.value)) {
    return t('tasks.completed', '所有任务已完成');
  }
  
  const pendingCount = pendingTasksCount.value;
  
  if (pendingCount > 0) {
    return t('tasks.pending', { count: pendingCount }, `有 ${pendingCount} 个任务处理中`);
  }
  
  return t('tasks.completed', '所有任务已完成');
});
</script>

<style scoped>
.task-icon-wrapper {
  display: inline-block;
  cursor: pointer;
  margin-left: 8px;
}

.task-icon-button {
  cursor: pointer;
}

/* 确保 badge 和 button 都可以点击 */
:deep(.el-badge) {
  cursor: pointer;
}

:deep(.el-badge__content) {
  pointer-events: none; /* badge 内容不阻止点击 */
}

/* 确保 tooltip 不阻止点击 */
:deep(.el-tooltip__trigger) {
  cursor: pointer;
}
</style>

