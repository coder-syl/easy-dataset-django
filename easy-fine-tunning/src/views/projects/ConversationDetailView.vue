<template>
  <div class="conversation-detail-view">
    <!-- 加载状态 -->
    <el-empty v-if="loading" :description="$t('datasets.loadingDataset')" />

    <!-- 无数据状态 -->
    <el-alert
      v-else-if="!conversation"
      :title="$t('datasets.conversationNotFound')"
      type="error"
      :closable="false"
    />

    <!-- 主要内容 -->
    <template v-else>
      <!-- 顶部导航栏 -->
      <ConversationHeader
        :project-id="projectId"
        :conversation-id="conversationId"
        :conversation="conversation"
        :edit-mode="editMode"
        :saving="saving"
        @edit="handleEdit"
        @save="handleSave"
        @cancel="handleCancel"
        @delete="handleDelete"
        @navigate="handleNavigate"
        @back="handleBack"
      />

      <!-- 主要布局：左右分栏 -->
      <div class="main-layout">
        <!-- 左侧主要内容区域 -->
        <div class="main-content">
          <el-card shadow="never">
            <!-- 对话内容 -->
            <ConversationContent
              :messages="editMode ? editData.messages : messages"
              :edit-mode="editMode"
              :conversation="conversation"
              @message-change="updateMessageContent"
            />
          </el-card>
        </div>

        <!-- 右侧固定侧边栏 -->
        <div class="sidebar">
          <!-- 元数据展示 -->
          <ConversationMetadata :conversation="conversation" />

          <!-- 评分、标签、备注区域 -->
          <ConversationRatingSection
            :conversation="conversation"
            :project-id="projectId"
            @update="handleUpdate"
          />
        </div>
      </div>

      <!-- 删除确认对话框 -->
      <el-dialog
        v-model="deleteDialogOpen"
        :title="$t('datasets.confirmDelete')"
        width="400px"
      >
        <p>{{ $t('datasets.confirmDeleteConversation') }}</p>
        <template #footer>
          <el-button @click="deleteDialogOpen = false">{{ $t('common.cancel') }}</el-button>
          <el-button type="danger" @click="handleDeleteConfirm">{{ $t('common.delete') }}</el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router';
import ConversationHeader from '@/components/multi-turn/ConversationHeader.vue';
import ConversationMetadata from '@/components/multi-turn/ConversationMetadata.vue';
import ConversationContent from '@/components/multi-turn/ConversationContent.vue';
import ConversationRatingSection from '@/components/multi-turn/ConversationRatingSection.vue';
import useConversationDetails from '@/composables/useConversationDetails';

const router = useRouter();
const route = useRoute();

const projectId = route.params.projectId;
const conversationId = route.params.conversationId;

// 使用 composable 管理状态和逻辑
const {
  conversation,
  messages,
  loading,
  editMode,
  saving,
  editData,
  deleteDialogOpen,
  handleEdit,
  handleSave,
  handleCancel,
  handleDelete: handleDeleteConfirm,
  handleNavigate,
  updateMessageContent,
  fetchConversation
} = useConversationDetails();

// 返回列表
const handleBack = () => {
  router.push(`/projects/${projectId}/multi-turn`);
};

// 删除对话（打开确认对话框）
const handleDelete = () => {
  deleteDialogOpen.value = true;
};

// 更新后刷新数据
const handleUpdate = () => {
  fetchConversation();
};
</script>

<style scoped>
.conversation-detail-view {
  padding: 24px;
}

.main-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.main-content {
  flex: 1;
  min-width: 0;
}

.sidebar {
  width: 360px;
  position: sticky;
  top: 24px;
  max-height: calc(100vh - 48px);
  overflow-y: auto;
}
</style>

