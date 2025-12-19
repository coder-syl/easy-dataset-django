<template>
  <div class="template-list-view">
    <div v-if="loading" class="loading-wrapper">
      <el-text type="info">{{ $t('common.loading') }}</el-text>
    </div>
    <el-empty
      v-else-if="!templatesList.length"
      :description="$t('questions.template.noTemplates') || '暂无问题模板，点击创建按钮添加'"
    />
    <el-table
      v-else
      :data="templatesList"
      border
      style="width: 100%"
    >
      <el-table-column :label="$t('questions.template.question')" min-width="260">
        <template #default="{ row }">
          <span class="template-question">{{ row.question }}</span>
        </template>
      </el-table-column>

      <el-table-column :label="$t('questions.template.sourceType.label')" width="160">
        <template #default="{ row }">
          <el-tag
            size="small"
            type="info"
            effect="plain"
          >
            {{ getSourceTypeLabel(row.source_type) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column :label="$t('questions.template.answerType.label')" width="160">
        <template #default="{ row }">
          <el-tag size="small" effect="plain">
            {{ getAnswerTypeLabel(row.answer_type) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column :label="$t('questions.template.description')" min-width="220">
        <template #default="{ row }">
          <span class="template-description">
            {{ row.description || '-' }}
          </span>
        </template>
      </el-table-column>

      <el-table-column :label="$t('questions.template.used')" width="120">
        <template #default="{ row }">
          <el-tag
            v-if="(row.usage_count || 0) > 0"
            size="small"
            type="success"
            effect="plain"
          >
            {{ row.usage_count }}
          </el-tag>
          <span v-else class="usage-zero">0</span>
        </template>
      </el-table-column>

      <el-table-column :label="$t('common.actions')" width="160" fixed="right">
        <template #default="{ row }">
          <div class="actions">
            <el-tooltip :content="$t('common.edit')">
              <el-button
                size="small"
                :icon="Edit"
                @click="$emit('edit', row)"
              />
            </el-tooltip>
            <el-tooltip :content="$t('questions.template.deleteConfirm') || $t('common.confirmDelete')">
              <el-button
                size="small"
                type="danger"
                :icon="Delete"
                :disabled="(row.usage_count || 0) > 0"
                @click="$emit('delete', row.id)"
              />
            </el-tooltip>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { Edit, Delete } from '@element-plus/icons-vue';

const props = defineProps({
  templates: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
});

defineEmits(['edit', 'delete']);

const { t } = useI18n();

const templatesList = computed(() => (Array.isArray(props.templates) ? props.templates : []));

const getAnswerTypeLabel = (type) => {
  const labels = {
    text: t('questions.template.answerType.text'),
    label: t('questions.template.answerType.tags'),
    custom_format: t('questions.template.answerType.customFormat')
  };
  return labels[type] || type;
};

const getSourceTypeLabel = (type) => {
  const labels = {
    image: t('questions.template.sourceType.image'),
    text: t('questions.template.sourceType.text')
  };
  return labels[type] || type;
};
</script>

<style scoped>
.template-list-view {
  padding: 16px;
}

.loading-wrapper {
  padding: 16px;
  text-align: center;
}

.template-question {
  display: inline-block;
  max-width: 320px;
  font-size: 14px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.template-description {
  display: inline-block;
  max-width: 260px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.usage-zero {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}
</style>

