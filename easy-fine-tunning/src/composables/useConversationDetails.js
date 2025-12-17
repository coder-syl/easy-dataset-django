import { ref, watch, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  fetchConversationDetail,
  updateConversation,
  deleteConversation
} from '@/api/conversation';

/**
 * 多轮对话详情页面的状态管理 Composable
 */
export default function useConversationDetails() {
  const { t } = useI18n();
  const router = useRouter();
  const route = useRoute();

  const projectId = ref(route.params.projectId);
  const conversationId = ref(route.params.conversationId);

  // 基础状态
  const conversation = ref(null);
  const messages = ref([]);
  const loading = ref(true);

  // 编辑状态
  const editMode = ref(false);
  const saving = ref(false);
  const editData = ref({
    score: 0,
    tags: '',
    note: '',
    confirmed: false,
    messages: []
  });

  // 对话框状态
  const deleteDialogOpen = ref(false);

  // 获取对话详情
  const fetchConversation = async () => {
    try {
      loading.value = true;
      const response = await fetchConversationDetail(projectId.value, conversationId.value);

      // 处理响应数据
      const data = response?.data || response || {};

      // 兼容 Django snake_case 字段到前端 camelCase
      const normalized = {
        ...data,
        rawMessages: data.raw_messages || data.rawMessages || '[]',
        turnCount: data.turn_count ?? data.turnCount ?? 0,
        maxTurns:
          data.max_turns ??
          data.maxTurns ??
          data.turn_count ??
          data.turnCount ??
          0,
        roleA: data.role_a ?? data.roleA,
        roleB: data.role_b ?? data.roleB,
        createAt:
          data.create_at ??
          data.createAt ??
          data.createTime ??
          data.create_time,
        aiEvaluation: data.ai_evaluation || data.aiEvaluation
      };

      conversation.value = normalized;

      // 解析对话消息
      let parsedMessages = [];
      try {
        parsedMessages = JSON.parse(normalized.rawMessages || '[]');
        messages.value = parsedMessages;
      } catch (error) {
        console.error('解析对话消息失败:', error);
        messages.value = [];
      }

      // 设置编辑数据
      editData.value = {
        score: normalized.score || 0,
        tags: normalized.tags || '',
        note: normalized.note || '',
        confirmed: normalized.confirmed || false,
        messages: parsedMessages
      };
    } catch (error) {
      console.error('获取对话详情失败:', error);
      ElMessage.error(error.message || t('datasets.fetchDataFailed'));
      
      // 如果是 404，跳转到列表页
      if (error.response?.status === 404 || error.code === 500) {
        ElMessage.error(t('datasets.conversationNotFound'));
        router.push(`/projects/${projectId.value}/multi-turn`);
      }
    } finally {
      loading.value = false;
    }
  };

  // 保存编辑
  const handleSave = async () => {
    try {
      saving.value = true;
      await updateConversation(projectId.value, conversationId.value, {
        score: editData.value.score,
        tags: editData.value.tags,
        note: editData.value.note,
        confirmed: editData.value.confirmed,
        messages: editData.value.messages
      });

      // 更新本地状态
      conversation.value = { ...conversation.value, ...editData.value };
      messages.value = editData.value.messages;
      editMode.value = false;
      ElMessage.success(t('datasets.saveSuccess'));
    } catch (error) {
      console.error('保存失败:', error);
      ElMessage.error(error.message || t('datasets.saveFailed'));
    } finally {
      saving.value = false;
    }
  };

  // 开始编辑
  const handleEdit = () => {
    editMode.value = true;
  };

  // 取消编辑
  const handleCancel = () => {
    // 恢复到原始数据
    editData.value = {
      score: conversation.value?.score || 0,
      tags: conversation.value?.tags || '',
      note: conversation.value?.note || '',
      confirmed: conversation.value?.confirmed || false,
      messages: messages.value
    };
    editMode.value = false;
  };

  // 删除对话
  const handleDelete = async () => {
    try {
      await deleteConversation(projectId.value, conversationId.value);
      ElMessage.success(t('datasets.deleteSuccess'));
      router.push(`/projects/${projectId.value}/multi-turn`);
    } catch (error) {
      console.error('删除失败:', error);
      ElMessage.error(error.message || t('datasets.deleteFailed'));
    } finally {
      deleteDialogOpen.value = false;
    }
  };

  // 更新消息内容
  const updateMessageContent = (index, newContent) => {
    const updatedMessages = [...editData.value.messages];
    updatedMessages[index] = { ...updatedMessages[index], content: newContent };
    editData.value = { ...editData.value, messages: updatedMessages };
  };

  // 翻页导航
  const handleNavigate = async (direction) => {
    try {
      // 获取当前对话列表，找到相邻的对话
      const { fetchAllConversationIds } = await import('@/api/conversation');
      const response = await fetchAllConversationIds(projectId.value);

      // Django 返回格式: { data: { allConversationIds: [...] } }
      const allIds = response?.data?.allConversationIds || response?.allConversationIds || [];
      const currentIndex = allIds.findIndex((id) => id === conversationId.value);

      if (currentIndex === -1) {
        ElMessage.warning(t('datasets.navigateFailed'));
        return;
      }

      let targetIndex;
      if (direction === 'next') {
        targetIndex = currentIndex + 1;
        if (targetIndex >= allIds.length) {
          ElMessage.warning(t('datasets.alreadyLastConversation'));
          return;
        }
      } else {
        targetIndex = currentIndex - 1;
        if (targetIndex < 0) {
          ElMessage.warning(t('datasets.alreadyFirstConversation'));
          return;
        }
      }

      const targetId = allIds[targetIndex];
      conversationId.value = targetId;
      router.push(`/projects/${projectId.value}/multi-turn/${targetId}`);
    } catch (error) {
      console.error('导航失败:', error);
      ElMessage.error(error.message || t('datasets.navigateFailed'));
    }
  };

  // 监听路由参数变化
  watch(
    () => route.params.conversationId,
    (newId) => {
      if (newId && newId !== conversationId.value) {
        conversationId.value = newId;
        fetchConversation();
      }
    }
  );

  watch(
    () => route.params.projectId,
    (newId) => {
      if (newId && newId !== projectId.value) {
        projectId.value = newId;
        fetchConversation();
      }
    }
  );

  // 初始化
  onMounted(() => {
    fetchConversation();
  });

  return {
    // 数据状态
    conversation,
    messages,
    loading,

    // 编辑状态
    editMode,
    saving,
    editData,

    // 对话框状态
    deleteDialogOpen,

    // 操作方法
    handleEdit,
    handleSave,
    handleCancel,
    handleDelete,
    handleNavigate,
    updateMessageContent,
    fetchConversation
  };
}

