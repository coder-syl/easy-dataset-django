<template>
  <div class="top-navigation">
    <el-menu
      :default-active="activeMenu"
      mode="horizontal"
      class="nav-menu"
      :ellipsis="false"
      @select="handleMenuSelect"
    >
      <!-- 数据源菜单 -->
      <el-sub-menu index="source">
        <template #title>
          <span class="submenu-title">
            <el-icon><Document /></el-icon>
            <span>{{ $t('common.dataSource') }}</span>
            <el-icon class="submenu-arrow"><ArrowDown /></el-icon>
          </span>
        </template>
        <el-menu-item
          :index="`/projects/${projectId}/text-split`"
          @click="navigate(`/projects/${projectId}/text-split`)"
        >
          <el-icon><Document /></el-icon>
          <span>{{ $t('textSplit.title') }}</span>
        </el-menu-item>
        <el-menu-item
          :index="`/projects/${projectId}/images`"
          @click="navigate(`/projects/${projectId}/images`)"
        >
          <el-icon><Picture /></el-icon>
          <span>{{ $t('images.title') }}</span>
        </el-menu-item>
      </el-sub-menu>

      <!-- 数据蒸馏 -->
      <el-menu-item
        :index="`/projects/${projectId}/distill`"
        @click="navigate(`/projects/${projectId}/distill`)"
      >
        <el-icon><Connection /></el-icon>
        <span>{{ $t('distill.title') }}</span>
      </el-menu-item>

      <!-- 问题管理 -->
      <el-menu-item
        :index="`/projects/${projectId}/questions`"
        @click="navigate(`/projects/${projectId}/questions`)"
      >
        <el-icon><ChatLineRound /></el-icon>
        <span>{{ $t('questions.title') }}</span>
      </el-menu-item>

      <!-- 数据集管理菜单 -->
      <el-sub-menu index="datasets">
        <template #title>
          <span class="submenu-title">
            <el-icon><DataBoard /></el-icon>
            <span>{{ $t('datasets.management') }}</span>
            <el-icon class="submenu-arrow"><ArrowDown /></el-icon>
          </span>
        </template>
        <el-menu-item
          :index="`/projects/${projectId}/datasets`"
          @click="navigate(`/projects/${projectId}/datasets`)"
        >
          <el-icon><DataBoard /></el-icon>
          <span>{{ $t('datasets.singleTurn') }}</span>
        </el-menu-item>
        <el-menu-item
          :index="`/projects/${projectId}/multi-turn`"
          @click="navigate(`/projects/${projectId}/multi-turn`)"
        >
          <el-icon><ChatLineRound /></el-icon>
          <span>{{ $t('datasets.multiTurn') }}</span>
        </el-menu-item>
        <el-menu-item
          :index="`/projects/${projectId}/image-datasets`"
          @click="navigate(`/projects/${projectId}/image-datasets`)"
        >
          <el-icon><Picture /></el-icon>
          <span>{{ $t('datasets.imageQA') }}</span>
        </el-menu-item>
      </el-sub-menu>

      <!-- 设置 -->
      <el-menu-item
        :index="`/projects/${projectId}/settings`"
        @click="navigate(`/projects/${projectId}/settings`)"
      >
        <el-icon><Setting /></el-icon>
        <span>{{ $t('settings.title') }}</span>
      </el-menu-item>

      <!-- 模型测试 -->
      <el-menu-item
        :index="`/projects/${projectId}/playground`"
        @click="navigate(`/projects/${projectId}/playground`)"
      >
        <el-icon><Promotion /></el-icon>
        <span>{{ $t('playground.title') }}</span>
      </el-menu-item>

      <!-- 数据集广场 -->
      <el-menu-item index="/dataset-square" @click="navigate('/dataset-square')">
        <el-icon><Box /></el-icon>
        <span>{{ $t('datasetSquare.title') }}</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import {
  Document,
  Picture,
  Connection,
  ChatLineRound,
  DataBoard,
  Setting,
  Promotion,
  Box,
  ArrowDown,
} from '@element-plus/icons-vue';

const props = defineProps({
  projectId: {
    type: String,
    required: true,
  },
});

const router = useRouter();
const route = useRoute();

const activeMenu = computed(() => {
  const path = route.path;
  if (path.includes('/text-split') || path.includes('/images')) {
    return 'source';
  }
  if (path.includes('/datasets') || path.includes('/multi-turn') || path.includes('/image-datasets')) {
    return 'datasets';
  }
  return path;
});

const navigate = (path) => {
  router.push(path);
};

const handleMenuSelect = (index) => {
  // 子菜单项已经在 @click 中处理，这里主要处理直接菜单项
  if (index.startsWith('/')) {
    navigate(index);
  }
};
</script>

<style scoped>
.top-navigation {
  flex: 1;
  display: flex;
  justify-content: center;
}

.nav-menu {
  border-bottom: none;
  background: transparent;
}

:deep(.el-menu--horizontal) {
  border-bottom: none;
  background: transparent;
}

:deep(.el-menu--horizontal > .el-menu-item),
:deep(.el-menu--horizontal > .el-sub-menu > .el-sub-menu__title) {
  height: 56px;
  line-height: 56px;
  padding: 0 20px;
  color: var(--nav-text, #0f172a);
}

:deep(.el-menu--horizontal > .el-menu-item.is-active),
:deep(.el-menu--horizontal > .el-sub-menu.is-active > .el-sub-menu__title) {
  color: var(--nav-text-active, #1d4ed8);
}

:deep(.el-menu--horizontal > .el-menu-item:hover),
:deep(.el-menu--horizontal > .el-sub-menu > .el-sub-menu__title:hover) {
  color: var(--nav-text-hover, #2563eb);
}

.submenu-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.submenu-arrow {
  font-size: 12px;
  transition: transform 0.3s;
}

:deep(.el-sub-menu.is-opened) .submenu-arrow {
  transform: rotate(180deg);
}

/* 隐藏内置箭头，使用自定义箭头图标 */
:deep(.el-sub-menu__icon-arrow) {
  display: none;
}
</style>

