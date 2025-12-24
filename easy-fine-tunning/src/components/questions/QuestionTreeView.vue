<template>
  <div class="question-tree-view">
    <!-- 没有标签和问题时的空状态 -->
    <el-empty
      v-if="isEmpty"
      :description="t('datasets.noTagsAndQuestions') || '暂无标签和问题'"
    />

    <div v-else class="tree-container">
      <!-- 未分类问题 -->
      <div v-if="uncategorizedQuestions.length > 0" class="uncategorized-block">
        <div class="tag-row tag-row-root" @click="toggleTag('uncategorized')">
          <el-icon class="tag-icon">
            <Folder />
          </el-icon>
          <span class="tag-label">{{ t('datasets.uncategorized') }}</span>
          <el-tag
            size="small"
            type="info"
            effect="plain"
            class="tag-count"
          >
            {{ t('datasets.questionCount', { count: uncategorizedQuestions.length }) }}
          </el-tag>
          <el-icon class="tag-expand-icon">
            <ArrowDown v-if="expandedTags.uncategorized" />
            <ArrowRight v-else />
          </el-icon>
        </div>

        <transition name="el-collapse-transition">
          <div v-show="expandedTags.uncategorized" class="uncategorized-questions">
            <div
              v-for="q in uncategorizedQuestions"
              :key="q.id"
              class="question-item"
              :style="{ paddingLeft: (16 + 24) + 'px' }"
            >
              <div class="question-main">
                <el-checkbox
                  :model-value="selectedQuestions.includes(q.id)"
                  @change="onSelectQuestion(q.id)"
                />
                <el-icon class="question-icon">
                  <QuestionFilled />
                </el-icon>
                <div class="question-text">
                  <div class="question-title">
                    {{ q.question }}
                    <el-tag
                      v-if="(q.datasetCount || q.dataset_count || 0) > 0"
                      size="small"
                      type="primary"
                      effect="plain"
                      class="answer-count-tag"
                    >
                      {{ t('datasets.answerCount', { count: q.datasetCount || q.dataset_count || 0 }) }}
                    </el-tag>
                  </div>
                  <div class="question-meta">
                    {{ t('datasets.source') }}:
                    {{ q.chunk?.name || q.chunk_name || t('common.unknown') }}
                  </div>
                </div>
              </div>

              <div class="question-actions">
                <el-tooltip :content="t('common.edit')">
                  <el-button
                    class="table-action-button"
                    size="small"
                    :icon="Edit"
                    :loading="processingQuestions[q.id]"
                    @click.stop="emitEdit(q)"
                  />
                </el-tooltip>
                <el-tooltip :content="t('datasets.generateDataset')">
                  <el-button
                    class="table-action-button"
                    size="small"
                    :icon="MagicStick"
                    :loading="processingQuestions[q.id]"
                    @click.stop="handleGenerateDataset(q)"
                  />
                </el-tooltip>
                <el-tooltip :content="t('common.delete')">
                  <el-button
                    class="table-action-button"
                    size="small"
                    type="danger"
                    :icon="Delete"
                    :loading="processingQuestions[q.id]"
                    @click.stop="emitDelete(q.id)"
                  />
                </el-tooltip>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- 标签树 -->
      <div class="tags-block">
        <QuestionTreeTagNode
          v-for="tag in tags"
          :key="tag.label"
          :tag="tag"
          :level="0"
          :is-expanded="expandedTags[tag.label]"
          :expanded-tags="expandedTags"
          :questions-by-tag="questionsByTag"
          :tag-question-counts="tagQuestionCounts"
          :selected-questions="selectedQuestions"
          :processing-questions="processingQuestions"
          :project-id="projectId"
          :t="t"
          @toggle-tag="toggleTag"
          @select-question="onSelectQuestion"
          @delete-question="emitDelete"
          @edit-question="emitEdit"
          @generate-dataset="handleGenerateDataset"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { Folder, ArrowDown, ArrowRight, QuestionFilled, Edit, Delete, MagicStick } from '@element-plus/icons-vue';
import QuestionTreeTagNode from './QuestionTreeTagNode.vue';
import { generateDataset } from '@/api/dataset';
import { useModelStore } from '@/stores/model';

const props = defineProps({
  questions: {
    type: Array,
    default: () => []
  },
  tags: {
    type: Array,
    default: () => []
  },
  selectedQuestions: {
    type: Array,
    default: () => []
  },
  searchTerm: {
    type: String,
    default: ''
  },
  projectId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['select-question', 'delete-question', 'edit-question']);

const { t, locale } = useI18n();
const modelStore = useModelStore();

const expandedTags = ref({});
const questionsByTag = ref({});
const processingQuestions = ref({});

// 初始化展开状态
const initExpandedState = () => {
  const state = {};
  const processTag = (tag) => {
    state[tag.label] = false;
    if (tag.child && tag.child.length > 0) {
      tag.child.forEach(processTag);
    }
  };
  props.tags.forEach(processTag);
  state.uncategorized = false;
  expandedTags.value = state;
};

// 根据标签构建 tag -> 问题映射
const buildQuestionsByTag = () => {
  const map = {};

  const initTagMap = (tag) => {
    map[tag.label] = [];
    if (tag.child && tag.child.length > 0) {
      tag.child.forEach(initTagMap);
    }
  };
  props.tags.forEach(initTagMap);

  const findAllMatchingTags = (tag, questionLabel, path = []) => {
    const currentPath = [...path, tag.label];
    const matches = [];

    if (tag.label === questionLabel) {
      matches.push({ label: tag.label, depth: currentPath.length });
    }

    if (tag.child && tag.child.length > 0) {
      for (const child of tag.child) {
        const childMatches = findAllMatchingTags(child, questionLabel, currentPath);
        matches.push(...childMatches);
      }
    }
    return matches;
  };

  props.questions.forEach((q) => {
    if (!q.label) {
      if (!map.uncategorized) map.uncategorized = [];
      map.uncategorized.push(q);
      return;
    }
    const questionLabel = q.label;
    let allMatches = [];
    for (const rootTag of props.tags) {
      const matches = findAllMatchingTags(rootTag, questionLabel);
      allMatches = allMatches.concat(matches);
    }
    let matched = null;
    if (allMatches.length > 0) {
      allMatches.sort((a, b) => b.depth - a.depth);
      matched = allMatches[0].label;
    }
    if (matched) {
      if (!map[matched]) map[matched] = [];
      map[matched].push(q);
    } else {
      if (!map.uncategorized) map.uncategorized = [];
      map.uncategorized.push(q);
    }
  });

  questionsByTag.value = map;
};

// 计算每个标签下问题数量（包含子标签）
const tagQuestionCounts = computed(() => {
  const counts = {};

  const countQuestions = (tag) => {
    const direct = questionsByTag.value[tag.label] || [];
    let total = direct.length;
    if (tag.child && tag.child.length > 0) {
      for (const child of tag.child) {
        total += countQuestions(child);
      }
    }
    counts[tag.label] = total;
    return total;
  };

  props.tags.forEach(countQuestions);
  return counts;
});

const uncategorizedQuestions = computed(() => questionsByTag.value.uncategorized || []);

const isEmpty = computed(() => props.tags.length === 0 && Object.keys(questionsByTag.value).length === 0);

// 监听标签/问题变化
watch(
  () => [props.tags, props.questions],
  () => {
    initExpandedState();
    buildQuestionsByTag();
  },
  { immediate: true, deep: true }
);

const toggleTag = (label) => {
  expandedTags.value = {
    ...expandedTags.value,
    [label]: !expandedTags.value[label]
  };
};

const onSelectQuestion = (id) => {
  emit('select-question', id, !props.selectedQuestions.includes(id));
};

const emitDelete = (id) => {
  emit('delete-question', id);
};

const emitEdit = (q) => {
  emit('edit-question', {
    question: q.question,
    chunkId: q.chunkId || q.chunk_id,
    label: q.label || 'other'
  });
};

const handleGenerateDataset = async (question) => {
  const questionId = question.id;
  processingQuestions.value[questionId] = true;
  try {
    const model = modelStore.selectedModelInfo;
    if (!model) {
      ElMessage.warning(t('models.configNotFound') || '请先选择模型');
      return;
    }
    const language = locale.value === 'zh' ? '中文' : 'en';
    await generateDataset(props.projectId, {
      questionId,
      model,
      language
    });
    ElMessage.success(t('datasets.generateSuccess') || '数据集生成成功');
  } catch (error) {
    console.error('生成数据集失败:', error);
    ElMessage.error(error.message || t('datasets.generateFailed') || '生成数据集失败');
  } finally {
    processingQuestions.value[questionId] = false;
  }
};
</script>

<style scoped>
.question-tree-view {
  padding: 0;
}

.tree-container {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  overflow: hidden;
}

.uncategorized-questions {
  margin-top: 0;
  margin-left: 0;
}

.tags-block {
  margin-top: 0;
}

.tag-row {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.tag-row-root {
  background-color: #3366cc; /* 更深的蓝色，接近 Next 版 */
  color: #ffffff;
}

.tag-row-root:hover {
  background-color: #2a55b3;
}

.tag-row-root .tag-icon {
  color: #ffffff;
}

.tag-row-root .tag-count {
  background-color: rgba(255, 255, 255, 0.2);
  border-color: transparent;
  color: #ffffff;
}

.tag-row:not(.tag-row-root) {
  background-color: var(--el-bg-color);
}

.tag-row:not(.tag-row-root):hover {
  background-color: var(--el-fill-color-light);
}

.tag-icon {
  margin-right: 8px;
  font-size: 16px;
  color: #3366cc;
}

.tag-label {
  font-size: 14px;
  font-weight: 600;
}

.tag-count {
  margin-left: 8px;
  font-weight: normal;
  border: none;
  font-size: 11px;
  height: 18px;
  line-height: 18px;
  padding: 0 6px;
  background-color: #333333;
  color: #ffffff;
}

.tag-row-root .tag-count {
  background-color: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.tag-expand-icon {
  margin-left: auto;
}

.question-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-bottom: 1px solid var(--el-border-color-extra-light);
  background-color: var(--el-bg-color);
}

.question-main {
  display: flex;
  align-items: flex-start;
  flex: 1;
  min-width: 0;
  gap: 12px;
}

.question-icon {
  color: #3366cc;
  font-size: 16px;
  margin-top: 2px;
}

.question-text {
  flex: 1;
  min-width: 0;
}

.question-title {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  line-height: 1.4;
  color: var(--el-text-color-primary);
  white-space: normal;
  word-break: break-word;
}

.answer-count-tag {
  flex-shrink: 0;
  height: 18px;
  line-height: 18px;
  font-size: 11px;
}

.question-meta {
  margin-top: 2px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.question-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 16px;
}
</style>

