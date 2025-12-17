<template>
  <div class="prompt-list">
    <el-empty v-if="!currentCategoryConfig?.prompts" :description="$t('settings.prompts.noPromptsAvailable', '暂无提示词')" />

    <el-menu
      v-else
      :default-active="selectedPrompt"
      class="prompt-menu"
      @select="handleSelect"
    >
      <el-menu-item
        v-for="[promptKey, promptConfig] in promptEntries"
        :key="promptKey"
        :index="promptKey"
      >
        <div class="prompt-item">
          <span class="prompt-name">{{ promptConfig.name }}</span>
          <el-tag v-if="isCustomized(promptKey)" type="primary" size="small" class="customized-tag">
            {{ $t('settings.prompts.customized', '已自定义') }}
          </el-tag>
        </div>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { shouldShowPrompt } from '../../utils/promptUtils';

const props = defineProps({
  currentCategory: {
    type: String,
    required: true,
  },
  currentCategoryConfig: {
    type: Object,
    default: null,
  },
  selectedPrompt: {
    type: String,
    default: null,
  },
  currentLanguage: {
    type: String,
    required: true,
  },
  isCustomized: {
    type: Function,
    required: true,
  },
});

const emit = defineEmits(['prompt-select']);

const promptEntries = computed(() => {
  if (!props.currentCategoryConfig?.prompts) {
    return [];
  }
  return Object.entries(props.currentCategoryConfig.prompts).filter(([promptKey]) =>
    shouldShowPrompt(promptKey, props.currentLanguage),
  );
});

const handleSelect = (promptKey) => {
  emit('prompt-select', promptKey);
};
</script>

<style scoped>
.prompt-list {
  min-height: 200px;
}

.prompt-menu {
  border: none;
}

.prompt-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.prompt-name {
  flex: 1;
  font-weight: 500;
}

.customized-tag {
  margin-left: 8px;
}
</style>

