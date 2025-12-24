<template>
  <div class="image-dataset-list">
    <el-table
      :data="datasets"
      style="width: 100%"
      @row-click="(row) => $emit('view-details', row.id)"
      @selection-change="onTableSelectionChange"
      :empty-text="$t('imageDatasets.noData', '暂无数据')"
      border
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
            :model-value="selectedIds.some(id => String(id) === String(row.id))"
            @change="() => selectItem(row.id)"
            @click.stop
          />
        </template>
      </el-table-column>

      <!-- 图片列 -->
      <el-table-column :label="$t('images.image', '图片')" width="100" align="center">
        <template #default="{ row }">
          <div class="image-cell">
            <el-image
              :src="row.base64 || getImageUrl(row)"
              :alt="row.imageName || row.image_name"
              fit="cover"
              class="thumbnail-image"
              :preview-src-list="[row.base64 || getImageUrl(row)]"
              :initial-index="0"
              preview-teleported
            />
          </div>
        </template>
      </el-table-column>

      <!-- 问题列 -->
      <el-table-column :label="$t('datasets.question', '问题')" min-width="180">
        <template #default="{ row }">
          <div class="question-cell">
            <div class="question-text">{{ row.question }}</div>
            <el-tag v-if="row.confirmed" size="small" type="success" class="confirmed-tag">
              {{ $t('datasets.confirmed', '已确认') }}
            </el-tag>
          </div>
        </template>
      </el-table-column>

      <!-- 答案类型列 -->
      <el-table-column :label="$t('imageDatasets.answerType', '答案类型')" width="100" align="center">
        <template #default="{ row }">
          <el-tag
            :type="getAnswerTypeColor(row.answerType || row.answer_type)"
            size="small"
            effect="plain"
          >
            {{ getAnswerTypeLabel(row.answerType || row.answer_type) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 评分列 -->
      <el-table-column :label="$t('datasets.rating', '评分')" width="150" align="center">
        <template #default="{ row }">
          <div class="rating-cell">
            <RatingChip :score="row.score || 0" />
          </div>
        </template>
      </el-table-column>

      <!-- 图片名称列 -->
      <el-table-column :label="$t('images.imageName', '图片名称')" min-width="120">
        <template #default="{ row }">
          <span class="image-name">{{ row.imageName || row.image_name || '-' }}</span>
        </template>
      </el-table-column>

      <!-- 创建时间列 -->
      <el-table-column :label="$t('datasets.createdAt', '创建时间')" width="110" align="center">
        <template #default="{ row }">
          <span class="create-time">
            {{ formatDate(row.create_at || row.createAt) }}
          </span>
        </template>
      </el-table-column>

      <!-- 操作列 -->
      <el-table-column :label="$t('common.actions', '操作')" width="220" fixed="right">
        <template #default="{ row }">
          <div class="action-buttons" @click.stop>
            <el-tooltip :content="$t('common.view')">
              <el-button
                class="table-action-button"
                size="small"
                :icon="View"
                @click="$emit('view-details', row.id)"
              />
            </el-tooltip>
            <el-tooltip :content="$t('imageDatasets.evaluate', '评估')">
              <el-button
                class="table-action-button"
                size="small"
                :icon="DataAnalysis"
                :loading="evaluatingIds.includes(row.id)"
                :disabled="evaluatingIds.includes(row.id)"
                @click="$emit('evaluate', row)"
              />
            </el-tooltip>
            <el-tooltip :content="$t('common.delete')">
              <el-button
                class="table-action-button"
                size="small"
                type="danger"
                :icon="Delete"
                @click="$emit('delete', row)"
              />
            </el-tooltip>
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
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { View, Delete, DataAnalysis } from '@element-plus/icons-vue';
import RatingChip from '@/components/datasets/RatingChip.vue';

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
  'selection-change',
  'page-change',
  'rows-per-page-change'
]);

const { t } = useI18n();

const jumpPage = ref(props.page);

// 监听 page 变化，同步 jumpPage
watch(() => props.page, (val) => {
  jumpPage.value = val;
});

// 计算全选状态
const isAllSelected = computed(() => {
  return props.datasets.length > 0 && props.datasets.every((d) =>
    props.selectedIds.some((id) => String(id) === String(d.id))
  );
});

// 计算半选状态
const isIndeterminate = computed(() => {
  const anySelectedOnPage = props.datasets.some((d) =>
    props.selectedIds.some((id) => String(id) === String(d.id))
  );
  return anySelectedOnPage && !isAllSelected.value;
});

// 计算总页数
const pageCount = computed(() => {
  return props.total > 0 ? Math.ceil(props.total / props.rowsPerPage) : 0;
});

// 处理全选/取消全选
const handleSelectAllChange = (checked) => {
  try {
    // eslint-disable-next-line no-console
    console.debug('[ImageDatasetList] header select-all change:', checked);
  } catch (e) {}
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

// 获取答案类型颜色
const getAnswerTypeColor = (answerType) => {
  const type = answerType || 'text';
  const colorMap = {
    text: 'info',
    label: 'primary',
    custom_format: 'warning'
  };
  return colorMap[type] || 'info';
};

// 获取答案类型标签
const getAnswerTypeLabel = (answerType) => {
  const type = answerType || 'text';
  const labelMap = {
    text: t('imageDatasets.answerTypeText', '文本'),
    label: t('imageDatasets.answerTypeLabel', '标签'),
    custom_format: t('imageDatasets.answerTypeCustom', '自定义格式')
  };
  return labelMap[type] || type;
};

// 获取图片 URL
const getImageUrl = (row) => {
  const imageName = row.imageName || row.image_name;
  if (!imageName) return '/placeholder.png';
  // 如果有 base64，直接返回
  if (row.base64) return row.base64;
  // 否则返回图片路径（需要根据实际 API 路径调整）
  return `/api/projects/${row.projectId || ''}/images/${row.imageId || row.image_id}/`;
};

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return t('datasets.invalidDate', '无效日期');
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN');
  } catch {
    return t('datasets.invalidDate', '无效日期');
  }
};

// 处理行选中（代理到父组件并打印调试日志）
const selectItem = (datasetId) => {
  try {
    // eslint-disable-next-line no-console
    console.debug('[ImageDatasetList] select-item clicked:', datasetId);
  } catch (e) {}
  emit('select-item', String(datasetId));
};

// Element Plus table native selection-change handler
const onTableSelectionChange = (selection) => {
  try {
    // eslint-disable-next-line no-console
    console.debug('[ImageDatasetList] table selection-change:', Array.isArray(selection) ? selection.map(s => s.id) : selection);
  } catch (e) {}
  const ids = Array.isArray(selection) ? selection.map((r) => String(r.id || r._id || r.id_str || '')) : [];
  emit('selection-change', ids);
};

</script>

<style scoped>
.image-dataset-list {
  margin-top: 16px;
}

/* 表格单元格样式优化 */
.image-dataset-list :deep(.el-table td) {
  padding: 12px 8px;
}

.image-dataset-list :deep(.el-table th) {
  padding: 12px 8px;
}

/* 问题列和图片名称列增加左右 padding */
.image-dataset-list :deep(.el-table td .question-cell),
.image-dataset-list :deep(.el-table td .image-name) {
  padding-left: 4px;
  padding-right: 4px;
}

.image-cell {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 70px;
  padding: 4px;
}

.thumbnail-image {
  width: 100%;
  height: 70px;
  max-width: 90px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
}

.question-cell {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 0;
}

.question-text {
  word-break: break-word;
  white-space: normal;
  line-height: 1.6;
  color: var(--el-text-color-primary);
  font-size: 14px;
}

.confirmed-tag {
  width: fit-content;
  margin-top: 4px;
}

.rating-cell {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding: 4px 0;
}

.image-name {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  word-break: break-word;
  white-space: normal;
  line-height: 1.5;
  display: block;
  padding: 4px 0;
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
  align-items: center;
  flex-wrap: nowrap;
  white-space: nowrap;
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

/* Unified action button style for table rows */
.table-action-button {
  padding: 4px;
  min-width: 34px;
  border-radius: 4px;
}
</style>

