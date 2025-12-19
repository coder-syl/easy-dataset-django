import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/projects/:projectId',
    name: 'project-overview',
    component: () => import('../views/ProjectOverview.vue'),
  },
  {
    path: '/projects/:projectId/text-split',
    name: 'text-split',
    component: () => import('../views/projects/TextSplitView.vue'),
  },
  {
    path: '/projects/:projectId/images',
    name: 'images',
    component: () => import('../views/projects/ImagesView.vue'),
  },
  {
    path: '/projects/:projectId/distill',
    name: 'distill',
    component: () => import('../views/projects/DistillView.vue'),
  },
  {
    path: '/projects/:projectId/questions',
    name: 'questions',
    component: () => import('../views/projects/QuestionsView.vue'),
  },
  {
    path: '/projects/:projectId/datasets',
    name: 'datasets',
    component: () => import('../views/projects/DatasetsView.vue'),
  },
  {
    path: '/projects/:projectId/datasets/:datasetId',
    name: 'dataset-details',
    component: () => import('../views/projects/DatasetDetailView.vue'),
  },
  {
    path: '/projects/:projectId/multi-turn',
    name: 'multi-turn',
    component: () => import('../views/projects/MultiTurnView.vue'),
  },
  {
    path: '/projects/:projectId/multi-turn/:conversationId',
    name: 'conversation-details',
    component: () => import('../views/projects/ConversationDetailView.vue'),
  },
  {
    path: '/projects/:projectId/image-datasets',
    name: 'image-datasets',
    component: () => import('../views/projects/ImageDatasetsView.vue'),
  },
  {
    path: '/projects/:projectId/image-datasets/:datasetId',
    name: 'image-dataset-details',
    component: () => import('../views/projects/ImageDatasetDetailView.vue'),
  },
  {
    path: '/projects/:projectId/settings',
    name: 'settings',
    component: () => import('../views/projects/SettingsView.vue'),
  },
  {
    path: '/projects/:projectId/tasks',
    name: 'tasks',
    component: () => import('../views/projects/TasksView.vue'),
  },
  {
    path: '/projects/:projectId/playground',
    name: 'playground',
    component: () => import('../views/projects/PlaygroundView.vue'),
  },
  {
    path: '/model-management',
    name: 'model-management',
    component: () => import('../views/ModelManagementView.vue'),
  },
  {
    path: '/dataset-square',
    name: 'dataset-square',
    component: () => import('../views/DatasetSquareView.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFoundView.vue'),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

// 路由守卫：在进入项目相关页面时加载模型配置
router.beforeEach(async (to, from, next) => {
  // 如果路由包含 projectId，加载模型配置
  if (to.params.projectId) {
    const { useModelStore } = await import('../stores/model');
    const modelStore = useModelStore();
    // 如果项目ID变化，或者 store 中还没有模型配置列表，则重新加载
    // 这样可以确保页面刷新时也能加载模型配置
    if (from.params.projectId !== to.params.projectId || modelStore.modelConfigList.length === 0) {
      await modelStore.loadModelConfigs(to.params.projectId);
    }
  }
  next();
});

export default router;

