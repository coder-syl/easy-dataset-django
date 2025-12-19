<template>
  <div>
    <div
      v-for="tag in tags"
      :key="tag.id"
      class="tag-block"
    >
      <div
        class="tag-row"
        :style="{ paddingLeft: `${levelPadding(level)}px` }"
        @click="() => $emit('toggle', tag.id)"
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
            {{ getTotalSubTagsCountLocal(tag.children) }} {{ t('distill.subTags') }}
          </el-tag>

          <el-tag
            v-if="totalQuestionsLocal(tag) > 0"
            size="small"
            type="success"
            effect="plain"
            class="tag-chip"
          >
            {{ totalQuestionsLocal(tag) }} {{ t('distill.questions') }}
          </el-tag>
        </div>

        <div class="tag-actions">
          <el-tooltip :content="t('distill.generateQuestions')" placement="top">
            <el-button
              link
              size="small"
              @click.stop="$emit('generate-questions', tag)"
            >
              <el-icon><QuestionFilled /></el-icon>
            </el-button>
          </el-tooltip>

          <el-tooltip :content="t('distill.generateSubTags')" placement="top">
            <el-button
              link
              size="small"
              @click.stop="$emit('generate-sub-tags', tag)"
            >
              <el-icon><Plus /></el-icon>
            </el-button>
          </el-tooltip>

          <el-dropdown
            trigger="click"
            @command="(cmd) => $emit('tag-menu-command', cmd, tag)"
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

          <el-icon
            v-if="tag.children && tag.children.length"
            class="expand-icon"
          >
            <ArrowDown v-if="expandedTags[tag.id]" />
            <ArrowRight v-else />
          </el-icon>
        </div>
      </div>

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
              <template v-if="(tagQuestions[tag.id] || []).length > 0">
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
                        @click.stop="$emit('generate-dataset', q)"
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
                        @click.stop="$emit('view-multi-turn-dataset', q)"
                      >
                        <el-icon><View /></el-icon>
                      </el-button>
                    </el-tooltip>
                    <el-tooltip
                      :content="t('questions.generateMultiTurnDataset', { defaultValue: '生成多轮对话数据集' })"
                      placement="top"
                    >
                      <el-button
                        link
                        size="small"
                        :loading="processingMultiTurnQuestions[q.id]"
                        @click.stop="$emit('generate-multi-turn-dataset', q)"
                      >
                        <el-icon><ChatDotRound /></el-icon>
                      </el-button>
                    </el-tooltip>
                    <el-tooltip :content="t('common.delete')" placement="top">
                      <el-button
                        link
                        size="small"
                        @click.stop="$emit('delete-question', q.id)"
                      >
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </el-tooltip>
                  </div>
                </div>
              </template>
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

      <transition name="fade">
        <div
          v-if="expandedTags[tag.id] && tag.children && tag.children.length > 0"
          class="children-container"
        >
          <DistillTreeChild
            :tags="tag.children"
            :level="level + 1"
            :expanded-tags="expandedTags"
            :tag-questions="tagQuestions"
            :loading-questions="loadingQuestions"
            :processing-questions="processingQuestions"
            :processing-multi-turn-questions="processingMultiTurnQuestions"
            :all-questions="allQuestions"
            @toggle="$emit('toggle', $event)"
            @generate-questions="$emit('generate-questions', $event)"
            @generate-sub-tags="$emit('generate-sub-tags', $event)"
            @generate-dataset="$emit('generate-dataset', $event)"
            @generate-multi-turn-dataset="$emit('generate-multi-turn-dataset', $event)"
            @delete-question="$emit('delete-question', $event)"
            @tag-menu-command="$emit('tag-menu-command', $event[0], $event[1])"
          />
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
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

const props = defineProps({
  tags: { type: Array, required: true },
  level: { type: Number, required: true },
  expandedTags: { type: Object, required: true },
  tagQuestions: { type: Object, required: true },
  loadingQuestions: { type: Object, required: true },
  processingQuestions: { type: Object, required: true },
  processingMultiTurnQuestions: { type: Object, required: true },
  allQuestions: { type: Array, required: true },
});

defineEmits([
  'toggle',
  'generate-questions',
  'generate-sub-tags',
  'generate-dataset',
  'generate-multi-turn-dataset',
  'view-multi-turn-dataset',
  'delete-question',
  'tag-menu-command',
]);

const { t } = useI18n();

const levelPadding = (level) => 24 + level * 16;

const getChildrenQuestionsCountLocal = (childrenTags) => {
  let count = 0;
  (childrenTags || []).forEach((child) => {
    if (props.tagQuestions[child.id] && props.tagQuestions[child.id].length > 0) {
      count += props.tagQuestions[child.id].length;
    } else {
      count += props.allQuestions.filter((q) => q.label === child.label).length;
    }
    if (child.children && child.children.length > 0) {
      count += getChildrenQuestionsCountLocal(child.children);
    }
  });
  return count;
};

const getCurrentTagQuestionsCountLocal = (tag) => {
  if (props.tagQuestions[tag.id] && props.tagQuestions[tag.id].length > 0) {
    return props.tagQuestions[tag.id].length;
  }
  return props.allQuestions.filter((q) => q.label === tag.label).length;
};

const totalQuestionsLocal = (tag) =>
  getCurrentTagQuestionsCountLocal(tag) + getChildrenQuestionsCountLocal(tag.children || []);

const getTotalSubTagsCountLocal = (childrenTags) => {
  let count = childrenTags.length;
  (childrenTags || []).forEach((child) => {
    if (child.children && child.children.length > 0) {
      count += getTotalSubTagsCountLocal(child.children);
    }
  });
  return count;
};
</script>

<style scoped>
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
}

.tag-folder {
  color: var(--el-color-primary);
}

.tag-label {
  font-size: 14px;
  color: var(--el-text-color-primary);
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
  align-items:center;
  gap: 4px;
  margin-left: 8px;
}

.children-container {
  margin-top: 4px;
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


