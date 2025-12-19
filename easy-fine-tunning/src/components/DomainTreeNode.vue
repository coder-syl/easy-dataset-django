<template>
  <div class="domain-tree-node">
    <div
      class="tree-node-item"
      :class="{ 'tree-node-root': level === 0, 'tree-node-expanded': isExpanded && hasChildren }"
      @click="toggleExpand"
    >
      <div class="tree-node-content">
        <span class="tree-node-label">{{ node.label }}</span>
      </div>
      <div class="tree-node-actions" @click.stop>
        <el-dropdown trigger="click" @command="handleCommand">
          <el-button text circle size="small" @click.stop>
            <el-icon><MoreVert /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="edit">
                <el-icon><Edit /></el-icon>
                {{ t('textSplit.editTag', '编辑标签') }}
              </el-dropdown-item>
              <el-dropdown-item command="delete" divided>
                <el-icon><Delete /></el-icon>
                {{ t('textSplit.deleteTag', '删除标签') }}
              </el-dropdown-item>
              <el-dropdown-item v-if="level === 0" command="addChild">
                <el-icon><Plus /></el-icon>
                {{ t('textSplit.addTag', '添加子标签') }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-icon v-if="hasChildren" class="tree-node-expand-icon" @click.stop="toggleExpand">
          <ExpandLess v-if="isExpanded" />
          <ExpandMore v-else />
        </el-icon>
      </div>
    </div>
    <el-collapse-transition>
      <div v-show="isExpanded && hasChildren" class="tree-node-children">
        <DomainTreeNode
          v-for="(child, index) in node.child"
          :key="index"
          :node="child"
          :level="level + 1"
          @edit="$emit('edit', $event)"
          @delete="$emit('delete', $event)"
          @add-child="$emit('add-child', $event)"
        />
      </div>
    </el-collapse-transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { Edit, Delete, Plus, ArrowUp as ExpandLess, ArrowDown as ExpandMore, MoreFilled as MoreVert } from '@element-plus/icons-vue';

defineOptions({
  name: 'DomainTreeNode',
});

const { t } = useI18n();

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
  level: {
    type: Number,
    default: 0,
  },
});

const emit = defineEmits(['edit', 'delete', 'add-child']);

const isExpanded = ref(true);
const hasChildren = computed(() => props.node.child && props.node.child.length > 0);

const toggleExpand = () => {
  if (hasChildren.value) {
    isExpanded.value = !isExpanded.value;
  }
};

const handleCommand = (command) => {
  if (command === 'edit') {
    emit('edit', props.node);
  } else if (command === 'delete') {
    emit('delete', props.node);
  } else if (command === 'addChild') {
    emit('add-child', props.node);
  }
};
</script>

<style scoped>
.domain-tree-node {
  margin-bottom: 4px;
}

.tree-node-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.tree-node-root {
  background: var(--el-color-primary);
  color: var(--el-color-primary-light-9);
  font-weight: 600;
  font-size: 15px;
}

.tree-node-root:hover {
  background: var(--el-color-primary-dark-2);
}

.tree-node-item:not(.tree-node-root):hover {
  background: var(--el-bg-color-page);
}

.tree-node-content {
  flex: 1;
  min-width: 0;
}

.tree-node-label {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-node-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 12px;
}

.tree-node-expand-icon {
  cursor: pointer;
  transition: transform 0.2s;
}

.tree-node-children {
  margin-left: 24px;
  margin-top: 4px;
}
</style>

