<template>
  <div class="tasks-table">
    <el-card shadow="never">
      <el-table
        :data="tasks"
        v-loading="loading"
        style="width: 100%"
        :default-expand-all="false"
        :row-key="(row) => row.id"
      >
        <el-table-column type="expand" width="50">
          <template #default="{ row }">
            <TaskDetail :task="row" />
          </template>
        </el-table-column>

        <el-table-column :label="$t('tasks.table.type', '任务类型')" width="150">
          <template #default="{ row }">
            {{ getLocalizedTaskType(row.taskType || row.task_type || '') }}
          </template>
        </el-table-column>

        <el-table-column :label="$t('tasks.table.status', '状态')" width="120">
          <template #default="{ row }">
            <TaskStatusChip :status="row.status" />
          </template>
        </el-table-column>

        <el-table-column :label="$t('tasks.table.progress', '进度')" width="200">
          <template #default="{ row }">
            <TaskProgress :task="row" />
          </template>
        </el-table-column>

        <el-table-column :label="$t('tasks.table.success', '成功')" width="80" align="center">
          <template #default="{ row }">
            {{ (row.completedCount || row.completed_count || 0) - (row.errorCount || row.error_count || 0) }}
          </template>
        </el-table-column>

        <el-table-column :label="$t('tasks.table.failed', '失败')" width="80" align="center">
          <template #default="{ row }">
            {{ row.errorCount || row.error_count || 0 }}
          </template>
        </el-table-column>

        <el-table-column :label="$t('tasks.table.createTime', '创建时间')" width="150">
          <template #default="{ row }">
            {{ formatDate(row.createAt || row.create_at) }}
          </template>
        </el-table-column>

        <el-table-column :label="$t('tasks.table.duration', '运行时间')" width="120">
          <template #default="{ row }">
            {{ calculateDuration(row.startTime || row.start_time, row.endTime || row.end_time) }}
          </template>
        </el-table-column>

        <el-table-column :label="$t('tasks.table.model', '模型')" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            {{ parseModelInfo(row.modelInfo || row.model_info) }}
          </template>
        </el-table-column>

        <el-table-column :label="$t('tasks.table.actions', '操作')" width="100" align="right" fixed="right">
          <template #default="{ row }">
            <TaskActions :task="row" @abort="$emit('abort-task', $event)" @delete="$emit('delete-task', $event)" />
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && (!tasks || tasks.length === 0)" class="empty-state">
        <el-empty :description="$t('tasks.empty', '暂无任务')" />
      </div>

      <div v-if="tasks && tasks.length > 0" class="pagination-wrapper">
        <div class="pagination-controls">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="currentPageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalCount"
            layout="sizes, prev, pager, next"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
          <div class="pagination-info">
            <span>
              {{
                totalCount > 0
                  ? t('common.totalItems', { count: totalCount }) || `共 ${totalCount} 条`
                  : t('common.currentPageItems', { count: tasks.length }) || `当前页 ${tasks.length} 条`
              }}
            </span>
            <span v-if="pageCount > 0" class="page-info">
              {{ t('common.pageInfo', { current: currentPage, total: pageCount }) || `第 ${currentPage}/${pageCount} 页` }}
            </span>
          </div>
          <div class="jump-to">
            <span>{{ t('common.jumpTo') || '跳转到' }}:</span>
            <el-input-number
              v-model="jumpPage"
              :min="1"
              :max="pageCount || 1"
              size="small"
              controls-position="right"
              @keyup.enter="handleJumpToPage"
            />
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { formatDistanceToNow } from 'date-fns';
import { zhCN, enUS } from 'date-fns/locale';
import TaskStatusChip from './TaskStatusChip.vue';
import TaskProgress from './TaskProgress.vue';
import TaskActions from './TaskActions.vue';
import TaskDetail from './TaskDetail.vue';

const props = defineProps({
  tasks: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  page: {
    type: Number,
    default: 0,
  },
  rowsPerPage: {
    type: Number,
    default: 10,
  },
  totalCount: {
    type: Number,
    default: 0,
  },
});

const emit = defineEmits(['abort-task', 'delete-task', 'page-change', 'size-change']);

const { t } = useI18n();

// 当前页（1-based，和其它页面保持一致）
const currentPage = computed({
  get: () => props.page + 1,
  set: (val) => emit('page-change', val - 1),
});

// 每页条数
const currentPageSize = computed({
  get: () => props.rowsPerPage,
  set: (val) => {
    emit('size-change', val);
  },
});

// 总页数
const pageCount = computed(() => {
  return props.totalCount > 0 ? Math.ceil(props.totalCount / props.rowsPerPage) : 0;
});

// 跳转页码（与其它页面一致的交互）
const jumpPage = computed({
  get() {
    return currentPage.value;
  },
  set(val) {
    // 只更新本地输入，真正跳转在 handleJumpToPage 中处理
  },
});

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return formatDistanceToNow(date, {
      addSuffix: true,
      locale: locale.value === 'zh' ? zhCN : enUS,
    });
  } catch (error) {
    return '-';
  }
};

// 计算任务运行时间
const calculateDuration = (startTimeStr, endTimeStr) => {
  if (!startTimeStr || !endTimeStr) return '-';

  try {
    const startTime = new Date(startTimeStr);
    const endTime = new Date(endTimeStr);
    const duration = endTime - startTime;
    const seconds = Math.floor(duration / 1000);

    if (seconds < 60) {
      return t('tasks.duration.seconds', { seconds }, `${seconds} 秒`);
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return t('tasks.duration.minutes', { minutes, seconds: remainingSeconds }, `${minutes} 分 ${remainingSeconds} 秒`);
    } else {
      const hours = Math.floor(seconds / 3600);
      const remainingMinutes = Math.floor((seconds % 3600) / 60);
      return t('tasks.duration.hours', { hours, minutes: remainingMinutes }, `${hours} 小时 ${remainingMinutes} 分钟`);
    }
  } catch (error) {
    console.error('计算运行时间出错:', error);
    return '-';
  }
};

// 解析模型信息
const parseModelInfo = (modelInfo) => {
  if (modelInfo && typeof modelInfo === 'object') {
    return modelInfo.modelName || modelInfo.model_name || modelInfo.name || '-';
  }

  if (typeof modelInfo === 'string') {
    try {
      const parsedModel = JSON.parse(modelInfo);
      if (parsedModel && typeof parsedModel === 'object') {
        return parsedModel.modelName || parsedModel.model_name || parsedModel.name || '-';
      }
      return modelInfo;
    } catch (error) {
      return modelInfo || '-';
    }
  }

  return '-';
};

// 任务类型本地化
const getLocalizedTaskType = (taskType) => {
  if (!taskType) return '-';
  
  // 直接使用 t 函数，vue-i18n 会自动处理 fallback
  const key = `tasks.types.${taskType}`;
  const translated = t(key);
  
  // 如果翻译结果和 key 相同，说明没有找到翻译
  // 这种情况下返回原始值（但应该不会发生，因为 i18n 配置中有这些翻译）
  if (translated === key) {
    console.warn(`未找到任务类型翻译: ${taskType}, key: ${key}, 返回原始值`);
    return taskType;
  }
  
  return translated;
};

const handlePageChange = (page) => {
  emit('page-change', page - 1);
};

const handleSizeChange = (size) => {
  emit('size-change', size);
};

// 跳转到指定页
const handleJumpToPage = () => {
  if (pageCount.value <= 0) return;
  const target = Math.min(Math.max(Number(jumpPage.value) || 1, 1), pageCount.value);
  emit('page-change', target - 1);
};
</script>

<style scoped>
.tasks-table {
  margin-top: 0;
}

.pagination-wrapper {
  margin-top: 12px;
}

.tasks-table :deep(.el-card__body) {
  padding: 16px;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding: 8px 0;
  border-top: 1px solid var(--el-border-color-lighter);
}

.pagination-info {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.page-info {
  color: var(--el-text-color-secondary);
}

.jump-to {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.jump-to :deep(.el-input-number) {
  width: 120px;
}

/* 减少表格行间距 */
/* :deep(.el-table) {
  font-size: 14px;
} */

:deep(.el-table .el-table__cell) {
  padding: 18px 0;
}

:deep(.el-table th.el-table__cell) {
  padding: 10px 0;
}
</style>

