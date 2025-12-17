<template>
  <el-card v-if="conversation" class="conversation-rating-section" shadow="never">
    <!-- 评分区域 -->
    <div class="rating-section">
      <div class="section-title">{{ $t('datasets.rating') }}</div>
      <StarRating
        :model-value="localScore"
        :read-only="loading"
        @update:model-value="handleScoreChange"
      />
    </div>

    <el-divider />

    <!-- 标签区域 -->
    <div class="tags-section">
      <div class="section-title">{{ $t('datasets.customTags') }}</div>
      <TagSelector
        :model-value="localTags"
        :available-tags="availableTags"
        :read-only="loading"
        :placeholder="$t('datasets.addCustomTag', '添加自定义标签...')"
        @update:model-value="handleTagsChange"
      />
    </div>

    <el-divider />

    <!-- 备注区域 -->
    <div class="note-section">
      <NoteInput
        :model-value="localNote"
        :read-only="loading"
        :placeholder="$t('datasets.addNote', '添加备注...')"
        @update:model-value="handleNoteChange"
      />
    </div>

    <el-divider />

    <!-- AI评估 -->
    <div v-if="conversation.aiEvaluation" class="ai-evaluation-section">
      <div class="section-title">{{ $t('datasets.aiEvaluation') }}</div>
      <div class="ai-evaluation-text">{{ conversation.aiEvaluation }}</div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import StarRating from '@/components/datasets/StarRating.vue';
import TagSelector from '@/components/datasets/TagSelector.vue';
import NoteInput from '@/components/datasets/NoteInput.vue';
import { fetchConversations, updateConversation } from '@/api/conversation';

const props = defineProps({
  conversation: {
    type: Object,
    default: null
  },
  projectId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['update']);

const { t } = useI18n();

const loading = ref(false);
const availableTags = ref([]);
const localScore = ref(0);
const localTags = ref([]);
const localNote = ref('');

// 解析对话中的标签
const parseConversationTags = (tagsString) => {
  try {
    if (typeof tagsString === 'string' && tagsString.trim()) {
      return tagsString.split(/\s+/).filter((tag) => tag.length > 0);
    }
    return [];
  } catch (e) {
    return [];
  }
};

// 同步 conversation 到本地状态
watch(
  () => props.conversation,
  (newConversation) => {
    if (newConversation) {
      localScore.value = newConversation.score || 0;
      localTags.value = parseConversationTags(newConversation.tags);
      localNote.value = newConversation.note || '';
    }
  },
  { immediate: true }
);

// 获取项目中已使用的标签
const fetchAvailableTags = async () => {
  try {
    const response = await fetchConversations(props.projectId, {});
    // 从响应中提取所有标签
    const allTags = new Set();
    if (response?.data?.data) {
      response.data.data.forEach((conv) => {
        if (conv.tags) {
          parseConversationTags(conv.tags).forEach((tag) => allTags.add(tag));
        }
      });
    }
    availableTags.value = Array.from(allTags);
  } catch (error) {
    console.error('获取可用标签失败:', error);
  }
};

// 更新对话元数据
const updateMetadata = async (updates) => {
  if (loading.value) return;

  // 立即更新本地状态
  if (updates.score !== undefined) {
    localScore.value = updates.score;
  }
  if (updates.tagsArray !== undefined) {
    localTags.value = updates.tagsArray;
  }
  if (updates.note !== undefined) {
    localNote.value = updates.note;
  }

  loading.value = true;
  try {
    const tagsString = updates.tagsArray ? updates.tagsArray.join(' ') : updates.tags || '';
    await updateConversation(props.projectId, props.conversation.id, {
      score: updates.score,
      tags: tagsString,
      note: updates.note
    });

    ElMessage.success(t('datasets.saveSuccess'));

    // 触发更新事件
    emit('update');
  } catch (error) {
    console.error('更新对话元数据失败:', error);
    ElMessage.error(error.message || t('datasets.saveFailed'));

    // 出错时恢复本地状态
    if (updates.score !== undefined) {
      localScore.value = props.conversation?.score || 0;
    }
    if (updates.tagsArray !== undefined) {
      localTags.value = parseConversationTags(props.conversation?.tags);
    }
    if (updates.note !== undefined) {
      localNote.value = props.conversation?.note || '';
    }
  } finally {
    loading.value = false;
  }
};

// 处理评分变更
const handleScoreChange = (newScore) => {
  updateMetadata({ score: newScore });
};

// 处理标签变更
const handleTagsChange = (newTags) => {
  updateMetadata({ tags: '', tagsArray: newTags });
};

// 处理备注变更
const handleNoteChange = (newNote) => {
  updateMetadata({ note: newNote });
};

onMounted(() => {
  if (props.projectId) {
    fetchAvailableTags();
  }
});
</script>

<style scoped>
.conversation-rating-section {
  margin-bottom: 24px;
}

.rating-section,
.tags-section,
.note-section,
.ai-evaluation-section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.ai-evaluation-text {
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 14px;
  color: var(--el-text-color-regular);
}
</style>

