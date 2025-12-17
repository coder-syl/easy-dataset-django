<template>
  <div class="template-list-view">
    <el-empty v-if="!loading && (!templates || templates.length === 0)" description="暂无模板" />
    <el-table v-else :data="templatesList" v-loading="loading">
      <el-table-column prop="name" label="模板名称" />
      <el-table-column prop="type" label="类型" />
      <el-table-column :label="$t('common.actions')" width="200">
        <template #default="{ row }">
          <el-button size="small" :icon="Edit" @click="$emit('edit', row)" />
          <el-button size="small" type="danger" :icon="Delete" @click="$emit('delete', row.id)" />
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed } from 'vue';
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

// 确保 templates 始终是数组
const templatesList = computed(() => {
  return Array.isArray(props.templates) ? props.templates : [];
});
</script>

<style scoped>
.template-list-view {
  padding: 16px;
}
</style>

