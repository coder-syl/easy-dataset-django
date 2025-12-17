<template>
  <div class="prompt-settings">
    <!-- 主要分类选择 -->
    <CategoryTabs
      :category-entries="categoryEntries"
      :selected-category="selectedCategory"
      :current-language="currentLanguage"
      @category-change="handleCategoryChange"
    />

    <!-- 左右布局：左侧垂直提示词选择，右侧内容展示 -->
    <el-row :gutter="20">
      <!-- 左侧：垂直 TAB 选择具体提示词 -->
      <el-col :xs="24" :md="8" :lg="6">
        <el-card>
          <PromptList
            :current-category="selectedCategory"
            :current-category-config="currentCategoryConfig"
            :selected-prompt="selectedPrompt"
            :current-language="currentLanguage"
            :is-customized="isCustomized"
            @prompt-select="handlePromptSelect"
          />
        </el-card>
      </el-col>

      <!-- 右侧：提示词内容展示和操作 -->
      <el-col :xs="24" :md="16" :lg="18">
        <PromptDetail
          :current-prompt-config="currentPromptConfig"
          :selected-prompt="selectedPrompt"
          :prompt-content="promptContent"
          :is-customized="isCustomized"
          @edit-click="handleEditButtonClick"
          @delete-click="handleDeleteButtonClick"
        />
      </el-col>
    </el-row>

    <!-- 编辑提示词对话框 -->
    <PromptEditDialog
      :open="editDialog.open"
      :title="editDialog.isNew ? $t('settings.prompts.createCustomPrompt', '创建自定义提示词') : $t('settings.prompts.editPrompt', '编辑提示词')"
      :prompt-type="editDialog.promptType"
      :prompt-key="editDialog.promptKey"
      :content="editDialog.content"
      :loading="loading"
      @close="handleDialogClose"
      @save="handleSavePrompt"
      @restore="handleRestoreDefault"
      @content-change="handleDialogContentChange"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { fetchCustomPrompts, saveCustomPrompt, deleteCustomPrompt, fetchDefaultPrompt } from '../../api/prompt';
import { getLanguageFromPromptKey, shouldShowPrompt } from '../../utils/promptUtils';
import CategoryTabs from './CategoryTabs.vue';
import PromptList from './PromptList.vue';
import PromptDetail from './PromptDetail.vue';
import PromptEditDialog from './PromptEditDialog.vue';

const props = defineProps({
  projectId: {
    type: String,
    required: true,
  },
});

const { locale, t } = useI18n();

// 基础状态
const getInitialLanguage = () => {
  try {
    const lang = locale?.value || locale || 'zh-CN';
    return lang === 'en' ? 'en' : 'zh-CN';
  } catch (error) {
    return 'zh-CN';
  }
};

const currentLanguage = ref(getInitialLanguage());
const loading = ref(false);
const templates = ref({});
const customPrompts = ref([]);

// 当前选中状态
const selectedCategory = ref(null);
const selectedPrompt = ref(null);
const promptContent = ref('');

// 编辑对话框状态
const editDialog = ref({
  open: false,
  promptType: '',
  promptKey: '',
  language: '',
  content: '',
  defaultContent: '',
  isNew: false,
});

// 监听语言变化
watch(
  () => locale?.value || locale,
  (newLang) => {
    if (!newLang) return;
    const newLanguage = newLang === 'en' ? 'en' : 'zh-CN';
    if (newLanguage !== currentLanguage.value) {
      currentLanguage.value = newLanguage;
      loadPromptData();
    }
  },
);

// 监听选中提示词变化
watch(selectedPrompt, () => {
  if (selectedPrompt.value) {
    loadPromptContent();
  }
});

// 初始化选择第一个分类和提示词
watch(
  [templates, currentLanguage],
  () => {
    if (Object.keys(templates.value).length > 0 && currentLanguage.value && !selectedCategory.value) {
      const firstCategory = Object.keys(templates.value)[0];
      selectedCategory.value = firstCategory;

      const promptEntries = Object.keys(templates.value[firstCategory]?.prompts || {});
      const firstPrompt = promptEntries.find((promptKey) => shouldShowPrompt(promptKey, currentLanguage.value));

      if (firstPrompt) {
        selectedPrompt.value = firstPrompt;
      }
    }
  },
  { immediate: true },
);

// ======= API 操作函数 =======

// 加载提示词数据
const loadPromptData = async () => {
  try {
    loading.value = true;
    const response = await fetchCustomPrompts(props.projectId, {
      language: currentLanguage.value,
    });
    const data = response?.data || response;
    const payload = data?.data || data || {};

    templates.value = payload.templates || {};
    customPrompts.value = payload.customPrompts || [];

    // 如果没有选中分类，选择第一个
    if (!selectedCategory.value && Object.keys(templates.value).length > 0) {
      selectedCategory.value = Object.keys(templates.value)[0];
    }
  } catch (error) {
    console.error('加载提示词数据出错:', error);
    ElMessage.error(t('settings.prompts.loadPromptsFailed', '加载提示词数据失败'));
  } finally {
    loading.value = false;
  }
};

// 加载提示词内容
const loadPromptContent = async (forceRefresh = false) => {
  if (!selectedPrompt.value) return;
  try {
    loading.value = true;
    const content = await getCurrentPromptContent(selectedPrompt.value, forceRefresh);
    promptContent.value = content;
  } catch (error) {
    console.error('加载提示词内容出错:', error);
    ElMessage.error(t('settings.prompts.loadContentFailed', '加载提示词内容失败'));
  } finally {
    loading.value = false;
  }
};

// 加载默认提示词内容
const loadDefaultContent = async (promptType, promptKey) => {
  let key = promptKey;
  if (currentLanguage.value === 'en' && !promptKey.endsWith('_EN')) {
    key += '_EN';
  }
  try {
    const response = await fetchDefaultPrompt(props.projectId, {
      promptType,
      promptKey: key,
    });
    const data = response?.data || response;
    const payload = data?.data || data || {};
    return payload.content || '';
  } catch (error) {
    console.error('加载默认提示词内容出错:', error);
    return '';
  }
};

// ======= 交互处理函数 =======

// 处理编辑提示词
const handleEditPrompt = async (promptType, promptKey, language) => {
  const existingPrompt = customPrompts.value.find(
    (p) => p.promptType === promptType && p.promptKey === promptKey && p.language === language,
  );

  const defaultContent = await loadDefaultContent(promptType, promptKey);

  editDialog.value = {
    open: true,
    promptType,
    promptKey,
    language,
    content: existingPrompt?.content || defaultContent,
    defaultContent,
    isNew: !existingPrompt,
  };
};

// 处理删除提示词
const handleDeletePrompt = async (promptType, promptKey, language) => {
  try {
    loading.value = true;
    await deleteCustomPrompt(props.projectId, {
      promptType,
      promptKey,
      language,
    });

    ElMessage.success(t('settings.prompts.restoreSuccess', '恢复成功'));
    await loadPromptData();
    await loadPromptContent(true);
  } catch (error) {
    console.error(t('settings.prompts.deleteError', '删除提示词出错'), error);
    ElMessage.error(t('settings.prompts.restoreFailed', '恢复失败'));
  } finally {
    loading.value = false;
  }
};

// 处理保存提示词
const handleSavePrompt = async () => {
  try {
    loading.value = true;
    const { promptType, promptKey, language, content } = editDialog.value;

    await saveCustomPrompt(props.projectId, {
      promptType,
      promptKey,
      language,
      content,
    });

    ElMessage.success(t('settings.prompts.saveSuccess', '保存成功'));
    editDialog.value.open = false;
    await loadPromptData();
    await loadPromptContent(true);
  } catch (error) {
    console.error(t('settings.prompts.saveError', '保存提示词出错'), error);
    ElMessage.error(t('settings.prompts.saveFailed', '保存失败'));
  } finally {
    loading.value = false;
  }
};

// 恢复默认内容
const handleRestoreDefault = () => {
  editDialog.value.content = editDialog.value.defaultContent;
};

// ======= 工具函数 =======

// 检查提示词是否已自定义
const isCustomized = (promptKey) => {
  if (!selectedCategory.value || !promptKey || !templates.value[selectedCategory.value]) return false;

  const language = getLanguageFromPromptKey(promptKey);
  const promptType = templates.value[selectedCategory.value]?.prompts?.[promptKey]?.type;

  if (!promptType) return false;

  return customPrompts.value.some(
    (p) => p.promptType === promptType && p.promptKey === promptKey && p.language === language,
  );
};

// 获取当前提示词内容
const getCurrentPromptContent = async (promptKey, forceRefresh = false) => {
  if (!selectedCategory.value || !promptKey || !templates.value[selectedCategory.value]) return '';

  const language = getLanguageFromPromptKey(promptKey);
  const promptType = templates.value[selectedCategory.value]?.prompts?.[promptKey]?.type;

  if (!promptType) {
    return '';
  }

  // 如果需要强制刷新，直接从服务器获取
  if (forceRefresh) {
    try {
      const response = await fetchCustomPrompts(props.projectId, {
        promptType,
        language,
      });
      const data = response?.data || response;
      const payload = data?.data || data || {};

      const existingPrompt = (payload.customPrompts || []).find(
        (p) => p.promptType === promptType && p.promptKey === promptKey && p.language === language,
      );

      if (existingPrompt) {
        return existingPrompt.content;
      }
    } catch (error) {
      console.error(t('settings.prompts.fetchContentError', '获取提示词内容出错'), error);
    }
  } else {
    // 使用缓存的状态
    const existingPrompt = customPrompts.value.find(
      (p) => p.promptType === promptType && p.promptKey === promptKey && p.language === language,
    );

    if (existingPrompt) {
      return existingPrompt.content;
    }
  }

  // 回退到默认内容
  return await loadDefaultContent(promptType, promptKey);
};

// ======= 数据准备 =======

// 当前分类的配置
const currentCategoryConfig = computed(() => templates.value[selectedCategory.value]);

// 当前提示词的配置
const currentPromptConfig = computed(() => currentCategoryConfig.value?.prompts?.[selectedPrompt.value]);

// 分类配置项
const categoryEntries = computed(() => Object.entries(templates.value));

// 处理分类变更
const handleCategoryChange = (newCategory) => {
  selectedCategory.value = newCategory;
  const promptEntries = Object.keys(templates.value[newCategory]?.prompts || {});
  const firstPrompt = promptEntries.find((promptKey) => shouldShowPrompt(promptKey, currentLanguage.value));
  selectedPrompt.value = firstPrompt;
};

// 处理提示词选择
const handlePromptSelect = (promptKey) => {
  selectedPrompt.value = promptKey;
};

// 处理编辑按钮点击
const handleEditButtonClick = () => {
  const promptType = templates.value[selectedCategory.value]?.prompts?.[selectedPrompt.value]?.type;
  const language = currentLanguage.value;

  if (promptType) {
    handleEditPrompt(promptType, selectedPrompt.value, language);
  }
};

// 处理删除按钮点击
const handleDeleteButtonClick = () => {
  const promptType = templates.value[selectedCategory.value]?.prompts?.[selectedPrompt.value]?.type;
  const language = currentLanguage.value;

  if (promptType) {
    handleDeletePrompt(promptType, selectedPrompt.value, language);
  }
};

// 处理对话框关闭
const handleDialogClose = () => {
  editDialog.value.open = false;
};

// 处理对话框内容变更
const handleDialogContentChange = (newContent) => {
  editDialog.value.content = newContent;
};

onMounted(() => {
  loadPromptData();
});
</script>

<style scoped>
.prompt-settings {
  padding: 20px 0;
}
</style>

