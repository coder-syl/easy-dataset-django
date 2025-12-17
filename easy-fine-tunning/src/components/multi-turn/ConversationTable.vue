<template>
  <div class="conversation-table">
    <el-table
      :data="conversations"
      style="width: 100%"
      v-loading="loading"
      :empty-text="$t('datasets.noConversations', '暂无对话')"
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
            @change="() => handleSelectOne(row.id)"
            @click.stop
          />
        </template>
      </el-table-column>
      <el-table-column :label="$t('datasets.firstQuestion', '首问')" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="question-cell">
            <div class="question-text">{{ row.question }}</div>
            <el-tag v-if="row.confirmed" size="small" type="success" class="confirmed-tag">
              {{ $t('datasets.confirmed', '已确认') }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column :label="$t('datasets.conversationScenario', '对话场景')" width="140" show-overflow-tooltip>
        <template #default="{ row }">
          <el-tag v-if="row.scenario" size="small" type="primary">
            {{ row.scenario }}
          </el-tag>
          <span v-else class="no-scenario">{{ $t('datasets.notSet', '未设置') }}</span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('datasets.conversationRounds', '对话轮数')" width="120" align="center">
        <template #default="{ row }">
          <span class="rounds-text">
            {{ row.turn_count || 0 }}/{{ row.max_turns || 0 }}
          </span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('datasets.modelUsed', '使用模型')" width="120" show-overflow-tooltip>
        <template #default="{ row }">
          <el-tag size="small" type="info">{{ row.model }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="$t('datasets.rating', '评分')" width="130" align="center">
        <template #default="{ row }">
          <RatingChip :score="row.score || 0" />
        </template>
      </el-table-column>
      <el-table-column :label="$t('datasets.createTime', '创建时间')" width="120" align="center">
        <template #default="{ row }">
          <span class="create-time">
            {{ formatDate(row.create_at) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('common.actions', '操作')" width="120" fixed="right" align="center">
        <template #default="{ row }">
          <div class="action-buttons" @click.stop>
            <el-button link type="primary" :icon="View" @click="$emit('view', row.id)" />
            <el-button link type="danger" :icon="Delete" @click="$emit('delete', row.id)" />
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
              : $t('common.currentPageItems', { count: conversations.length }) || `当前页 ${conversations.length} 条`
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
import { View, Delete } from '@element-plus/icons-vue';
import RatingChip from '@/components/datasets/RatingChip.vue';

const props = defineProps({
  conversations: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  page: {
    type: Number,
    default: 1
  },
  rowsPerPage: {
    type: Number,
    default: 20
  },
  total: {
    type: Number,
    default: 0
  },
  selectedIds: {
    type: Array,
    default: () => []
  },
  isAllSelected: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['view', 'delete', 'selection-change', 'select-all', 'page-change', 'rows-per-page-change']);

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

// 计算半选状态
const isIndeterminate = computed(() => {
  return props.selectedIds.length > 0 && !props.isAllSelected;
});

// 计算总页数
const pageCount = computed(() => {
  return props.total > 0 ? Math.ceil(props.total / props.rowsPerPage) : 0;
});

// 处理单个选择
const handleSelectOne = (conversationId) => {
  if (props.selectedIds.includes(conversationId)) {
    emit('selection-change', props.selectedIds.filter((id) => id !== conversationId));
  } else {
    emit('selection-change', [...props.selectedIds, conversationId]);
  }
};

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
.conversation-table {
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

.no-scenario {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
}

.rounds-text {
  font-size: 14px;
  color: var(--el-text-color-regular);
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

