<template>
  <div class="top-navigation">
    <el-menu
      :default-active="activeMenu"
      mode="horizontal"
      class="nav-menu"
      :ellipsis="false"
      @select="handleMenuSelect"
    >
      <!-- 首页 -->
      <el-menu-item :index="'/'" @click="navigate('/')">
        <el-icon><House /></el-icon>
        <span>{{ $t('common.home','首页') }}</span>
      </el-menu-item>

      <!-- 数据源菜单 -->
      <el-sub-menu index="source" v-if="projectIdLocal">
        <template #title>
          <span class="submenu-title">
            <el-icon><Document /></el-icon>
            <span>{{ $t('common.dataSource') }}</span>
            <el-icon class="submenu-arrow"><ArrowDown /></el-icon>
          </span>
        </template>
        <el-menu-item
          :index="`/projects/${projectIdLocal}/text-split`"
          @click="navigate(`/projects/${projectIdLocal}/text-split`)"
        >
          <el-icon><Document /></el-icon>
          <span>{{ $t('textSplit.title') }}</span>
        </el-menu-item>
        <el-menu-item
          :index="`/projects/${projectIdLocal}/images`"
          @click="navigate(`/projects/${projectIdLocal}/images`)"
        >
          <el-icon><Picture /></el-icon>
          <span>{{ $t('images.title') }}</span>
        </el-menu-item>
      </el-sub-menu>

      <!-- 数据蒸馏 -->
      <el-menu-item
        v-if="projectIdLocal"
        :index="`/projects/${projectIdLocal}/distill`"
        @click="navigate(`/projects/${projectIdLocal}/distill`)"
      >
        <el-icon><Connection /></el-icon>
        <span>{{ $t('distill.title') }}</span>
      </el-menu-item>

      <!-- 问题管理 -->
      <el-menu-item
        v-if="projectIdLocal"
        :index="`/projects/${projectIdLocal}/questions`"
        @click="navigate(`/projects/${projectIdLocal}/questions`)"
      >
        <el-icon><ChatLineRound /></el-icon>
        <span>{{ $t('questions.title') }}</span>
      </el-menu-item>

      <!-- 数据集管理菜单 -->
      <el-sub-menu index="datasets" v-if="projectIdLocal">
        <template #title>
          <span class="submenu-title">
            <el-icon><DataBoard /></el-icon>
            <span>{{ $t('datasets.management') }}</span>
            <el-icon class="submenu-arrow"><ArrowDown /></el-icon>
          </span>
        </template>
        <el-menu-item
          :index="`/projects/${projectIdLocal}/datasets`"
          @click="navigate(`/projects/${projectIdLocal}/datasets`)"
        >
          <el-icon><DataBoard /></el-icon>
          <span>{{ $t('datasets.singleTurn') }}</span>
        </el-menu-item>
        <el-menu-item
          :index="`/projects/${projectIdLocal}/multi-turn`"
          @click="navigate(`/projects/${projectIdLocal}/multi-turn`)"
        >
          <el-icon><ChatLineRound /></el-icon>
          <span>{{ $t('datasets.multiTurn') }}</span>
        </el-menu-item>
        <el-menu-item
          :index="`/projects/${projectIdLocal}/image-datasets`"
          @click="navigate(`/projects/${projectIdLocal}/image-datasets`)"
        >
          <el-icon><Picture /></el-icon>
          <span>{{ $t('datasets.imageQA') }}</span>
        </el-menu-item>
        <el-menu-item
          :index="`/projects/${projectIdLocal}/datasets-overview`"
          @click="navigate(`/projects/${projectIdLocal}/datasets-overview`)"
        >
          <el-icon><DataBoard /></el-icon>
          <span>{{ $t('datasets.overview','数据集总览') }}</span>
        </el-menu-item>
      </el-sub-menu>

      <!-- 设置 -->
      <el-menu-item
        v-if="projectIdLocal"
        :index="`/projects/${projectIdLocal}/settings`"
        @click="navigate(`/projects/${projectIdLocal}/settings`)"
      >
        <el-icon><Setting /></el-icon>
        <span>{{ $t('settings.title') }}</span>
      </el-menu-item>

      <!-- 模型管理 -->
      <el-menu-item index="/model-management" @click="navigate('/model-management')">
        <el-icon><Promotion /></el-icon>
        <span>{{ $t('modelManagement.title') }}</span>
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
  House,
} from '@element-plus/icons-vue';

const props = defineProps({
  projectId: {
    type: String,
    required: false,
  },
});

const router = useRouter();
const route = useRoute();

 

const projectIdLocal = computed(() => {
  return props.projectId || route.query.projectId || route.params.projectId || null;
});

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
  // Preserve project context when navigating to global pages so project menu stays visible
  const currentProjectId = projectIdLocal.value;
  if (currentProjectId && (path === '/model-management' || path === '/dataset-square')) {
    router.push({ path, query: { projectId: currentProjectId } });
  } else {
    router.push(path);
  }
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

