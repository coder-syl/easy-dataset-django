# Next.js → Vue 3 迁移方案（Vite + Vue Router 4 + Element Plus）

## 总体策略
- 双栈并行：保持后端 API/DTO 不变，新建 Vue 前端，逐模块迁移、对照验证，再切流。
- 路由等价：Next App Router 动态段 `[projectId]/[conversationId]` → Vue Router `:projectId/:conversationId`。
- 数据语义对齐：React hooks + React Query → 组合式函数 + vue-query（缓存 key、重试、staleTime 对齐）。
- 组件库替换：MUI → Element Plus（表单、对话框、表格、消息、Skeleton/Empty）。

## 基础设施模块
1) 路由与布局  
   - `src/router/index.js`：映射 Next 路由，含 404、重定向、鉴权守卫。  
   - 全局布局 `MainLayout`：顶栏/侧栏/内容区，Breadcrumb，暗黑模式切换。  
   - 输出：路由表、Layout 组件、守卫逻辑。

2) 状态与数据层  
   - Pinia：`user/session`（token、profile）、`projects`、`conversations`、`ui`。  
   - vue-query：配置 QueryClient；封装 `useApiQuery/useApiMutation`，统一错误提示与重试。  
   - 输出：`src/stores/*.js`，查询/变更封装。

3) API 封装  
   - axios 实例：baseURL、超时、鉴权拦截、全局错误处理（ElMessage）。  
   - 模块化 API：`api/project.js`、`api/conversation.js`、`api/task.js`、`api/upload.js`。  
   - 输出：axios 实例、各 API 方法、错误码映射。

4) 国际化  
   - 迁移 i18next 资源 → vue-i18n `messages`；脚本比对缺失 key。  
   - 输出：`src/i18n/index.js`，语言包，缺失键校验脚本。

5) 通用组件与样式  
   - 基础组件：Button/Link、Dialog、Drawer、Form+校验、Message/Notification、Skeleton/Empty、Tag/Badge、Loading。  
   - 主题：Element Plus 变量，暗黑模式通过 `data-theme`/`class` 切换。  
   - 输出：`src/components/base/*`，主题变量文件，全局样式。

## 业务模块迁移（按优先级）
1) 会话详情与多轮对话（重点）  
   - 路由：`/projects/:projectId/multi-turn/:conversationId`。  
   - 组件：Header（标题/状态/操作）、Content（消息列表/角色高亮/引用）、Metadata（键值对、编辑）、RatingSection（评分）。  
   - 数据：`useConversationDetails` 组合式函数；vue-query 获取详情/消息；评分与元数据 Mutation（乐观更新）。  
   - 输出：`views/ConversationView.vue` + 子组件，`composables/useConversationDetails.js`。

2) 项目列表与详情  
   - 表格/筛选/分页/搜索（Element Table + Pagination）。  
   - 输出：`views/Projects/List.vue`、`views/Projects/Detail.vue`，相关 API。

3) 任务流/进度  
   - 状态标签、进度条，轮询或 `refetchInterval`。  
   - 输出：`views/Tasks/TaskList.vue`，`composables/useTasks.js`。

4) 文件上传与分段处理  
   - 上传（拖拽/按钮）、进度、分块配置；Element Upload 或自定义。  
   - 输出：`views/Upload/FileUpload.vue`，`composables/useUploader.js`。

5) 导出与配置  
   - 表单配置、校验、预览；提交导出任务。  
   - 输出：`views/Export/Config.vue`，表单规则、提交 API。

6) 辅助/工具  
   - 工具函数迁移到 `src/utils/*`；图标 `@element-plus/icons-vue` / `@iconify/vue`。  
   - 输出：工具函数库、图标封装。

## 迁移步骤（可执行）
- 第 0 步：Vite+Vue3 基座、Element Plus、Pinia、vue-query、axios、vue-i18n、路由骨架。  
- 第 1 步：会话详情（只读）→ 评分/元数据编辑 → Loading/Empty/Error。  
- 第 2 步：项目列表/详情、任务流轮询；公共组件 Dialog/Message/Empty/Skeleton。  
- 第 3 步：文件上传模块、导出配置表单；表单校验统一。  
- 第 4 步：国际化资源转换、缺失键校验；主题/暗黑模式细化。  
- 第 5 步：测试（Vitest + Vue Test Utils，保留 E2E）、性能与体积优化，CI（lint/test/build）。

## 测试与验收
- 单测：核心组件/组合式函数（数据获取、表单校验、状态切换）。  
- E2E：登录→项目列表→会话详情→评分/编辑→导出；上传流程。  
- 对照：双栈页面并排验证 UI/行为；接口响应一致；i18n key 覆盖率。

## 注意事项
- Node 需 ≥20.19（或 22.12+）；升级后重装依赖。  
- Vite 环境变量使用 `VITE_` 前缀；确认 base/publicPath。  
- 路由守卫代替 Next middleware；鉴权/角色逻辑需迁移。  
- Element Plus 组件行为差异需验证（表格排序、表单校验、Dialog 焦点管理）。  

