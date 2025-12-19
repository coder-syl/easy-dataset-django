<template>
  <div class="distill-tree">
    <div v-if="tagTree.length > 0">
      <div class="tag-list">
        <template v-for="tag in tagTree" :key="tag.id">
          <div class="tag-block">
            <div
              class="tag-row"
              :style="{ paddingLeft: `${tagLevelPadding(0)}px` }"
              @click="toggleTag(tag.id)"
            >
              <div class="tag-main">
                <el-icon class="tag-folder">
                  <Folder />
                </el-icon>
                <span class="tag-label">{{ tag.label }}</span>

                <el-tag
                  v-if="tag.children && tag.children.length > 0"
                  size="small"
                  type="info"
                  effect="plain"
                  class="tag-chip"
                >
                  {{ getTotalSubTagsCount(tag.children) }} {{ t('distill.subTags') }}
                </el-tag>

                <el-tag
                  v-if="totalQuestions(tag) > 0"
                  size="small"
                  type="success"
                  effect="plain"
                  class="tag-chip"
                >
                  {{ totalQuestions(tag) }} {{ t('distill.questions') }}
                </el-tag>
              </div>

              <div class="tag-actions">
                <el-tooltip :content="t('distill.generateQuestions')" placement="top">
                  <el-button
                    link
                    size="small"
                    @click.stop="handleGenerateQuestions(tag)"
                  >
                    <el-icon><QuestionFilled /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-tooltip :content="t('distill.generateSubTags')" placement="top">
                  <el-button
                    link
                    size="small"
                    @click.stop="handleGenerateSubTags(tag)"
                  >
                    <el-icon><Plus /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-dropdown
                  trigger="click"
                  @command="(cmd) => handleTagMenuCommand(cmd, tag)"
                >
                  <span class="el-dropdown-link" @click.stop>
                    <el-icon><MoreFilled /></el-icon>
                  </span>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit">
                        {{ t('common.edit') }}
                      </el-dropdown-item>
                      <el-dropdown-item command="delete">
                        {{ t('common.delete') }}
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>

                <el-icon v-if="tag.children && tag.children.length" class="expand-icon">
                  <ArrowDown
                    v-if="expandedTags[tag.id]"
                  />
                  <ArrowRight
                    v-else
                  />
                </el-icon>
              </div>
            </div>

            <!-- 标签下的问题 -->
            <transition name="fade">
              <div
                v-if="expandedTags[tag.id]"
                class="questions-container"
              >
                <div class="questions-list">
                  <div
                    v-if="loadingQuestions[tag.id]"
                    class="questions-loading"
                  >
                    <el-icon class="mr-4"><Loading /></el-icon>
                    <span>{{ t('common.loading') }}</span>
                  </div>
                  <template v-else>
                    <div
                      v-if="(tagQuestions[tag.id] || []).length > 0"
                    >
                      <div
                        v-for="q in tagQuestions[tag.id]"
                        :key="q.id"
                        class="question-row"
                      >
                        <div class="question-main">
                          <el-icon class="question-icon">
                            <InfoFilled />
                          </el-icon>
                          <span class="question-text">
                            {{ q.question }}
                          </span>
                          <el-tag
                            v-if="q.answered"
                            type="success"
                            size="small"
                            effect="plain"
                            class="question-chip"
                          >
                            {{ t('datasets.answered') }}
                          </el-tag>
                        </div>
                        <div class="question-actions">
                          <el-tooltip :content="t('datasets.generateDataset')" placement="top">
                            <el-button
                              link
                              size="small"
                              :loading="processingQuestions[q.id]"
                              @click.stop="handleGenerateDataset(q)"
                            >
                              <el-icon><MagicStick /></el-icon>
                            </el-button>
                          </el-tooltip>
                          <el-tooltip
                            v-if="q.conversation_count > 0"
                            :content="t('datasets.viewMultiTurnDataset', { defaultValue: '查看多轮对话数据集' })"
                            placement="top"
                          >
                            <el-button
                              link
                              size="small"
                              @click.stop="handleViewMultiTurnDataset(q)"
                            >
                              <el-icon><View /></el-icon>
                            </el-button>
                          </el-tooltip>
                          <el-tooltip :content="t('questions.generateMultiTurnDataset', { defaultValue: '生成多轮对话数据集' })" placement="top">
                            <el-button
                              link
                              size="small"
                              :loading="processingMultiTurnQuestions[q.id]"
                              @click.stop="handleGenerateMultiTurnDataset(q)"
                            >
                              <el-icon><ChatDotRound /></el-icon>
                            </el-button>
                          </el-tooltip>
                          <el-tooltip :content="t('common.delete')" placement="top">
                            <el-button
                              link
                              size="small"
                              @click.stop="openDeleteQuestionConfirm(q.id)"
                            >
                              <el-icon><Delete /></el-icon>
                            </el-button>
                          </el-tooltip>
                        </div>
                      </div>
                    </div>
                    <div
                      v-else
                      class="questions-empty"
                    >
                      {{ t('distill.noQuestions') }}
                    </div>
                  </template>
                </div>
              </div>
            </transition>

            <!-- 子标签 -->
            <transition name="fade">
              <div
                v-if="expandedTags[tag.id] && tag.children && tag.children.length"
                class="children-container"
              >
                <DistillTreeChild
                  :tags="tag.children"
                  :level="1"
                  :expanded-tags="expandedTags"
                  :tag-questions="tagQuestions"
                  :loading-questions="loadingQuestions"
                  :processing-questions="processingQuestions"
                  :processing-multi-turn-questions="processingMultiTurnQuestions"
                  :all-questions="allQuestions"
                  @toggle="toggleTag"
                  @generate-questions="handleGenerateQuestions"
                  @generate-sub-tags="handleGenerateSubTags"
                  @generate-dataset="handleGenerateDataset"
                  @generate-multi-turn-dataset="handleGenerateMultiTurnDataset"
                  @view-multi-turn-dataset="handleViewMultiTurnDataset"
                  @delete-question="openDeleteQuestionConfirm"
                  @tag-menu-command="handleTagMenuCommand"
                />
              </div>
            </transition>
          </div>
        </template>
      </div>
    </div>
    <div v-else class="empty-tip">
      {{ t('distill.noTags') }}
    </div>

    <!-- 编辑标签对话框 -->
    <el-dialog
      v-model="editDialogOpen"
      :title="t('distill.editTagTitle')"
      width="420px"
    >
      <div class="dialog-body">
        <el-input
          v-model="editTagLabel"
          :placeholder="t('distill.tagName')"
        />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogOpen = false">
            {{ t('common.cancel') }}
          </el-button>
          <el-button
            type="primary"
            :loading="editingTag"
            :disabled="!editTagLabel.trim()"
            @click="handleEditTagConfirm"
          >
            {{ t('common.confirm') }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 删除标签确认 -->
    <el-dialog
      v-model="deleteTagConfirmOpen"
      :title="t('distill.deleteTagConfirmTitle')"
      width="420px"
    >
      <div>
        {{ t('distill.deleteTagConfirmText') }}
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteTagConfirmOpen = false">
            {{ t('common.cancel') }}
          </el-button>
          <el-button
            type="danger"
            :loading="deletingTag"
            @click="handleDeleteTag"
          >
            {{ t('common.delete') }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 删除问题确认 -->
    <el-dialog
      v-model="deleteQuestionConfirmOpen"
      :title="t('questions.deleteConfirm')"
      width="420px"
    >
      <div>
        {{ t('questions.deleteConfirm') }}
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteQuestionConfirmOpen = false">
            {{ t('common.cancel') }}
          </el-button>
          <el-button
            type="danger"
            :loading="deletingQuestion"
            @click="handleDeleteQuestion"
          >
            {{ t('common.delete') }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import {
  Folder,
  Plus,
  QuestionFilled,
  MoreFilled,
  ArrowDown,
  ArrowRight,
  Loading,
  InfoFilled,
  MagicStick,
  ChatDotRound,
  Delete,
  View,
} from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import http from '@/api/http';
import { useModelStore } from '@/stores/model';
import DistillTreeChild from './DistillTreeChild.vue';

const props = defineProps({
  projectId: {
    type: String,
    required: true,
  },
  tags: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits([
  'generate-sub-tags',
  'generate-questions',
  'update:tags',
]);

const { t } = useI18n();
const modelStore = useModelStore();

const expandedTags = ref({});
const tagQuestions = ref({});
const loadingQuestions = ref({});
const processingQuestions = ref({});
const processingMultiTurnQuestions = ref({});
const allQuestions = ref([]);

const editDialogOpen = ref(false);
const editTagLabel = ref('');
const editingTag = ref(false);
const currentEditTag = ref(null);

const deleteTagConfirmOpen = ref(false);
const deletingTag = ref(false);
const currentDeleteTag = ref(null);

const deleteQuestionConfirmOpen = ref(false);
const deletingQuestion = ref(false);
const currentDeleteQuestionId = ref(null);

const projectName = ref('');

// 构建树
const tagTree = computed(() => {
  const roots = [];
  const map = {};
  (props.tags || []).forEach((tag) => {
    map[tag.id] = { ...tag, children: [] };
  });
  Object.values(map).forEach((tag) => {
    if (tag.parentId && map[tag.parentId]) {
      map[tag.parentId].children.push(map[tag.id]);
    } else {
      roots.push(map[tag.id]);
    }
  });
  return roots;
});

const tagLevelPadding = (level) => 24 + level * 16;

// 获取项目名
const fetchProjectName = async () => {
  try {
    const res = await http.get(`/projects/${props.projectId}/`);
    const data = res?.data && Object.keys(res.data || {}).length ? res.data : res;
    projectName.value = data?.name || '';
  } catch {
    projectName.value = '';
  }
};

// 统计问题
const fetchQuestionsStats = async () => {
  try {
    const res = await http.get(`/projects/${props.projectId}/questions/tree/`, {
      params: { isDistill: 'yes' },
    });
    const list = Array.isArray(res) ? res : res?.data || res || [];
    allQuestions.value = list;
  } catch (e) {
    console.error('获取问题统计信息失败:', e);
  }
};

// 暴露给父组件
defineExpose({
  fetchQuestionsStats,
});

// 根据标签ID加载问题
const fetchQuestionsByTag = async (tagId) => {
  if (!tagId) return;
  try {
    loadingQuestions.value = { ...loadingQuestions.value, [tagId]: true };
    const res = await http.get(`/projects/${props.projectId}/distill/questions/by-tag/`, {
      params: { tagId },
    });
    const list = Array.isArray(res) ? res : res?.data || res || [];
    tagQuestions.value = {
      ...tagQuestions.value,
      [tagId]: list,
    };
  } catch (e) {
    console.error('获取标签问题失败:', e);
  } finally {
    loadingQuestions.value = { ...loadingQuestions.value, [tagId]: false };
  }
};

const toggleTag = (tagId) => {
  expandedTags.value = {
    ...expandedTags.value,
    [tagId]: !expandedTags.value[tagId],
  };
  if (expandedTags.value[tagId] && !tagQuestions.value[tagId]) {
    fetchQuestionsByTag(tagId);
  }
};

// 路径
const getTagPath = (tag) => {
  if (!tag) return '';
  const findPath = (current, path = []) => {
    const newPath = [current.label, ...path];
    if (!current.parentId) {
      if (projectName.value && !newPath.includes(projectName.value)) {
        return [projectName.value, ...newPath];
      }
      return newPath;
    }
    const parent = (props.tags || []).find((t) => t.id === current.parentId);
    if (!parent) {
      if (projectName.value && !newPath.includes(projectName.value)) {
        return [projectName.value, ...newPath];
      }
      return newPath;
    }
    return findPath(parent, newPath);
  };
  const path = findPath(tag);
  if (projectName.value && path.length > 0 && path[0] !== projectName.value) {
    path.unshift(projectName.value);
  }
  return path.join(' > ');
};

const handleGenerateSubTags = (tag) => {
  const tagPath = getTagPath(tag);
  emit('generate-sub-tags', tag, tagPath);
};

const handleGenerateQuestions = (tag) => {
  const tagPath = getTagPath(tag);
  emit('generate-questions', tag, tagPath);
};

// 问题数量（当前标签 + 子标签）
const getChildrenQuestionsCount = (childrenTags) => {
  let count = 0;
  (childrenTags || []).forEach((child) => {
    if (tagQuestions.value[child.id] && tagQuestions.value[child.id].length > 0) {
      count += tagQuestions.value[child.id].length;
    } else {
      count += allQuestions.value.filter((q) => q.label === child.label).length;
    }
    if (child.children && child.children.length > 0) {
      count += getChildrenQuestionsCount(child.children);
    }
  });
  return count;
};

const getCurrentTagQuestionsCount = (tag) => {
  if (tagQuestions.value[tag.id] && tagQuestions.value[tag.id].length > 0) {
    return tagQuestions.value[tag.id].length;
  }
  return allQuestions.value.filter((q) => q.label === tag.label).length;
};

const totalQuestions = (tag) => {
  return getCurrentTagQuestionsCount(tag) + getChildrenQuestionsCount(tag.children || []);
};

const getTotalSubTagsCount = (childrenTags) => {
  let count = childrenTags.length;
  (childrenTags || []).forEach((child) => {
    if (child.children && child.children.length > 0) {
      count += getTotalSubTagsCount(child.children);
    }
  });
  return count;
};

// 生成单轮数据集
const handleGenerateDataset = async (question) => {
  const questionId = question.id;
  processingQuestions.value = {
    ...processingQuestions.value,
    [questionId]: true,
  };
  try {
    const model = modelStore.selectedModelInfo;
    if (!model) {
      ElMessage.error(t('models.configNotFound'));
      return;
    }
    await http.post(`/projects/${props.projectId}/datasets/`, {
      questionId,
      model,
      language: 'zh-CN',
    });
    ElMessage.success(t('datasets.generateSuccess') || '生成数据集成功');
    await fetchQuestionsStats();
  } catch (e) {
    console.error('生成数据集失败:', e);
    ElMessage.error(t('datasets.generateFailed') || '生成数据集失败');
  } finally {
    processingQuestions.value = {
      ...processingQuestions.value,
      [questionId]: false,
    };
  }
};

// 生成多轮数据集
const handleGenerateMultiTurnDataset = async (question) => {
  const questionId = question.id;
  processingMultiTurnQuestions.value = {
    ...processingMultiTurnQuestions.value,
    [questionId]: true,
  };
  try {
    const model = modelStore.selectedModelInfo;
    if (!model) {
      throw new Error(t('distill.selectModelFirst'));
    }
    const configRaw = await http.get(`/projects/${props.projectId}/tasks/`);
    const config =
      configRaw?.data && Object.keys(configRaw.data || {}).length
        ? configRaw.data
        : configRaw || {};
    const multiTurnConfig = {
      systemPrompt: config.multiTurnSystemPrompt,
      scenario: config.multiTurnScenario,
      rounds: parseInt(config.multiTurnRounds, 10),
      roleA: config.multiTurnRoleA,
      roleB: config.multiTurnRoleB,
    };
    if (
      !multiTurnConfig.scenario ||
      !multiTurnConfig.roleA ||
      !multiTurnConfig.roleB ||
      !multiTurnConfig.rounds ||
      multiTurnConfig.rounds < 1
    ) {
      throw new Error(t('datasets.multiTurnConfigMissing') || '请先在项目设置中配置多轮对话相关参数');
    }

    await http.post(`/projects/${props.projectId}/dataset-conversations/`, {
      questionId,
      ...multiTurnConfig,
      model,
      language: 'zh-CN',
    });

    await fetchQuestionsStats();
    ElMessage.success(
      t('datasets.multiTurnGenerateSuccess', { defaultValue: '多轮对话数据集生成成功！' }),
    );

    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('refreshDistillStats'));
    }
  } catch (e) {
    console.error('生成多轮对话数据集失败:', e);
    ElMessage.error(
      e?.message ||
        t('datasets.multiTurnGenerateError', { defaultValue: '生成多轮对话数据集失败' }),
    );
  } finally {
    processingMultiTurnQuestions.value = {
      ...processingMultiTurnQuestions.value,
      [questionId]: false,
    };
  }
};

// 查看多轮对话数据集
const handleViewMultiTurnDataset = async (question) => {
  try {
    const res = await http.get(`/projects/${props.projectId}/dataset-conversations/`, {
      params: { questionId: question.id },
    });
    const data = res?.data?.data || res?.data || res;
    const conversations = Array.isArray(data) ? data : data.conversations || [];
    if (conversations.length > 0) {
      router.push(`/projects/${props.projectId}/multi-turn/${conversations[0].id}`);
    } else {
      ElMessage.warning(t('datasets.noConversationFound') || '未找到关联的多轮对话');
    }
  } catch (e) {
    console.error('获取多轮对话失败:', e);
    ElMessage.error(t('datasets.fetchConversationError') || '获取多轮对话详情失败');
  }
};

// 标签菜单
const handleTagMenuCommand = (command, tag) => {
  if (command === 'edit') {
    currentEditTag.value = tag;
    editTagLabel.value = tag.label;
    editDialogOpen.value = true;
  } else if (command === 'delete') {
    currentDeleteTag.value = tag;
    deleteTagConfirmOpen.value = true;
  }
};

const handleEditTagConfirm = async () => {
  if (!currentEditTag.value || !editTagLabel.value.trim()) return;
  try {
    editingTag.value = true;
    const res = await http.put(
      `/projects/${props.projectId}/distill/tags/${currentEditTag.value.id}/`,
      { label: editTagLabel.value.trim() },
    );
    const updated = res?.data || res;
    const updatedTags = (props.tags || []).map((t) =>
      t.id === updated.id ? { ...t, label: updated.label } : t,
    );
    emit('update:tags', updatedTags);
    ElMessage.success(t('distill.tagUpdateSuccess') || '标签已更新');
    editDialogOpen.value = false;
  } catch (e) {
    console.error('更新标签失败:', e);
    ElMessage.error(t('distill.tagUpdateFailed') || '更新标签失败');
  } finally {
    editingTag.value = false;
  }
};

const handleDeleteTag = async () => {
  if (!currentDeleteTag.value) return;
  try {
    deletingTag.value = true;
    await http.delete(`/projects/${props.projectId}/tags/`, {
      params: { id: currentDeleteTag.value.id },
    });
    // 简化处理：刷新页面，保持与 Next 版本行为一致
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  } catch (e) {
    console.error('删除标签失败:', e);
    ElMessage.error(t('distill.tagDeleteFailed') || '删除标签失败');
  } finally {
    deletingTag.value = false;
  }
};

// 删除问题
const openDeleteQuestionConfirm = (questionId) => {
  currentDeleteQuestionId.value = questionId;
  deleteQuestionConfirmOpen.value = true;
};

const handleDeleteQuestion = async () => {
  if (!currentDeleteQuestionId.value) return;
  try {
    deletingQuestion.value = true;
    await http.delete(
      `/projects/${props.projectId}/questions/${currentDeleteQuestionId.value}/`,
    );
    const qId = currentDeleteQuestionId.value;
    const newMap = { ...tagQuestions.value };
    Object.keys(newMap).forEach((tagId) => {
      newMap[tagId] = (newMap[tagId] || []).filter((q) => q.id !== qId);
    });
    tagQuestions.value = newMap;
    deleteQuestionConfirmOpen.value = false;
  } catch (e) {
    console.error('删除问题失败:', e);
    ElMessage.error(t('questions.deleteFailed') || '删除问题失败');
  } finally {
    deletingQuestion.value = false;
  }
};

onMounted(async () => {
  await fetchProjectName();
  await fetchQuestionsStats();
});
</script>

<style scoped>
.distill-tree {
  padding: 8px 80px 8px 0; /* 右侧预留空间，让操作按钮整体左移一点 */
  overflow-x: hidden;
}

.tag-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tag-block {
  margin-bottom: 4px;
}

.tag-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
}

.tag-row:hover {
  background-color: var(--el-fill-color-light);
}

.tag-main {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.tag-folder {
  color: var(--el-color-primary);
}

.tag-label {
  font-size: 14px;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.tag-chip {
  margin-left: 4px;
}

.tag-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.expand-icon {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.questions-container {
  margin-left: 32px;
  border-left: 1px dashed var(--el-border-color-lighter);
  padding-left: 12px;
}

.questions-list {
  margin-top: 4px;
}

.questions-loading {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.questions-empty {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  padding: 4px 0;
}

.question-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.question-row:last-child {
  border-bottom: none;
}

.question-main {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}

.question-icon {
  color: var(--el-color-warning);
}

.question-text {
  font-size: 13px;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.question-chip {
  margin-left: 4px;
}

.question-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 8px;
}

.children-container {
  margin-top: 4px;
}

.empty-tip {
  padding: 8px;
  text-align: center;
  color: var(--el-text-color-secondary);
}

.dialog-body {
  padding: 8px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>