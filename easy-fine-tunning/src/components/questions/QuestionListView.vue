<template>
  <div class="question-list-view">
    <!-- 问题表格 -->
    <el-table
      :data="questionsList"
      style="width: 100%"
      :empty-text="$t('questions.noQuestions')"
      border
    >
      <!-- 选择列 -->
      <el-table-column width="55">
        <template #header>
          <el-checkbox
            :model-value="isAllSelected"
            :indeterminate="isIndeterminate"
            @change="handleSelectAllChange"
          />
        </template>
        <template #default="{ row }">
          <el-checkbox
            :model-value="isQuestionSelected(row.id)"
            @change="val => handleSelectQuestion(row.id, val)"
            @click.stop
          />
        </template>
      </el-table-column>

      <!-- 问题列 -->
      <el-table-column :label="$t('datasets.question')" min-width="400" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="question-cell">
            <div class="question-text">
              {{ row.question }}
            </div>
            <el-tag
              v-if="(row.datasetCount || row.dataset_count || 0) > 0"
              size="small"
              type="primary"
              effect="plain"
              class="answer-count-tag"
            >
              {{ $t('datasets.answerCount', { count: row.datasetCount || row.dataset_count || 0 }) }}
            </el-tag>
          </div>
        </template>
      </el-table-column>

      <!-- 标签列 -->
      <el-table-column :label="$t('common.label')" width="160">
        <template #default="{ row }">
          <div class="label-cell">
            <el-tag v-if="row.label" size="small" type="primary" effect="plain">
              {{ row.label }}
            </el-tag>
            <span v-else class="no-tag">{{ $t('datasets.noTag') }}</span>
          </div>
        </template>
      </el-table-column>

      <!-- 数据源列 -->
      <el-table-column :label="$t('common.dataSource')" min-width="200">
        <template #default="{ row }">
          <div class="source-cell">
            <el-tooltip :content="getChunkTitle(row.chunk?.content)">
              <el-tag size="small" type="info" effect="plain">
                {{ getSourceLabel(row) }}
              </el-tag>
            </el-tooltip>
          </div>
        </template>
      </el-table-column>

      <!-- 操作列 -->
      <el-table-column :label="$t('common.actions')" width="200" fixed="right">
        <template #default="{ row }">
          <div class="question-actions" @click.stop>
            <el-tooltip :content="$t('common.edit')">
              <el-button
                size="small"
                :icon="Edit"
                :loading="processingQuestions[row.id]"
                @click="handleEdit(row)"
              />
            </el-tooltip>
            <el-tooltip :content="$t('datasets.generateDataset')">
              <el-button
                size="small"
                :icon="MagicStick"
                :loading="processingQuestions[row.id]"
                @click="handleGenerateDataset(row)"
              />
            </el-tooltip>
            <el-tooltip v-if="!(row.imageId || row.image_id)" :content="$t('questions.generateMultiTurn')">
              <el-button
                size="small"
                :icon="ChatLineRound"
                :loading="processingQuestions[`${row.id}_multi`]"
                @click="handleGenerateMultiTurn(row)"
              />
            </el-tooltip>
            <el-tooltip :content="$t('common.delete')">
              <el-button
                size="small"
                type="danger"
                :icon="Delete"
                :loading="processingQuestions[row.id]"
                @click="handleDelete(row.id)"
              />
            </el-tooltip>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div v-if="questionsList.length > 0" class="pagination-wrapper">
      <div class="pagination-controls">
        <el-pagination
          v-model:current-page="localCurrentPage"
          :page-size="pageSize"
          :total="totalCount"
          :page-sizes="[10, 20, 50, 100]"
          layout="sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
        <div class="pagination-info">
          <span>
            {{ totalCount > 0
              ? $t('common.totalItems', { count: totalCount }) || `共 ${totalCount} 条`
              : $t('common.currentPageItems', { count: questionsList.length }) || `当前页 ${questionsList.length} 条`
            }}
          </span>
          <span v-if="totalQuestions > 0">
            {{ $t('common.pageInfo', { current: currentPage, total: totalQuestions }) || `第 ${currentPage}/${totalQuestions} 页` }}
          </span>
        </div>
        <div class="jump-to">
          <span>{{ $t('common.jumpTo') || '跳转到' }}:</span>
          <el-input-number
            v-model="jumpPage"
            :min="1"
            :max="totalQuestions"
            size="small"
            controls-position="right"
            @keyup.enter="handleJumpToPage"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { Edit, Delete, MagicStick, ChatLineRound } from '@element-plus/icons-vue';
import { generateDataset } from '@/api/dataset';
import { generateImageDataset } from '@/api/images';
import { createConversation } from '@/api/conversation';
import { fetchTaskSettings } from '@/api/task';
import { useModelStore } from '@/stores/model';

const props = defineProps({
  questions: {
    type: Array,
    default: () => []
  },
  currentPage: {
    type: Number,
    default: 1
  },
  totalQuestions: {
    type: Number,
    default: 0
  },
  totalCount: {
    type: Number,
    default: 0
  },
  pageSize: {
    type: Number,
    default: 10
  },
  selectedQuestions: {
    type: Array,
    default: () => []
  },
  projectId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['page-change', 'size-change', 'select-question', 'delete-question', 'edit-question', 'refresh']);

const { t, locale } = useI18n();
const modelStore = useModelStore();

const localCurrentPage = ref(props.currentPage);
const jumpPage = ref(1);
const processingQuestions = ref({});

// 确保 questions 始终是数组
const questionsList = computed(() => {
  return Array.isArray(props.questions) ? props.questions : [];
});

watch(() => props.currentPage, (val) => {
  localCurrentPage.value = val;
  jumpPage.value = val;
});

// 获取文本块的标题
const getChunkTitle = (content) => {
  if (!content) return '';
  const firstLine = content.split('\n')[0].trim();
  if (firstLine.startsWith('# ')) {
    return firstLine.substring(2);
  } else if (firstLine.length > 0) {
    return firstLine.length > 200 ? firstLine.substring(0, 200) + '...' : firstLine;
  }
  return '';
};

// 获取数据源标签
const getSourceLabel = (question) => {
  const imageId = question.image_id || question.imageId;
  const imageName = question.image_name || question.imageName;
  const chunkName = question.chunk?.name || question.chunk_name;
  if (imageId) {
    return `Image: ${imageName || ''}`;
  }
  return `${t('chunks.title') || '文本块'}: ${chunkName || t('common.unknown') || '未知'}`;
};

// 检查问题是否被选中
const isQuestionSelected = (questionId) => {
  return props.selectedQuestions.includes(questionId);
};

// 是否全选 / 半选状态（交给 QuestionsView 里的逻辑来算，这里只负责转发事件）
const isAllSelected = computed(() => false);
const isIndeterminate = computed(() => false);

// 处理选择问题
const handleSelectQuestion = (questionId, selected) => {
  emit('select-question', questionId, selected);
};

// 处理全选/取消全选（让父组件去真正更新 selectedQuestions）
const handleSelectAllChange = () => {
  emit('select-question', null, 'toggle-all');
};

// 处理每页条数变化
const handleSizeChange = (size) => {
  emit('size-change', size);
};

// 处理生成数据集
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
    
    // 判断是否为图片问题
    const imageId = question.imageId || question.image_id;
    const imageName = question.imageName || question.image_name;
    const isImageQuestion = !!imageId;

    if (isImageQuestion) {
      // 图片问题：调用图片数据集生成接口
      await generateImageDataset(props.projectId, {
        imageName,
        question: { question: question.question, id: questionId },
        model,
        language
      });
    } else {
      // 文本问题：调用普通数据集生成接口
      await generateDataset(props.projectId, {
        questionId,
        model,
        language
      });
    }

    ElMessage.success(t('datasets.generateSuccess') || '数据集生成成功');
    emit('refresh');
  } catch (error) {
    console.error('生成数据集失败:', error);
    ElMessage.error(error.message || t('datasets.generateFailed') || '生成数据集失败');
  } finally {
    processingQuestions.value[questionId] = false;
  }
};

// 处理生成多轮对话
const handleGenerateMultiTurn = async (question) => {
  const questionId = question.id;
  const processingKey = `${questionId}_multi`;
  processingQuestions.value[processingKey] = true;

  try {
    // 检查模型
    const model = modelStore.selectedModelInfo;
    if (!model) {
      ElMessage.error(t('datasets.selectModelFirst') || '请先选择模型');
      return;
    }

    // 获取任务配置
    const config = await fetchTaskSettings(props.projectId);
    const configData = config?.data || config || {};
    const multiTurnConfig = {
      systemPrompt: configData.multiTurnSystemPrompt,
      scenario: configData.multiTurnScenario,
      rounds: parseInt(configData.multiTurnRounds, 10),
      roleA: configData.multiTurnRoleA,
      roleB: configData.multiTurnRoleB
    };

    // 检查配置
    if (
      !multiTurnConfig.scenario ||
      !multiTurnConfig.roleA ||
      !multiTurnConfig.roleB ||
      !multiTurnConfig.rounds ||
      multiTurnConfig.rounds < 1
    ) {
      ElMessage.error(t('questions.multiTurnNotConfigured') || '请先在项目设置中配置多轮对话相关参数');
      return;
    }

    // 调用多轮对话生成API
    await createConversation(props.projectId, {
      questionId,
      ...multiTurnConfig,
      model
    });

    ElMessage.success(t('questions.multiTurnGenerated') || '多轮对话数据集生成成功！');
    emit('refresh');
  } catch (error) {
    console.error('生成多轮对话数据集失败:', error);
    ElMessage.error(error.message || '生成多轮对话数据集失败');
  } finally {
    processingQuestions.value[processingKey] = false;
  }
};

// 处理页面变化
const handlePageChange = (page) => {
  localCurrentPage.value = page;
  emit('page-change', page);
};

// 处理跳转到指定页面
const handleJumpToPage = () => {
  if (jumpPage.value >= 1 && jumpPage.value <= props.totalQuestions) {
    handlePageChange(jumpPage.value);
  }
};

// 处理编辑
const handleEdit = (row) => {
  emit('edit-question', row);
};

// 处理删除
const handleDelete = (questionId) => {
  emit('delete-question', questionId);
};
</script>

<style scoped>
.question-list-view {
  padding: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: var(--el-bg-color-page);
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-label {
  min-width: 120px;
  display: none;
}

.header-source {
  min-width: 150px;
  display: none;
}

.header-actions {
  width: 160px;
  text-align: center;
}

@media (min-width: 600px) {
  .header-label {
    display: block;
  }
}

@media (min-width: 960px) {
  .header-source {
    display: block;
  }
}

.empty-state {
  padding: 40px 0;
}

.questions-list {
  background-color: var(--el-bg-color);
  border-radius: 4px;
  overflow: hidden;
}

.question-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 12px;
  transition: background-color 0.2s;
}

.question-item:hover {
  background-color: var(--el-fill-color-light);
}

.question-item.selected {
  background-color: var(--el-color-primary-light-9);
}

.question-content {
  flex: 1;
  min-width: 0;
  margin-right: 16px;
}

.question-text {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.question-meta-mobile {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  display: block;
}

@media (min-width: 600px) {
  .question-meta-mobile {
    display: none;
  }
}

.question-label {
  min-width: 120px;
  display: none;
}

@media (min-width: 600px) {
  .question-label {
    display: block;
  }
}

.no-tag {
  font-size: 12px;
  color: var(--el-text-color-disabled);
}

.question-source {
  min-width: 150px;
  display: none;
}

@media (min-width: 960px) {
  .question-source {
    display: block;
  }
}

.question-actions {
  width: 160px;
  display: flex;
  justify-content: center;
  gap: 4px;
  flex-shrink: 0;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 24px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 16px;
}

.pagination-info {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.jump-to {
  display: flex;
  align-items: center;
  gap: 8px;
}

.jump-to .el-input-number {
  width: 80px;
}
</style>
