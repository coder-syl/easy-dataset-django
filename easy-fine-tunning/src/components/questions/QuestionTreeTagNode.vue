<template>
  <div class="tag-node">
    <!-- 标签行 -->
    <div
      class="tag-row"
      :class="{ 'tag-row-root': level === 0 }"
      :style="{ paddingLeft: (16 + level * 24) + 'px' }"
      @click="handleToggle"
    >
      <el-icon class="tag-icon">
        <Folder />
      </el-icon>
      <span class="tag-label">{{ tag.label }}</span>
      <el-tag
        v-if="totalQuestions > 0"
        size="small"
        type="info"
        effect="plain"
        class="tag-count"
      >
        {{ t('datasets.questionCount', { count: totalQuestions }) }}
      </el-tag>
      <el-icon class="tag-expand-icon">
        <ArrowDown v-if="isExpanded" />
        <ArrowRight v-else />
      </el-icon>
    </div>

    <!-- 子标签 + 问题列表 -->
    <transition name="el-collapse-transition">
      <div v-show="isExpanded" class="tag-children">
        <!-- 子标签 -->
        <QuestionTreeTagNode
          v-for="child in tag.child || []"
          :key="child.label"
          :tag="child"
          :level="level + 1"
          :is-expanded="expandedTags[child.label]"
          :expanded-tags="expandedTags"
          :questions-by-tag="questionsByTag"
          :tag-question-counts="tagQuestionCounts"
          :selected-questions="selectedQuestions"
          :processing-questions="processingQuestions"
          :project-id="projectId"
          :t="t"
          @toggle-tag="$emit('toggle-tag', $event)"
          @select-question="$emit('select-question', $event)"
          @delete-question="$emit('delete-question', $event)"
          @edit-question="$emit('edit-question', $event)"
          @generate-dataset="$emit('generate-dataset', $event)"
        />

        <!-- 当前标签下的问题 -->
        <div v-if="questions.length > 0" class="question-list">
          <div
            v-for="(q, index) in questions"
            :key="q.id"
            class="question-item"
            :style="{ paddingLeft: (16 + (level + 1) * 24) + 'px' }"
          >
            <div class="question-main">
              <el-checkbox
                :model-value="selectedQuestions.includes(q.id)"
                @change="emitSelect(q.id)"
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
                  size="small"
                  :icon="Edit"
                  :loading="processingQuestions[q.id]"
                  @click.stop="emitEdit(q)"
                />
              </el-tooltip>
              <el-tooltip :content="t('datasets.generateDataset')">
                <el-button
                  size="small"
                  :icon="MagicStick"
                  :loading="processingQuestions[q.id]"
                  @click.stop="emitGenerate(q)"
                />
              </el-tooltip>
              <el-tooltip :content="t('common.delete')">
                <el-button
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
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Folder, ArrowDown, ArrowRight, QuestionFilled, Edit, Delete, MagicStick } from '@element-plus/icons-vue';

const props = defineProps({
  tag: {
    type: Object,
    required: true
  },
  level: {
    type: Number,
    default: 0
  },
  isExpanded: {
    type: Boolean,
    default: false
  },
  expandedTags: {
    type: Object,
    required: true
  },
  questionsByTag: {
    type: Object,
    required: true
  },
  tagQuestionCounts: {
    type: Object,
    required: true
  },
  selectedQuestions: {
    type: Array,
    default: () => []
  },
  processingQuestions: {
    type: Object,
    required: true
  },
  projectId: {
    type: String,
    required: true
  },
  t: {
    type: Function,
    required: true
  }
});

const emit = defineEmits([
  'toggle-tag',
  'select-question',
  'delete-question',
  'edit-question',
  'generate-dataset'
]);

const questions = computed(() => props.questionsByTag[props.tag.label] || []);
const totalQuestions = computed(() => props.tagQuestionCounts[props.tag.label] || 0);

const handleToggle = () => {
  emit('toggle-tag', props.tag.label);
};

const emitSelect = (id) => {
  emit('select-question', id);
};

const emitDelete = (id) => {
  emit('delete-question', id);
};

const emitEdit = (q) => {
  emit('edit-question', q);
};

const emitGenerate = (q) => {
  emit('generate-dataset', q);
};
</script>

<style scoped>
.tag-node {
  margin-bottom: 0;
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
  background-color: #3366cc;
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

.tag-row:not(.tag-row-root) .tag-label {
  font-weight: 400;
  color: var(--el-text-color-primary);
}

.tag-row:not(.tag-row-root) .tag-expand-icon {
  color: var(--el-text-color-secondary);
}

.tag-icon {
  margin-right: 8px;
  font-size: 16px;
  color: #3366cc; /* 子级文件夹图标保持蓝色 */
}

.tag-label {
  font-size: 14px;
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

.tag-children {
  margin-left: 0;
  margin-top: 0;
}

.question-list {
  margin-top: 0;
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


