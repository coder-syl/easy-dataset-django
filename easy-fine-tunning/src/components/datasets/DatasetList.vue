<template>
  <div class="dataset-list">
    <el-table
      :data="datasets"
      style="width: 100%"
      @row-click="(row) => $emit('view-details', row.id)"
      :empty-text="$t('datasets.noData', '暂无数据')"
    >
      <el-table-column type="selection" width="55" :selectable="() => true">
        <template #header>
          <el-checkbox
            :model-value="isAllSelected"
            :indeterminate="isIndeterminate"
            @change="handleSelectAllChange"
          />
        </template>
        <template #default="{ row }">
          <el-checkbox
            :model-value="selectedIds.includes(row.id)"
            @change="(val) => $emit('select-item', row.id)"
            @click.stop
          />
        </template>
      </el-table-column>
      <el-table-column :label="$t('datasets.question', '问题')" min-width="300" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="question-cell">
            <div class="question-text">{{ row.question }}</div>
            <el-tag v-if="row.confirmed" size="small" type="success" class="confirmed-tag">
              {{ $t('datasets.confirmed', '已确认') }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column :label="$t('datasets.rating', '评分')" min-width="130" align="center">
        <template #default="{ row }">
          <div class="rating-cell">
            <RatingChip :score="row.score || 0" />
          </div>
        </template>
      </el-table-column>
      <el-table-column :label="$t('datasets.model', '模型')" min-width="120" align="center">
        <template #default="{ row }">
          <div class="model-cell">
            <el-tag size="small" type="info" class="model-tag">{{ row.model }}</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column :label="$t('datasets.domainTag', '领域标签')" min-width="140" align="center">
        <template #default="{ row }">
          <div class="tag-cell">
            <el-tag v-if="row.question_label" size="small" type="primary" class="tag-tag">
              {{ row.question_label }}
            </el-tag>
            <span v-else class="no-tag">{{ $t('datasets.noTag', '无标签') }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column :label="$t('datasets.createdAt', '创建时间')" width="120" align="center">
        <template #default="{ row }">
          <span class="create-time">
            {{ formatDate(row.create_at) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('common.actions', '操作')" width="120" fixed="right">
        <template #default="{ row }">
          <div class="action-buttons" @click.stop>
            <el-button
              link
              type="primary"
              :icon="View"
              @click="$emit('view-details', row.id)"
            />
            <el-button
              link
              type="warning"
              :icon="DataAnalysis"
              :loading="evaluatingIds.includes(row.id)"
              :disabled="evaluatingIds.includes(row.id)"
              @click="$emit('evaluate', row)"
            />
            <el-button
              link
              type="danger"
              :icon="Delete"
              @click="$emit('delete', row)"
            />
          </div>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <div class="pagination-controls">
        <el-pagination
          :current-page="page"
          :page-size="rowsPerPage"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
        <div class="pagination-info">
          <span>
            {{ total > 0
              ? $t('common.totalItems', { count: total }) || `共 ${total} 条`
              : $t('common.currentPageItems', { count: datasets.length }) || `当前页 ${datasets.length} 条`
            }}
          </span>
          <span v-if="pageCount > 0">
            {{ $t('common.pageInfo', { current: page, total: pageCount }) || `第 ${page}/${pageCount} 页` }}
          </span>
        </div>
        <div class="jump-to">
          <span>{{ $t('common.jumpTo') || '跳转到' }}:</span>
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
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { View, Delete, DataAnalysis } from '@element-plus/icons-vue';
import RatingChip from './RatingChip.vue';

const props = defineProps({
  datasets: {
    type: Array,
    default: () => []
  },
  page: {
    type: Number,
    default: 1
  },
  rowsPerPage: {
    type: Number,
    default: 10
  },
  total: {
    type: Number,
    default: 0
  },
  selectedIds: {
    type: Array,
    default: () => []
  },
  evaluatingIds: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits([
  'view-details',
  'delete',
  'evaluate',
  'select-all',
  'select-item',
  'page-change',
  'rows-per-page-change'
]);

// 移除未使用的导入

const { t } = useI18n();

const localCurrentPage = computed({
  get() {
    return props.page;
  },
  set(val) {
    emit('page-change', val);
  }
});

const jumpPage = computed({
  get() {
    return props.page;
  },
  set(val) {
    // 只更新本地输入，实际跳转在 handleJumpToPage 中处理
  }
});

// 计算全选状态
const isAllSelected = computed(() => {
  return props.datasets.length > 0 && props.selectedIds.length === props.total;
});

// 计算半选状态
const isIndeterminate = computed(() => {
  return props.selectedIds.length > 0 && props.selectedIds.length < props.total;
});

// 计算总页数
const pageCount = computed(() => {
  return props.total > 0 ? Math.ceil(props.total / props.rowsPerPage) : 0;
});

// 处理全选/取消全选
const handleSelectAllChange = (checked) => {
  emit('select-all', checked);
};

const handleSizeChange = (val) => {
  emit('rows-per-page-change', val);
};

const handleCurrentChange = (val) => {
  emit('page-change', val);
};

const handleJumpToPage = () => {
  if (pageCount.value <= 0) return;
  const target = Math.min(Math.max(Number(jumpPage.value) || 1, 1), pageCount.value);
  emit('page-change', target);
};

const formatDate = (dateStr) => {
  if (!dateStr) return t('datasets.invalidDate', '无效日期');
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN');
  } catch {
    return t('datasets.invalidDate', '无效日期');
  }
};
</script>

<style scoped>
.dataset-list {
  margin-top: 16px;
}

.question-cell {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.question-text {
  word-break: break-word;
  white-space: normal;
  line-height: 1.5;
  max-height: 3em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.confirmed-tag {
  width: fit-content;
  margin-top: 4px;
}

.no-tag {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
}

.create-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.rating-cell,
.model-cell,
.tag-cell {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  text-align: center;
}

.model-tag,
.tag-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap !important;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  word-break: keep-all;
}

.model-tag :deep(.el-tag__content),
.tag-tag :deep(.el-tag__content) {
  white-space: nowrap !important;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
  max-width: 100%;
  word-break: keep-all;
  text-align: center;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 24px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 16px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.pagination-info {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.jump-to {
  display: flex;
  align-items: center;
  gap: 8px;
}

.jump-to .el-input-number {
  width: 80px;
}
</style>

