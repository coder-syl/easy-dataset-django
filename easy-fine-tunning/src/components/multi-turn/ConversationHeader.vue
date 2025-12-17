<template>
  <el-card class="conversation-header" shadow="never">
    <div class="header-content">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="handleBack">
          {{ $t('common.backToList') }}
        </el-button>
        <el-divider direction="vertical" />
        <span class="header-title">{{ $t('datasets.conversationDetail') }}</span>
        <span v-if="conversation" class="header-subtitle">
          <template v-if="conversation.scenario">
            {{ conversation.scenario }} • {{ conversation.turnCount }}/{{ conversation.maxTurns }} {{ $t('datasets.rounds') }}
          </template>
        </span>
      </div>

      <div class="header-right">
        <!-- 翻页按钮 -->
        <el-button :icon="ArrowLeft" circle @click="handleNavigate('prev')" />
        <el-button :icon="ArrowRight" circle @click="handleNavigate('next')" />
        <el-divider direction="vertical" />

        <!-- 编辑/保存按钮 -->
        <template v-if="editMode">
          <el-button @click="handleCancel">{{ $t('common.cancel') }}</el-button>
          <el-button
            type="primary"
            :icon="saving ? Loading : Document"
            :loading="saving"
            @click="handleSave"
          >
            {{ saving ? $t('datasets.saving') : $t('common.save') }}
          </el-button>
        </template>
        <template v-else>
          <el-button :icon="Edit" @click="handleEdit">{{ $t('common.edit') }}</el-button>
          <el-button type="danger" :icon="Delete" @click="handleDelete">{{ $t('common.delete') }}</el-button>
        </template>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ArrowLeft, ArrowRight, Edit, Delete, Document, Loading } from '@element-plus/icons-vue';

const props = defineProps({
  projectId: {
    type: String,
    required: true
  },
  conversationId: {
    type: String,
    required: true
  },
  conversation: {
    type: Object,
    default: null
  },
  editMode: {
    type: Boolean,
    default: false
  },
  saving: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['edit', 'save', 'cancel', 'delete', 'navigate', 'back']);

const handleBack = () => {
  emit('back');
};

const handleEdit = () => {
  emit('edit');
};

const handleSave = () => {
  emit('save');
};

const handleCancel = () => {
  emit('cancel');
};

const handleDelete = () => {
  emit('delete');
};

const handleNavigate = (direction) => {
  emit('navigate', direction);
};
</script>

<style scoped>
.conversation-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  font-size: 18px;
  font-weight: 500;
}

.header-subtitle {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>

