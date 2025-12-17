<template>
  <el-card v-if="conversation" class="conversation-metadata" shadow="never">
    <template #header>
      <span class="metadata-title">{{ $t('datasets.metadata') }}</span>
    </template>
    <div class="metadata-content">
      <el-tag size="small" effect="plain">
        {{ $t('datasets.modelUsed') }}: {{ conversation.model }}
      </el-tag>

      <el-tag v-if="conversation.scenario" size="small" type="primary" effect="plain">
        {{ $t('datasets.conversationScenario') }}: {{ conversation.scenario }}
      </el-tag>

      <el-tag size="small" effect="plain">
        {{ $t('datasets.conversationRounds') }}: {{ conversation.turnCount }}/{{ conversation.maxTurns }}
      </el-tag>

      <el-tag v-if="conversation.roleA" size="small" type="info" effect="plain">
        {{ $t('settings.multiTurnRoleA') }}: {{ conversation.roleA }}
      </el-tag>

      <el-tag v-if="conversation.roleB" size="small" type="success" effect="plain">
        {{ $t('settings.multiTurnRoleB') }}: {{ conversation.roleB }}
      </el-tag>

      <el-tag v-if="conversation.createAt" size="small" effect="plain">
        {{ $t('datasets.createdAt') }}: {{ formatDate(conversation.createAt) }}
      </el-tag>

      <el-tag v-if="conversation.confirmed" size="small" type="success" effect="plain">
        {{ $t('datasets.confirmed') }}
      </el-tag>
    </div>
  </el-card>
</template>

<script setup>
const props = defineProps({
  conversation: {
    type: Object,
    default: null
  }
});

const formatDate = (dateString) => {
  if (!dateString) return '';
  try {
    return new Date(dateString).toLocaleDateString();
  } catch (e) {
    return dateString;
  }
};
</script>

<style scoped>
.conversation-metadata {
  margin-bottom: 24px;
}

.metadata-title {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.metadata-content {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>

