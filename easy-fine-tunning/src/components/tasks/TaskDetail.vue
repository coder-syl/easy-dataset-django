<template>
  <div v-if="detail" class="task-detail">
    <h4 class="detail-title">{{ $t('tasks.detail', '任务详情') }}</h4>

    <!-- 如果是对象，显示结构化信息 -->
    <div v-if="typeof displayDetail === 'object' && displayDetail !== null && displayDetail" class="detail-content">
      <!-- 当前步骤 -->
      <div v-if="displayDetail && displayDetail.stepInfo" class="detail-item">
        <span class="detail-label">{{ $t('tasks.detail.stepInfo', '当前步骤') }}:</span>
        <span class="detail-value">{{ displayDetail.stepInfo }}</span>
      </div>

      <!-- 当前处理 -->
      <div v-if="displayDetail && displayDetail.current" class="detail-item">
        <span class="detail-label">{{ $t('tasks.detail.current', '当前处理') }}:</span>
        <span class="detail-value">
          <span v-if="displayDetail.current.fileName">{{ displayDetail.current.fileName }} </span>
          <span v-if="displayDetail.current.processedPage && displayDetail.current.totalPage">
            ({{ displayDetail.current.processedPage }}/{{ displayDetail.current.totalPage }} {{ $t('tasks.detail.pages', '页') }})
          </span>
          <span v-if="displayDetail.current.chunksGenerated !== undefined">
            - {{ $t('tasks.detail.chunksGenerated', '生成文本块') }}: {{ displayDetail.current.chunksGenerated }}
          </span>
        </span>
        <el-tag
          v-if="displayDetail.current.status"
          :type="displayDetail.current.status === 'completed' ? 'success' : 'warning'"
          size="small"
          style="margin-left: 8px"
        >
          {{ getStatusLabel(displayDetail.current.status) }}
        </el-tag>
      </div>

      <!-- LLM调用详情 -->
      <div v-if="displayDetail && displayDetail.llmCall" class="llm-call-detail">
        <h5 class="llm-call-title">{{ $t('tasks.detail.llmCall', '大模型调用详情') }}</h5>
        <div class="llm-call-content">
          <div class="detail-item">
            <span class="detail-label">{{ $t('tasks.detail.provider', '提供商') }}:</span>
            <span class="detail-value">{{ displayDetail.llmCall.provider || '-' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">{{ $t('tasks.detail.model', '模型') }}:</span>
            <span class="detail-value">{{ displayDetail.llmCall.model || '-' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">{{ $t('tasks.detail.action', '操作') }}:</span>
            <span class="detail-value">{{ displayDetail.llmCall.action || '-' }}</span>
          </div>
          <div v-if="displayDetail.llmCall.tocLength !== undefined" class="detail-item">
            <span class="detail-label">{{ $t('tasks.detail.tocLength', '目录长度') }}:</span>
            <span class="detail-value">{{ displayDetail.llmCall.tocLength }} 字符</span>
          </div>
          <div v-if="displayDetail.llmCall.status" class="detail-item">
            <span class="detail-label">{{ $t('tasks.detail.status', '状态') }}:</span>
            <el-tag
              :type="detail.llmCall.status === 'completed' ? 'success' : 'warning'"
              size="small"
            >
              {{ getStatusLabel(displayDetail.llmCall.status) }}
            </el-tag>
          </div>
          <div v-if="displayDetail.llmCall.tagsGenerated !== undefined" class="detail-item">
            <span class="detail-label">{{ $t('tasks.detail.tagsGenerated', '生成标签数') }}:</span>
            <span class="detail-value">{{ displayDetail.llmCall.tagsGenerated }}</span>
          </div>
          <div v-if="displayDetail.llmCall.startTime" class="detail-item">
            <span class="detail-label">{{ $t('tasks.detail.startTime', '开始时间') }}:</span>
            <span class="detail-value">{{ new Date(displayDetail.llmCall.startTime).toLocaleString() }}</span>
          </div>
          <div v-if="displayDetail.llmCall.endTime" class="detail-item">
            <span class="detail-label">{{ $t('tasks.detail.endTime', '结束时间') }}:</span>
            <span class="detail-value">{{ new Date(displayDetail.llmCall.endTime).toLocaleString() }}</span>
          </div>
          <div v-if="displayDetail.llmCall.endpoint" class="detail-item">
            <span class="detail-label">{{ $t('tasks.detail.endpoint', 'API端点') }}:</span>
            <span class="detail-value endpoint-value">{{ displayDetail.llmCall.endpoint }}</span>
          </div>
        </div>
      </div>

      <!-- 文件进度 -->
      <div v-if="detail.processedFiles !== undefined && detail.totalFiles !== undefined" class="detail-item">
        <span class="detail-label">{{ $t('tasks.detail.files', '文件进度') }}:</span>
        <span class="detail-value">{{ detail.processedFiles }} / {{ detail.totalFiles }}</span>
      </div>

      <!-- 已完成列表 -->
      <div v-if="displayDetail.finishedList && Array.isArray(displayDetail.finishedList) && displayDetail.finishedList.length > 0" class="finished-list">
        <h5 class="finished-list-title">{{ $t('tasks.detail.finishedFiles', '已完成/已处理') }}:</h5>
        <div class="finished-items">
          <div v-for="(item, idx) in displayDetail.finishedList" :key="idx" class="finished-item">
            <div class="finished-item-header">
              <el-tag
                :type="item.status === 'error' ? 'danger' : 'success'"
                size="small"
              >
                {{ item.status || 'success' }}
              </el-tag>
              <div style="display:flex;flex-direction:column;">
                <span class="finished-item-name">
                {{
                    // prefer first generated question text if available
                    (item.questions && item.questions.length > 0 && (item.questions[0].question || item.questions[0])) 
                      || item.fileName
                      || item.chunkName
                      || item.imageName
                      || item.questionSnippet
                      || item.chunkId
                      || item.questionId
                      || item.imageId
                      || $t('tasks.detail.item', '条目')
                }}
                </span>
                <span v-if="item.questionSnippet" class="finished-item-sub" style="font-size:12px;color:var(--el-text-color-secondary);margin-top:4px;">
                  {{ item.questionSnippet }}
                </span>
              </div>
              <span v-if="item.error" class="finished-item-error" style="margin-left:8px;">{{ item.error }}</span>
            </div>
            <div v-if="item.llm" class="finished-item-llm">
              <h6>{{ $t('tasks.detail.llmCall', '大模型调用详情') }}</h6>
              <div class="detail-item">
                <span class="detail-label">{{ $t('tasks.detail.provider', '提供商') }}:</span>
                <span class="detail-value">{{ item.llm.provider || '-' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">{{ $t('tasks.detail.model', '模型') }}:</span>
                <span class="detail-value">{{ item.llm.model || '-' }}</span>
              </div>
              <div v-if="item.llm.promptPreview" class="detail-item">
                <span class="detail-label">{{ $t('tasks.detail.prompt', '提示词') }}:</span>
                <span class="detail-value prompt-value">{{ item.llm.promptPreview }}</span>
              </div>
              <div v-if="item.llm.answerPreview" class="detail-item">
                <span class="detail-label">{{ $t('tasks.detail.answer', '回答') }}:</span>
                <span class="detail-value answer-value">{{ item.llm.answerPreview }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 错误列表 -->
      <div v-if="displayDetail.errorList && Array.isArray(displayDetail.errorList) && displayDetail.errorList.length > 0" class="error-list">
        <h5 class="error-list-title">{{ $t('tasks.detail.errors', '错误信息') }}:</h5>
        <ul class="error-items">
          <li v-for="(error, idx) in detail.errorList" :key="idx" class="error-item">
            {{ error }}
          </li>
        </ul>
      </div>

      <!-- 处理日志 -->
      <div v-if="displayDetail.logs && Array.isArray(displayDetail.logs) && displayDetail.logs.length > 0" class="logs-section">
        <h5 class="logs-title">{{ $t('tasks.detail.logs', '处理日志') }}</h5>
        <div class="logs-content">
          <div v-for="(log, idx) in detail.logs" :key="idx" class="log-item">
            <span class="log-time">{{ log.time ? new Date(log.time).toLocaleTimeString() : '' }}</span>
            <el-tag
              :type="getLogTagType(log.level)"
              size="small"
            >
              {{ log.level || 'info' }}
            </el-tag>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>

      <!-- 其他消息 -->
      <div v-if="!displayDetail.stepInfo && !displayDetail.current && !displayDetail.processedFiles && displayDetail.message" class="detail-item">
        <span class="detail-value">{{ displayDetail.message }}</span>
      </div>
    </div>

    <!-- 如果是字符串，直接显示 -->
    <div v-else-if="typeof detail === 'string'" class="detail-content">
      <pre class="detail-text">{{ detail }}</pre>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  task: {
    type: Object,
    required: true,
  },
});

const { t } = useI18n();

// 解析任务详情
const detail = computed(() => {
  const taskDetail = props.task.detail;
  if (!taskDetail) return null;

  try {
    if (typeof taskDetail === 'string') {
      const parsed = JSON.parse(taskDetail);
      return parsed;
    }
    if (typeof taskDetail === 'object') {
      return taskDetail;
    }
  } catch (e) {
    return { message: taskDetail };
  }

  return null;
});

// displayDetail is a mutable copy we can enrich (e.g., add questionSnippet) for rendering
const displayDetail = ref(null);

watch(detail, async (newVal) => {
  if (!newVal) {
    displayDetail.value = null;
    return;
  }
  // deep clone to avoid mutating original
  const cloned = JSON.parse(JSON.stringify(newVal));
  displayDetail.value = cloned;

  // Enrich displayDetail from embedded task.detail data (no network calls).
  try {
    if (displayDetail.value.finishedList && Array.isArray(displayDetail.value.finishedList)) {
      displayDetail.value.finishedList = displayDetail.value.finishedList.map((it) => {
        const copy = { ...it };
        // If handler already embedded questions array, prefer its values
        if (Array.isArray(copy.questions) && copy.questions.length > 0) {
          const q0 = copy.questions[0];
          if (q0) {
            if (typeof q0 === 'object') {
              copy.questionSnippet = copy.questionSnippet || q0.questionSnippet || (q0.questionText ? q0.questionText.slice(0, 100) : '');
              if (!copy.questionText && q0.questionText && q0.questionText.length <= 100) {
                copy.questionText = q0.questionText;
              }
            } else {
              // plain string entry
              copy.questionSnippet = copy.questionSnippet || String(q0).slice(0, 100);
            }
          }
        } else {
          // fallback: if there's questionText or questionSnippet fields, ensure length limit
          if (copy.questionText && !copy.questionSnippet) {
            copy.questionSnippet = String(copy.questionText).slice(0, 100);
          }
        }
        return copy;
      });
    }

    if (displayDetail.value.current) {
      const cur = displayDetail.value.current;
      if (cur.questionText && !cur.questionSnippet) {
        cur.questionSnippet = String(cur.questionText).slice(0, 100);
      } else if (Array.isArray(cur.questions) && cur.questions.length > 0) {
        const q0 = cur.questions[0];
        if (typeof q0 === 'object') {
          cur.questionSnippet = cur.questionSnippet || q0.questionSnippet || (q0.questionText ? q0.questionText.slice(0, 100) : '');
        } else {
          cur.questionSnippet = cur.questionSnippet || String(q0).slice(0, 100);
        }
      }
    }
  } catch (e) {
    // ignore enrichment errors
    console.error('Failed to enrich question names from task.detail', e);
  }
}, { immediate: true });

// 获取状态标签
const getStatusLabel = (status) => {
  if (status === 'processing') return t('tasks.detail.processing', '处理中');
  if (status === 'completed') return t('tasks.detail.completed', '已完成');
  if (status === 'calling') return t('tasks.detail.calling', '调用中');
  return status;
};

// 获取日志标签类型
const getLogTagType = (level) => {
  if (level === 'error') return 'danger';
  if (level === 'success') return 'success';
  if (level === 'warning') return 'warning';
  return 'info';
};
</script>

<style scoped>
.task-detail {
  padding: 12px;
  background: var(--el-bg-color-page);
  border-top: 1px solid var(--el-border-color-lighter);
}

.detail-title {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.detail-content {
  margin-top: 6px;
}

.detail-item {
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
  min-width: 80px;
}

.detail-value {
  font-size: 13px;
  color: var(--el-text-color-primary);
  flex: 1;
}

.endpoint-value {
  word-break: break-all;
  font-size: 12px;
}

.llm-call-detail {
  margin: 12px 0;
  padding: 10px;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
  border: 1px solid var(--el-border-color-lighter);
}

.llm-call-title {
  margin: 0 0 6px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
}

.llm-call-content {
  margin-top: 6px;
}

.finished-list {
  margin: 12px 0;
}

.finished-list-title {
  margin: 0 0 6px 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.finished-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.finished-item {
  padding: 6px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  background: var(--el-bg-color);
}

.finished-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.finished-item-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.finished-item-error {
  font-size: 13px;
  color: var(--el-color-danger);
}

.finished-item-llm {
  margin-top: 6px;
  padding: 6px;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}

.finished-item-llm h6 {
  margin: 0 0 6px 0;
  font-size: 12px;
  font-weight: 600;
}

.prompt-value,
.answer-value {
  white-space: pre-wrap;
  word-break: break-word;
}

.error-list {
  margin: 12px 0;
}

.error-list-title {
  margin: 0 0 6px 0;
  font-size: 13px;
  color: var(--el-color-danger);
}

.error-items {
  margin: 0;
  padding-left: 20px;
}

.error-item {
  font-size: 13px;
  color: var(--el-color-danger);
  margin-bottom: 3px;
}

.logs-section {
  margin: 12px 0;
  padding: 10px;
  background: var(--el-bg-color);
  border-radius: 4px;
  border: 1px solid var(--el-border-color-lighter);
  max-height: 300px;
  overflow-y: auto;
}

.logs-title {
  margin: 0 0 6px 0;
  font-size: 13px;
  font-weight: 600;
}

.logs-content {
  margin-top: 6px;
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 3px;
}

.log-time {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  min-width: 60px;
}

.log-message {
  font-size: 12px;
  flex: 1;
  color: var(--el-text-color-primary);
}

.detail-text {
  margin: 6px 0 0 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  color: var(--el-text-color-primary);
}
</style>

