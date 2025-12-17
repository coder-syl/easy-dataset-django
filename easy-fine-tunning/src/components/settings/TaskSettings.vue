<template>
  <div class="task-settings">
    <el-skeleton v-if="loading" :rows="10" animated />

    <div v-else class="settings-content">
      <!-- 文本分块设置 -->
      <el-card class="settings-card">
        <template #header>
          <h3>{{ $t('settings.textSplitSettings', '文本分块设置') }}</h3>
        </template>

        <el-form :model="taskSettings" label-width="150px" label-position="left">
          <!-- 分块策略选择 -->
          <el-form-item :label="$t('settings.splitType', '分块策略')">
            <el-select v-model="taskSettings.splitType" style="width: 100%">
              <el-option value="markdown" :label="$t('settings.splitTypeMarkdown', '文档结构分块（Markdown）')">
                <div>
                  <div style="font-weight: 500">{{ $t('settings.splitTypeMarkdown', '文档结构分块（Markdown）') }}</div>
                  <div style="font-size: 12px; color: #909399; margin-top: 4px">
                    {{ $t('settings.splitTypeMarkdownDesc', '根据文档中的标题自动分割文本') }}
                  </div>
                </div>
              </el-option>
              <el-option value="recursive" :label="$t('settings.splitTypeRecursive', '文本结构分块（自定义分隔符）')">
                <div>
                  <div style="font-weight: 500">
                    {{ $t('settings.splitTypeRecursive', '文本结构分块（自定义分隔符）') }}
                  </div>
                  <div style="font-size: 12px; color: #909399; margin-top: 4px">
                    {{ $t('settings.splitTypeRecursiveDesc', '递归地尝试多级分隔符') }}
                  </div>
                </div>
              </el-option>
              <el-option value="text" :label="$t('settings.splitTypeText', '固定长度分块（字符）')">
                <div>
                  <div style="font-weight: 500">{{ $t('settings.splitTypeText', '固定长度分块（字符）') }}</div>
                  <div style="font-size: 12px; color: #909399; margin-top: 4px">
                    {{ $t('settings.splitTypeTextDesc', '按指定分隔符切分文本') }}
                  </div>
                </div>
              </el-option>
              <el-option value="token" :label="$t('settings.splitTypeToken', '固定长度分块（Token）')">
                <div>
                  <div style="font-weight: 500">{{ $t('settings.splitTypeToken', '固定长度分块（Token）') }}</div>
                  <div style="font-size: 12px; color: #909399; margin-top: 4px">
                    {{ $t('settings.splitTypeTokenDesc', '基于 Token 数量分块') }}
                  </div>
                </div>
              </el-option>
              <el-option value="code" :label="$t('settings.splitTypeCode', '程序代码智能分块')">
                <div>
                  <div style="font-weight: 500">{{ $t('settings.splitTypeCode', '程序代码智能分块') }}</div>
                  <div style="font-size: 12px; color: #909399; margin-top: 4px">
                    {{ $t('settings.splitTypeCodeDesc', '根据不同编程语言的语法结构进行智能分块') }}
                  </div>
                </div>
              </el-option>
              <el-option value="custom" :label="$t('settings.splitTypeCustom', '自定义符号分块')">
                <div>
                  <div style="font-weight: 500">{{ $t('settings.splitTypeCustom', '自定义符号分块') }}</div>
                  <div style="font-size: 12px; color: #909399; margin-top: 4px">
                    {{ $t('settings.splitTypeCustomDesc', '根据自定义符号进行文档分割') }}
                  </div>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <!-- Markdown模式设置 -->
          <template v-if="!taskSettings.splitType || taskSettings.splitType === 'markdown'">
            <el-form-item :label="$t('settings.minLength', '最小长度')">
              <el-slider
                v-model="taskSettings.textSplitMinLength"
                :min="100"
                :max="5000"
                :step="100"
                show-input
                show-stops
              />
            </el-form-item>

            <el-form-item :label="$t('settings.maxLength', '最大分割长度')">
              <el-slider
                v-model="taskSettings.textSplitMaxLength"
                :min="2000"
                :max="20000"
                :step="100"
                show-input
                show-stops
              />
            </el-form-item>
          </template>

          <!-- 通用 LangChain 参数设置 -->
          <template v-if="taskSettings.splitType && taskSettings.splitType !== 'markdown'">
            <el-form-item :label="$t('settings.chunkSize', '分块大小')">
              <el-slider
                v-model="taskSettings.chunkSize"
                :min="500"
                :max="20000"
                :step="100"
                show-input
                show-stops
              />
            </el-form-item>

            <el-form-item :label="$t('settings.chunkOverlap', '分块重叠')">
              <el-slider
                v-model="taskSettings.chunkOverlap"
                :min="0"
                :max="1000"
                :step="50"
                show-input
                show-stops
              />
            </el-form-item>
          </template>

          <!-- Text 分块器特殊设置 -->
          <el-form-item
            v-if="taskSettings.splitType === 'text'"
            :label="$t('settings.separator', '分隔符')"
          >
            <el-input
              v-model="taskSettings.separator"
              :placeholder="$t('settings.separatorHelper', '文本分割的分隔符')"
            />
          </el-form-item>

          <!-- 自定义符号分块器特殊设置 -->
          <el-form-item
            v-if="taskSettings.splitType === 'custom'"
            :label="$t('settings.customSeparator', '自定义分隔符')"
          >
            <el-input
              v-model="taskSettings.customSeparator"
              :placeholder="$t('settings.customSeparatorHelper', '文档分割的自定义分隔符')"
            />
          </el-form-item>

          <!-- Code 分块器特殊设置 -->
          <el-form-item
            v-if="taskSettings.splitType === 'code'"
            :label="$t('settings.codeLanguage', '代码语言')"
          >
            <el-select v-model="taskSettings.splitLanguage" style="width: 100%">
              <el-option value="js" label="JavaScript" />
              <el-option value="python" label="Python" />
              <el-option value="java" label="Java" />
              <el-option value="go" label="Go" />
              <el-option value="ruby" label="Ruby" />
              <el-option value="cpp" label="C++" />
              <el-option value="c" label="C" />
              <el-option value="csharp" label="C#" />
              <el-option value="php" label="PHP" />
              <el-option value="rust" label="Rust" />
              <el-option value="typescript" label="TypeScript" />
              <el-option value="swift" label="Swift" />
              <el-option value="kotlin" label="Kotlin" />
              <el-option value="scala" label="Scala" />
            </el-select>
            <div class="el-form-item__help">
              {{ $t('settings.codeLanguageHelper', '代码分割的编程语言') }}
            </div>
          </el-form-item>

          <!-- Recursive 分块器特殊设置 -->
          <template v-if="taskSettings.splitType === 'recursive'">
            <el-form-item :label="$t('settings.separatorsInput', '分隔符输入')">
              <el-input
                v-model="taskSettings.separatorsInput"
                :placeholder="$t('settings.separatorsHelper', '逗号分隔的分隔符列表')"
                @input="handleSeparatorsInput"
              />
              <div class="el-form-item__help">
                {{ $t('settings.separatorsHelper', '逗号分隔的分隔符列表') }}
              </div>
            </el-form-item>

            <el-form-item>
              <div style="display: flex; flex-wrap: wrap; gap: 8px">
                <el-tag v-for="(sep, index) in separatorsArray" :key="index" type="info" size="small">
                  {{ sep }}
                </el-tag>
              </div>
            </el-form-item>
          </template>

          <el-form-item>
            <el-text type="info" size="small">
              {{ $t('settings.textSplitDescription', '调整文本分割的长度范围，影响分割结果的粒度') }}
            </el-text>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 问题生成设置 -->
      <el-card class="settings-card">
        <template #header>
          <h3>{{ $t('settings.questionGenSettings', '问题生成设置') }}</h3>
        </template>

        <el-form :model="taskSettings" label-width="150px" label-position="left">
          <el-form-item :label="$t('settings.questionGenLength', '问题生成长度')">
            <el-slider
              v-model="taskSettings.questionGenerationLength"
              :min="10"
              :max="1000"
              :step="10"
              show-input
              show-stops
            />
            <div class="el-form-item__help">
              {{ questionGenLengthHelp }}
            </div>
          </el-form-item>

          <el-form-item :label="$t('settings.questionMaskRemovingProbability', '问题掩码移除概率')">
            <el-slider
              v-model="taskSettings.questionMaskRemovingProbability"
              :min="0"
              :max="100"
              :step="5"
              show-input
              show-stops
            />
            <div class="el-form-item__help">
              {{ questionMaskRemovingProbabilityHelp }}
            </div>
          </el-form-item>

          <el-form-item :label="$t('settings.concurrencyLimit', '并发限制')">
            <el-input-number
              v-model="taskSettings.concurrencyLimit"
              :min="1"
              :max="100"
              style="width: 100%"
            />
            <div class="el-form-item__help">
              {{ $t('settings.concurrencyLimitHelper', '最大并发请求数') }}
            </div>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- PDF设置 -->
      <el-card class="settings-card">
        <template #header>
          <h3>{{ $t('settings.pdfSettings', 'PDF设置') }}</h3>
        </template>

        <el-form :model="taskSettings" label-width="150px" label-position="left">
          <el-form-item :label="$t('settings.minerUToken', 'MinerU Token')">
            <el-input
              v-model="taskSettings.minerUToken"
              type="password"
              show-password
              :placeholder="$t('settings.minerUHelper', 'MinerU PDF处理的Token')"
            />
          </el-form-item>

          <el-form-item :label="$t('settings.minerULocalUrl', 'MinerU本地URL')">
            <el-input v-model="taskSettings.minerULocalUrl" />
          </el-form-item>

          <el-form-item :label="$t('settings.visionConcurrencyLimit', '视觉并发限制')">
            <el-input-number
              v-model="taskSettings.visionConcurrencyLimit"
              :min="1"
              :max="100"
              style="width: 100%"
            />
          </el-form-item>
        </el-form>
      </el-card>

      <!-- HuggingFace设置 -->
      <el-card class="settings-card">
        <template #header>
          <h3>{{ $t('settings.huggingfaceSettings', 'HuggingFace设置') }}</h3>
        </template>

        <el-form :model="taskSettings" label-width="150px" label-position="left">
          <el-form-item :label="$t('settings.huggingfaceToken', 'HuggingFace Token')">
            <el-input
              v-model="taskSettings.huggingfaceToken"
              type="password"
              show-password
            />
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 多轮对话数据集设置 -->
      <el-card class="settings-card">
        <template #header>
          <h3>{{ $t('settings.multiTurnSettings', '多轮对话数据集设置') }}</h3>
        </template>

        <el-form :model="taskSettings" label-width="150px" label-position="left">
          <el-form-item :label="$t('settings.multiTurnSystemPrompt', '系统提示词')">
            <el-input
              v-model="taskSettings.multiTurnSystemPrompt"
              type="textarea"
              :rows="3"
              :placeholder="$t('settings.multiTurnSystemPromptHelper', '设定AI助手的身份和行为规范')"
            />
          </el-form-item>

          <el-form-item :label="$t('settings.multiTurnScenario', '对话场景')">
            <el-input
              v-model="taskSettings.multiTurnScenario"
              :placeholder="$t('settings.multiTurnScenarioHelper', '描述对话的具体场景和目标')"
            />
          </el-form-item>

          <el-form-item :label="$t('settings.multiTurnRounds', '对话轮数')">
            <el-slider
              v-model="taskSettings.multiTurnRounds"
              :min="2"
              :max="8"
              :step="1"
              show-input
              show-stops
            />
            <div class="el-form-item__help">
              {{ multiTurnRoundsHelp }}
            </div>
          </el-form-item>

          <el-form-item :label="$t('settings.multiTurnRoleA', '角色A设定（用户）')">
            <el-input
              v-model="taskSettings.multiTurnRoleA"
              type="textarea"
              :rows="2"
              :placeholder="$t('settings.multiTurnRoleAHelper', '定义用户角色的身份和特征')"
            />
          </el-form-item>

          <el-form-item :label="$t('settings.multiTurnRoleB', '角色B设定（助手）')">
            <el-input
              v-model="taskSettings.multiTurnRoleB"
              type="textarea"
              :rows="2"
              :placeholder="$t('settings.multiTurnRoleBHelper', '定义助手角色的身份和特征')"
            />
          </el-form-item>

          <el-form-item>
            <el-text type="info" size="small">
              {{ $t('settings.multiTurnDescription', '多轮对话配置用于生成连贯的多轮对话数据集') }}
            </el-text>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 固定底部保存按钮 -->
      <div class="save-button-container">
        <el-button
          type="primary"
          :icon="Document"
          :loading="saving"
          size="large"
          @click="handleSave"
        >
          {{ $t('settings.saveTaskConfig', '保存任务配置') }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { Document } from '@element-plus/icons-vue';
import { fetchTaskSettings, updateTaskSettings } from '../../api/task';
import { DEFAULT_SETTINGS } from '../../constants/setting';

const props = defineProps({
  projectId: {
    type: String,
    required: true,
  },
});

const { t } = useI18n();

const taskSettings = ref({ ...DEFAULT_SETTINGS });
const loading = ref(true);
const saving = ref(false);

// 计算属性：问题生成长度帮助文本
const questionGenLengthHelp = computed(() => {
  return `问题生成长度：${taskSettings.value.questionGenerationLength} 个字符生成一个问题`;
});

// 计算属性：问题掩码移除概率帮助文本
const questionMaskRemovingProbabilityHelp = computed(() => {
  return `问题掩码移除概率：${taskSettings.value.questionMaskRemovingProbability}%`;
});

// 计算属性：多轮对话轮数帮助文本
const multiTurnRoundsHelp = computed(() => {
  return `对话轮数：${taskSettings.value.multiTurnRounds} 轮`;
});

// 分隔符数组（用于显示）
const separatorsArray = computed(() => {
  if (taskSettings.value.splitType === 'recursive') {
    return taskSettings.value.separators || taskSettings.value.separatorsInput?.split(',').map((s) => s.trim()) || [];
  }
  return [];
});

// 处理分隔符输入
const handleSeparatorsInput = (value) => {
  if (taskSettings.value.splitType === 'recursive') {
    taskSettings.value.separators = value.split(',').map((s) => s.trim()).filter((s) => s);
  }
};

// 确保 multiTurnRounds 有正确的初始值
watch(
  () => taskSettings.value.multiTurnRounds,
  (newVal) => {
    if (newVal === undefined || newVal === null) {
      taskSettings.value.multiTurnRounds = 3;
    }
  },
  { immediate: true },
);

// 加载任务配置
const loadTaskSettings = async () => {
  try {
    loading.value = true;
    const response = await fetchTaskSettings(props.projectId);
    
    // HTTP 拦截器已经解包了 { code, message, data } 格式，直接返回 data
    // 所以 response 就是配置数据对象
    const settings = response || {};

    // 合并默认值
    taskSettings.value = {
      ...DEFAULT_SETTINGS,
      ...settings,
    };

    // 确保 multiTurnRounds 是数字类型
    if (taskSettings.value.multiTurnRounds !== undefined) {
      taskSettings.value.multiTurnRounds = Number(taskSettings.value.multiTurnRounds);
    }

    // 处理分隔符数组
    if (taskSettings.value.splitType === 'recursive') {
      if (taskSettings.value.separators && Array.isArray(taskSettings.value.separators)) {
        taskSettings.value.separatorsInput = taskSettings.value.separators.join(',');
      } else if (taskSettings.value.separatorsInput) {
        taskSettings.value.separators = taskSettings.value.separatorsInput.split(',').map((s) => s.trim());
      }
    }
  } catch (error) {
    console.error('获取任务配置出错:', error);
    ElMessage.error(t('settings.fetchTasksFailed', '获取任务配置失败'));
  } finally {
    loading.value = false;
  }
};

// 保存任务配置
const handleSave = async () => {
  try {
    saving.value = true;

    // 确保数组类型的数据被正确处理
    const settingsToSave = { ...taskSettings.value };

    // 确保递归分块的分隔符数组存在
    if (settingsToSave.splitType === 'recursive' && settingsToSave.separatorsInput) {
      if (!settingsToSave.separators || !Array.isArray(settingsToSave.separators)) {
        settingsToSave.separators = settingsToSave.separatorsInput.split(',').map((item) => item.trim());
      }
    }

    await updateTaskSettings(props.projectId, settingsToSave);
    ElMessage.success(t('settings.saveSuccess', '保存成功'));
  } catch (error) {
    console.error('保存任务配置出错:', error);
    ElMessage.error(t('settings.saveTasksFailed', '保存任务配置失败'));
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  loadTaskSettings();
});
</script>

<style scoped>
.task-settings {
  padding-bottom: 80px; /* 为固定按钮留出空间 */
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-card {
  margin-bottom: 20px;
}

.settings-card h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.save-button-container {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: center;
  z-index: 1000;
}

.save-button-container .el-button {
  min-width: 200px;
}

:deep(.el-form-item__help) {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
</style>

