<template>
  <div class="text-split-view projects-container">
    <!-- 顶部操作栏 + 上传/已上传列表（单卡片，横向布局） -->
    <el-card class="top-card" shadow="never">
      <div class="toolbar">
        <div class="header-left">
          <h3>{{ $t('textSplit.title', '文本文献') }}</h3>
          <el-button type="primary" :loading="splitting" @click="handleSplit">
            {{ $t('textSplit.splitNow', '开始分割') }}
          </el-button>
          <el-button type="primary" text circle @click="toggleUploader">
            <el-icon v-if="uploaderExpanded"><ArrowUp /></el-icon>
            <el-icon v-else><ArrowDown /></el-icon>
          </el-button>
        </div>
      </div>

      <el-collapse-transition>
        <div v-show="uploaderExpanded" class="uploader-form top-form">
          <div class="upload-left">
            <div class="upload-inner">
              <div class="upload-title">
                {{ $t('textSplit.uploadNew', '上传新文献') }}
              </div>
              <el-upload
                :auto-upload="false"
                :multiple="true"
                :show-file-list="false"
                :on-change="handleFileSelect"
                ref="uploadRef"
              >
                <template #trigger>
                  <el-button type="primary" :disabled="!modelStore.selectedModelInfo">
                    <el-icon><Upload /></el-icon>
                    {{ $t('textSplit.selectFile', '选择文件') }} ({{ $t('textSplit.supportsMultiple', '支持多个') }})
                  </el-button>
                </template>
              </el-upload>
              <div class="uploader-tips">
                <p>{{ $t('textSplit.uploadHint', '上传新文件后会重新构建领域树') }}</p>
              </div>
              <div v-if="pendingFiles.length > 0" class="pending-files">
                <div class="pending-files-title">
                  {{ $t('textSplit.selectedFiles', { count: pendingFiles.length }, `已选择 ${pendingFiles.length} 个文件`) }}
                </div>
                <div class="pending-files-list">
                  <div v-for="(file, index) in pendingFiles" :key="index" class="pending-file-item">
                    <span>{{ file.name }}</span>
                    <el-button size="default" text type="danger" @click="removePendingFile(index)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
                <el-button
                  type="primary"
                  :loading="uploading"
                  :disabled="!modelStore.selectedModelInfo"
                  @click="handleUploadPendingFiles"
                  class="upload-button"
                >
                  {{ $t('textSplit.uploadAndProcess', '上传并处理') }}
                </el-button>
              </div>
            </div>
          </div>
          <div class="upload-right">
            <div class="uploaded-header">
              <span class="uploaded-title">
                {{ $t('textSplit.uploadedDocuments', { count: filesTotal }, `已上传 ${filesTotal} 个文档`) }}
              </span>
              <div class="uploaded-actions">
                <el-button
                  v-if="filesTotal > 0"
                  size="default"
                  :type="selectedFileIds.length === filesTotal ? 'primary' : 'default'"
                  @click="handleToggleSelectAllFiles"
                >
                  {{ selectedFileIds.length === filesTotal ? $t('gaPairs.deselectAllFiles', '取消全选') : $t('gaPairs.selectAllFiles', '全选') }}
                </el-button>
                <el-button
                  v-if="filesTotal > 0"
                  size="default"
                  type="primary"
                  :disabled="selectedFileIds.length === 0"
                  @click="batchGenerateGaDialogOpen = true"
                >
                  <el-icon><MagicStick /></el-icon>
                  {{ $t('gaPairs.batchGenerate', '批量生成GA对') }}
                </el-button>
                <el-button size="default" @click="refreshFiles">
                  <el-icon><Refresh /></el-icon>
                  {{ $t('common.refresh', '刷新') }}
                </el-button>
                <el-button
                  v-if="filesTotal > 0"
                  size="default"
                  type="primary"
                  @click="openFileListDialog"
                >
                  <el-icon><FullScreen /></el-icon>
                  {{ $t('textSplit.expandFileList', '全屏查看') }}
                </el-button>
              </div>
            </div>
            <div v-loading="filesLoading" class="uploaded-files-list">
              <el-empty v-if="filesTotal === 0" :description="$t('textSplit.noFilesUploaded', '暂未上传文件')" />
              <div v-else class="file-list">
                <div v-for="file in filesDisplay" :key="file.id || file.fileId" class="file-item">
                  <el-icon class="file-icon"><Document /></el-icon>
                  <div class="file-info" @click="handleViewFile(file)">
                    <div class="file-name">{{ file.file_name || file.fileName || file.name }}</div>
                    <div class="file-meta">
                      {{ formatFileSize(file.size || file.file_size || 0) }} · {{ formatDate(file.create_at || file.createAt || file.created_at) }}
                    </div>
                  </div>
                  <div class="file-actions">
                    <el-checkbox
                      :model-value="selectedFileIds.includes(String(file.id || file.fileId))"
                      @change="(val) => toggleFile(file.id || file.fileId, val)"
                    />
                    <div class="ga-pairs-wrapper">
                      <GaPairsIndicator
                        :project-id="projectId"
                        :file-id="String(file.id || file.fileId)"
                        :file-name="file.file_name || file.fileName || file.name"
                      />
                    </div>
                    <el-tooltip :content="$t('textSplit.download', '下载')" placement="top">
                      <el-button size="default" text circle @click.stop="handleDownloadFile(file)">
                        <el-icon><Download /></el-icon>
                      </el-button>
                    </el-tooltip>
                    <el-tooltip :content="$t('common.delete', '删除')" placement="top">
                      <el-button size="default" text circle type="danger" @click.stop="handleDeleteFile(file)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </el-tooltip>
                  </div>
                </div>
              </div>
              <div class="uploaded-pagination" v-if="filesTotal > 0">
                <el-pagination
                  background
                  layout="sizes, prev, pager, next"
                  :total="filesTotal"
                  :page-size="filesPageSize"
                  :current-page="filesPage"
                  :page-sizes="[5, 10, 20, 50]"
                  @current-change="handleFilesPageChange"
                  @size-change="handleFilesSizeChange"
                />
              </div>
            </div>
          </div>
        </div>
      </el-collapse-transition>
    </el-card>

    <!-- Tab 切换：智能分割 / 领域分析 -->
    <el-card class="main-card ed-card" shadow="never">
      <el-tabs v-model="activeTab" class="main-tabs" stretch>
        <el-tab-pane :label="$t('textSplit.tabs.smartSplit', '智能分割')" name="split">
          <el-row   class="main-row">
            <el-col :span="24">
              <el-card shadow="never" class="chunk-panel">
                <div class="chunk-toolbar">
                  <div class="chunk-toolbar-left">
                    <el-checkbox
                      :indeterminate="selectedChunkIds.length > 0 && selectedChunkIds.length < filteredChunks.length"
                      :model-value="selectedChunkIds.length === filteredChunks.length && filteredChunks.length > 0"
                      @change="toggleSelectAll"
                    />
                    <span class="selection-text">
                      {{ $t('textSplit.selectedCount', { count: selectedChunkIds.length }, `已选择 ${selectedChunkIds.length} 个文本块`) }},
                      {{ $t('textSplit.totalCount', { count: filteredChunks.length }, `共 ${filteredChunks.length} 个文本块`) }}
                    </span>
                  </div>
                  <div class="chunk-toolbar-actions">
                    <el-badge :value="activeFilterCount" :hidden="activeFilterCount === 0" type="danger">
                      <el-button size="default" @click="filterDialogOpen = true">
                        <el-icon><Filter /></el-icon>
                        {{ $t('datasets.moreFilters', '更多筛选') }}
                      </el-button>
                    </el-badge>
                    <el-button
                      size="default"
                      type="primary"
                      :disabled="selectedChunkIds.length === 0"
                      @click="handleGenerateQuestions()"
                    >
                      <el-icon><CollectionTag /></el-icon>
                      {{ $t('textSplit.batchGenerateQuestions', '批量生成问题') }}
                    </el-button>
                    <el-button
                      size="default"
                      :disabled="!modelStore.selectedModelInfo"
                      @click="handleAutoGenerateQuestions"
                    >
                      <el-icon><MagicStick /></el-icon>
                      {{ $t('textSplit.autoGenerateQuestions', '自动提取问题') }}
                    </el-button>
                    <el-button
                      size="default"
                      type="success"
                      :disabled="!modelStore.selectedModelInfo"
                      @click="handleAutoDataCleaning"
                    >
                      <el-icon><Brush /></el-icon>
                      {{ $t('textSplit.autoDataCleaning', '自动数据清洗') }}
                    </el-button>
                    <el-dropdown trigger="click" @command="handleMoreCommand">
                      <el-button size="default" circle>
                        <el-icon><MoreFilled /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="batchEdit" :disabled="selectedChunkIds.length === 0">
                            <el-icon><Edit /></el-icon>
                            {{ batchEditLabel }}
                          </el-dropdown-item>
                          <el-dropdown-item command="batchDelete" :disabled="selectedChunkIds.length === 0" divided>
                            <el-icon><Delete /></el-icon>
                            {{ $t('textSplit.batchDelete', '批量删除') }}
                          </el-dropdown-item>
                          <el-dropdown-item command="export" :disabled="chunks.length === 0">
                            <el-icon><Download /></el-icon>
                            {{ $t('textSplit.exportChunks', '导出文本块') }}
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </div>

                <div v-loading="loading" class="chunk-list">
                  <el-empty v-if="!filteredChunks || filteredChunks.length === 0" :description="$t('textSplit.noChunks', '暂无文本块')" />
                  <div
                    v-for="chunk in filteredChunks"
                    :key="chunk.id"
                    class="chunk-card"
                    :class="{ 'chunk-card-selected': selectedChunkIds.includes(chunk.id) }"
                  >
                    <div class="chunk-card-content">
                      <el-checkbox
                        :model-value="selectedChunkIds.includes(chunk.id)"
                        @change="(val) => toggleChunk(chunk.id, val)"
                        class="chunk-checkbox"
                      />
                      <div class="chunk-main">
                        <div class="chunk-header-row">
                          <div class="chunk-title">{{ chunk.name || chunk.fileName || ('Chunk ' + chunk.id) }}</div>
                          <div class="chunk-tags">
                            <el-tag size="default" type="primary" effect="plain" class="chunk-tag">
                              {{ chunk.fileName || chunk.file_name || $t('textSplit.unknownFile', '未知文件') }}
                            </el-tag>
                            <el-tag size="default" type="info" effect="plain" class="chunk-tag">
                              {{ chunk.size || 0 }}{{ $t('textSplit.words', '字') }}
                            </el-tag>
                            <!-- question count and generating badge temporarily disabled -->
                          </div>
                        </div>
                        <div class="chunk-preview">
                          {{ getChunkPreview(chunk.content || chunk.preview || '') }}
                        </div>
                      </div>
                    </div>
                    <div class="chunk-card-actions">
                      <el-tooltip :content="$t('textSplit.view', '查看')" placement="top">
                        <el-button size="default" circle @click="handleViewChunk(chunk)" class="action-btn action-btn-view">
                          <el-icon><View /></el-icon>
                        </el-button>
                      </el-tooltip>
                      <el-tooltip :content="$t('textSplit.generateQuestions', '生成问题')" placement="top">
                        <el-button
                          size="default"
                          circle
                          @click="handleGenerateQuestions([chunk.id])"
                          :disabled="!modelStore.selectedModelInfo"
                          class="action-btn action-btn-question"
                        >
                          <el-icon><CollectionTag /></el-icon>
                        </el-button>
                      </el-tooltip>
                      <el-tooltip :content="$t('textSplit.dataCleaning', '数据清洗')" placement="top">
                        <el-button
                          size="default"
                          circle
                          @click="handleDataCleaning([chunk.id])"
                          :disabled="!modelStore.selectedModelInfo"
                          class="action-btn action-btn-clean"
                        >
                          <el-icon><Brush /></el-icon>
                        </el-button>
                      </el-tooltip>
                      <el-tooltip :content="$t('common.edit', '编辑')" placement="top">
                        <el-button size="default" circle @click="handleEditChunk(chunk)" class="action-btn action-btn-edit">
                          <el-icon><Edit /></el-icon>
                        </el-button>
                      </el-tooltip>
                      <el-tooltip :content="$t('common.delete', '删除')" placement="top">
                        <el-button
                          size="default"
                          circle
                          type="danger"
                          @click="handleDeleteChunk(chunk)"
                          class="action-btn action-btn-delete"
                        >
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </el-tooltip>
                    </div>
                  </div>
                </div>
              </el-card>
            </el-col>

            
          </el-row>
        </el-tab-pane>

        <el-tab-pane :label="$t('textSplit.tabs.domainAnalysis', '领域分析')" name="domain">
          <el-card shadow="never" class="domain-analysis-card">
            <el-tabs v-model="domainActiveTab" class="domain-tabs">
              <!-- 领域树 Tab -->
              <el-tab-pane :label="$t('domain.tabs.tree', '领域树')" name="tree">
                <div class="domain-tree-section">
                  <div class="domain-tree-header">
                    <h3>{{ $t('domain.tabs.tree', '领域树') }}</h3>
                    <el-button type="primary" @click="handleAddRootTag">
                      <el-icon><Plus /></el-icon>
                      {{ $t('domain.addRootTag', '添加一级标签') }}
                    </el-button>
                  </div>
                  <el-divider />
                  <div class="domain-tree-content" v-loading="tagsLoading">
                    <el-empty v-if="!tags || tags.length === 0" :description="$t('domain.noTags', '暂无标签')">
                      <el-button type="primary" @click="handleAddRootTag">
                        <el-icon><Plus /></el-icon>
                        {{ $t('domain.addFirstTag', '添加第一个标签') }}
                      </el-button>
                    </el-empty>
                    <div v-else class="domain-tree-list">
                      <template v-for="(node, index) in tags" :key="index">
                        <DomainTreeNode
                          :node="node"
                          :level="0"
                          @edit="handleEditTag"
                          @delete="handleDeleteTag"
                          @add-child="handleAddChildTag"
                        />
                      </template>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <!-- 文档结构 Tab -->
              <el-tab-pane :label="$t('domain.tabs.structure', '文档结构')" name="structure">
                <div class="domain-structure-section">
                  <h3>{{ $t('domain.docStructure', '文档结构') }}</h3>
                  <el-divider />
                  <div class="toc-content" v-if="tocData">
                    <div class="markdown-body" v-html="renderedToc"></div>
                  </div>
                  <el-empty v-else :description="$t('domain.noToc', '暂无目录数据')" />
                </div>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 查看文本块 -->
    <el-dialog v-model="viewDialogOpen" :title="$t('textSplit.viewChunk', '查看文本块')" width="60%">
      <div class="chunk-content" v-if="currentChunk">
        <p><strong>ID:</strong> {{ currentChunk.id }}</p>
        <p><strong>{{ $t('textSplit.chunkName', '名称') }}:</strong> {{ currentChunk.name }}</p>
        <p><strong>{{ $t('textSplit.fileName', '文件名') }}:</strong> {{ currentChunk.fileName }}</p>
        <el-divider />
        <div class="chunk-markdown markdown-body" v-html="renderedChunk"></div>
      </div>
    </el-dialog>

    <!-- 编辑文本块 -->
    <el-dialog
      v-model="editChunkDialogOpen"
      :title="$t('textSplit.editChunk', { chunkId: editingChunk?.name || '' }, `编辑文本块: ${editingChunk?.name || ''}`)"
      width="70%"
    >
      <el-input
        v-model="editingContent"
        type="textarea"
        :rows="15"
        :placeholder="$t('textSplit.editChunkPlaceholder', '请输入文本块内容...')"
      />
      <template #footer>
        <el-button @click="editChunkDialogOpen = false">{{ $t('common.cancel', '取消') }}</el-button>
        <el-button type="primary" @click="handleSaveEdit">{{ $t('common.save', '保存') }}</el-button>
      </template>
    </el-dialog>

    <!-- 筛选对话框 -->
    <el-dialog v-model="filterDialogOpen" :title="$t('datasets.moreFilters', '更多筛选')" width="500px">
      <div class="filter-dialog-content">
        <!-- 文本块内容筛选 -->
        <div class="filter-section">
          <div class="filter-label">{{ $t('textSplit.contentKeyword', '文本块内容') }}</div>
          <el-input
            v-model="advancedFilters.contentKeyword"
            :placeholder="$t('textSplit.contentKeywordPlaceholder', '输入关键词搜索文本块内容')"
            clearable
          />
        </div>

        <!-- 字数范围筛选 -->
        <div class="filter-section">
          <div class="filter-label-row">
            <span class="filter-label">{{ $t('textSplit.characterRange', '字数范围') }}</span>
            <span class="filter-value">{{ advancedFilters.sizeRange[0] }} - {{ advancedFilters.sizeRange[1] }}</span>
          </div>
          <el-slider
            v-model="advancedFilters.sizeRange"
            :min="0"
            :max="10000"
            :step="100"
            range
            show-stops
            :marks="[
              { value: 0, label: '0' },
              { value: 10000, label: '10000' },
            ]"
          />
        </div>

        <!-- 问题状态筛选 -->
        <div class="filter-section">
          <div class="filter-label">{{ $t('textSplit.questionStatus', '问题状态') }}</div>
          <el-radio-group v-model="advancedFilters.hasQuestions">
            <el-radio :label="null">{{ $t('textSplit.allChunks', '全部文本块') }}</el-radio>
            <el-radio :label="true">{{ $t('textSplit.generatedQuestions2', '已生成问题') }}</el-radio>
            <el-radio :label="false">{{ $t('textSplit.ungeneratedQuestions', '未生成问题') }}</el-radio>
          </el-radio-group>
        </div>
      </div>
      <template #footer>
        <el-button @click="handleResetFilters">{{ $t('common.reset', '重置') }}</el-button>
        <el-button @click="filterDialogOpen = false">{{ $t('common.cancel', '取消') }}</el-button>
        <el-button type="primary" @click="handleApplyFilters">{{ $t('common.apply', '应用') }}</el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑标签对话框 -->
    <el-dialog
      v-model="tagDialogOpen"
      :title="
        tagDialogMode === 'add'
          ? $t('domain.dialog.addTitle', '添加一级标签')
          : tagDialogMode === 'edit'
            ? $t('domain.dialog.editTitle', '编辑标签')
            : $t('domain.dialog.addChildTitle', '添加子标签')
      "
      width="500px"
    >
      <div class="tag-dialog-content">
        <p v-if="tagDialogMode === 'add'">{{ $t('domain.dialog.inputRoot', '请输入一级标签名称') }}</p>
        <p v-else-if="tagDialogMode === 'edit'">{{ $t('domain.dialog.inputEdit', '请输入标签名称') }}</p>
        <p v-else>{{ $t('domain.dialog.inputChild', { label: tagParentNode }, `请输入 ${tagParentNode} 的子标签名称`) }}</p>
        <el-input
          v-model="tagLabelValue"
          :placeholder="$t('domain.dialog.labelName', '标签名称')"
          clearable
          @keyup.enter="handleSubmitTag"
        />
      </div>
      <template #footer>
        <el-button @click="tagDialogOpen = false">{{ $t('common.cancel', '取消') }}</el-button>
        <el-button type="primary" :loading="tagSaving" :disabled="!tagLabelValue?.trim()" @click="handleSubmitTag">
          {{ tagSaving ? $t('common.saving', '保存中...') : $t('common.save', '保存') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 删除标签确认对话框 -->
    <el-dialog v-model="tagDeleteDialogOpen" :title="$t('common.confirmDelete', '确认删除')" width="400px">
      <div class="tag-delete-content">
        <p>
          {{ $t('domain.dialog.deleteConfirm', { label: tagCurrentNode?.label }, `确定要删除标签 "${tagCurrentNode?.label}" 吗？`) }}
        </p>
        <p v-if="tagCurrentNode?.child && tagCurrentNode.child.length > 0" style="color: var(--el-color-warning)">
          {{ $t('domain.dialog.deleteWarning', '删除此标签将同时删除其所有子标签') }}
        </p>
      </div>
      <template #footer>
        <el-button @click="tagDeleteDialogOpen = false">{{ $t('common.cancel', '取消') }}</el-button>
        <el-button type="danger" :loading="tagSaving" @click="handleConfirmDeleteTag">
          {{ tagSaving ? $t('common.deleting', '删除中...') : $t('common.delete', '删除') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 全屏文件列表对话框 -->
    <el-dialog
      v-model="fileListDialogOpen"
      :title="$t('textSplit.uploadedFiles', '已上传文献')"
      width="80%"
      top="5vh"
    >
      <!-- 搜索框和操作按钮 -->
      <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; gap: 12px">
        <el-input
          v-model="searchFileName"
          :placeholder="$t('textSplit.searchFiles', '搜索文件名...')"
          clearable
          style="max-width: 400px"
          @clear="handleSearchFiles"
          @keyup.enter="handleSearchFiles"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <div style="display: flex; gap: 8px">
          <el-button
            v-if="filesTotal > 0"
            size="small"
            :type="selectedFileIds.length === filesTotal ? 'primary' : 'default'"
            @click="handleToggleSelectAllFiles"
          >
            {{ selectedFileIds.length === filesTotal ? $t('gaPairs.deselectAllFiles', '取消全选') : $t('gaPairs.selectAllFiles', '全选') }}
          </el-button>
          <el-button
            v-if="filesTotal > 0"
            size="small"
            type="primary"
            :disabled="selectedFileIds.length === 0"
            @click="batchGenerateGaDialogOpen = true"
          >
            <el-icon><MagicStick /></el-icon>
            {{ $t('gaPairs.batchGenerate', '批量生成GA对') }}
          </el-button>
        </div>
      </div>

      <el-table
        ref="fileTableRef"
        :data="filesDisplay"
        :row-key="row => String(row.id || row.fileId)"
        v-loading="filesLoading"
        size="default"
        style="width: 100%"
        @selection-change="handleTableSelectionChange"
      >
        <el-table-column
          type="selection"
          width="55"
          :reserve-selection="true"
          :selectable="() => true"
        />
        <el-table-column
          prop="file_name"
          :label="$t('textSplit.fileName', '文件名')"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column
          prop="size"
          :label="$t('textSplit.fileSize', '大小')"
          width="120"
        />
        <el-table-column :label="$t('gaPairs.gaPairs', 'GA对')" width="150">
          <template #default="{ row }">
            <GaPairsIndicator
              :project-id="projectId"
              :file-id="String(row.id || row.fileId)"
              :file-name="row.file_name || row.fileName || row.name"
            />
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions', '操作')" width="180">
          <template #default="{ row }">
            <el-button size="small" link @click="handleViewFile(row)">
              {{ $t('textSplit.view', '查看') }}
            </el-button>
            <el-button size="small" link @click="handleDownloadFile(row)">
              {{ $t('textSplit.download', '下载') }}
            </el-button>
            <el-button size="small" type="danger" link @click="handleDeleteFile(row)">
              {{ $t('common.delete', '删除') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="uploaded-pagination" v-if="filesTotal > 0">
        <el-pagination
          background
          layout="sizes, prev, pager, next"
          :total="filesTotal"
          :page-size="filesPageSize"
          :current-page="filesPage"
          :page-sizes="[5, 10, 20, 50]"
          @current-change="handleFilesPageChange"
          @size-change="handleFilesSizeChange"
        />
      </div>
      <template #footer>
        <el-button @click="fileListDialogOpen = false">{{ $t('common.close', '关闭') }}</el-button>
      </template>
    </el-dialog>

    <!-- 批量生成GA对对话框 -->
    <BatchGenerateGaDialog
      v-model="batchGenerateGaDialogOpen"
      :project-id="projectId"
      :file-ids="selectedFileIds"
      @success="handleBatchGenerateGaSuccess"
    />

    <!-- 批量编辑文本块对话框 -->
    <BatchEditChunksDialog
      :visible.sync="batchEditDialogOpen"
      :selected-chunk-ids="selectedChunkIds"
      :total-chunks="chunks.length"
      :loading="batchEditLoading"
      @confirm="handleConfirmBatchEdit"
    />

    <!-- 进度蒙版 -->
    <el-dialog
      :model-value="progressDialogOpen"
      :title="$t('textSplit.processing', '处理中...')"
      width="360px"
      align-center
      :close-on-click-modal="false"
      :show-close="false"
      class="progress-dialog"
    >
      <div class="progress-body">
        <el-icon class="progress-icon" :size="28" color="#409EFF">
          <Loading />
        </el-icon>
        <div class="progress-text">
          <div>{{ progressText }}</div>
        </div>
      </div>
      <template #footer>
        <span class="progress-hint">{{ $t('textSplit.loading', '加载中...') }}</span>
      </template>
    </el-dialog>

    <!-- 领域树处理选择对话框 -->
    <el-dialog
      v-model="domainTreeActionDialogOpen"
      :title="domainTreeDialogTitle"
      width="500px"
      :before-close="() => { domainTreeActionDialogOpen = false; pendingSplitAction = null; pendingUploadAction = null; }"
    >
      <el-radio-group v-model="selectedDomainTreeAction" class="domain-tree-radio-group">
        <el-radio
          v-if="!isFirstUpload"
          value="revise"
          class="domain-tree-radio"
        >
          <div class="radio-label">
            <div class="radio-title">{{ $t('textSplit.domainTree.reviseOption', '修订领域树') }}</div>
            <div class="radio-desc">{{ $t('textSplit.domainTree.reviseDesc', '在现有领域树基础上，根据新文档内容进行修订和扩展') }}</div>
          </div>
        </el-radio>
        <el-radio value="rebuild" class="domain-tree-radio">
          <div class="radio-label">
            <div class="radio-title">{{ $t('textSplit.domainTree.rebuildOption', '重建领域树') }}</div>
            <div class="radio-desc">{{ $t('textSplit.domainTree.rebuildDesc', '删除现有领域树，根据所有文档内容重新生成') }}</div>
          </div>
        </el-radio>
        <el-radio
          v-if="!isFirstUpload"
          value="keep"
          class="domain-tree-radio"
        >
          <div class="radio-label">
            <div class="radio-title">{{ $t('textSplit.domainTree.keepOption', '保持领域树不变') }}</div>
            <div class="radio-desc">{{ $t('textSplit.domainTree.keepDesc', '不修改现有领域树，仅处理文档分割') }}</div>
          </div>
        </el-radio>
      </el-radio-group>
      <template #footer>
        <el-button @click="domainTreeActionDialogOpen = false; pendingSplitAction = null; pendingUploadAction = null;">
          {{ $t('common.cancel', '取消') }}
        </el-button>
        <el-button type="primary" @click="handleDomainTreeAction(selectedDomainTreeAction)">
          {{ $t('common.confirm', '确认') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ElMessage, ElMessageBox } from 'element-plus';
import { fetchChunks, splitFiles, deleteChunk } from '@/api/textSplit';
import { uploadFile, fetchFiles, deleteFile } from '@/api/files';
import { generateQuestionsForChunk, cleanChunk } from '@/api/chunk';
import { fetchTags as fetchTagsApi, saveTag, deleteTag as deleteTagApi } from '@/api/tags';
import { createTask } from '@/api/task';
import { useModelStore } from '@/stores/model';
import DomainTreeNode from '@/components/DomainTreeNode.vue';
import GaPairsIndicator from '@/components/files/GaPairsIndicator.vue';
import BatchGenerateGaDialog from '@/components/files/BatchGenerateGaDialog.vue';
import BatchEditChunksDialog from '@/components/text-split/BatchEditChunksDialog.vue';
import http from '@/api/http';
import { getChunk, updateChunk, batchEditChunks } from '@/api/textSplit';
import {
  ArrowUp,
  ArrowDown,
  FullScreen,
  Loading,
  View,
  Delete,
  Edit,
  CollectionTag,
  Brush,
  Upload,
  Document,
  Download,
  Filter,
  MagicStick,
  MoreFilled,
  Plus,
  ArrowUp as ExpandLess,
  ArrowDown as ExpandMore,
  MoreFilled as MoreVert,
  Search,
  Refresh,
} from '@element-plus/icons-vue';
import MarkdownIt from 'markdown-it';

const route = useRoute();
const { t, locale } = useI18n();
const modelStore = useModelStore();

const projectId = route.params.projectId;

// Markdown 渲染器
const md = new MarkdownIt();

const renderedChunk = computed(() => {
  if (!currentChunk.value) return '';
  const text = currentChunk.value.content || '';
  return md.render(text);
});

// 领域分析相关状态
const domainActiveTab = ref('tree');
const tags = ref([]);
const tagsLoading = ref(false);
const tagDialogOpen = ref(false);
const tagDeleteDialogOpen = ref(false);
const tagDialogMode = ref('add'); // 'add' | 'edit' | 'addChild'
const tagCurrentNode = ref(null);
const tagParentNode = ref('');
const tagLabelValue = ref('');
const tagSaving = ref(false);

const loading = ref(false);
const splitting = ref(false);
const chunks = ref([]);
const tocData = ref('');
const domainTreeAction = ref('rebuild');
const selectedDomainTreeAction = ref('rebuild');
const viewDialogOpen = ref(false);
const currentChunk = ref(null);
const selectedChunkIds = ref([]);
const uploaderExpanded = ref(true);
const fileListDialogOpen = ref(false);
const activeTab = ref('split');
const filterDialogOpen = ref(false);
const advancedFilters = ref({
  contentKeyword: '',
  sizeRange: [0, 10000],
  hasQuestions: null, // null: 全部, true: 已生成, false: 未生成
});

// 文件列表
const files = ref([]);
const filesTotal = ref(0);
const filesPage = ref(1);
const filesPageSize = ref(10);
const filesLoading = ref(false);
const pendingFiles = ref([]);
const uploading = ref(false);
const selectedFileIds = ref([]);
const uploadRef = ref(null);
const searchFileName = ref('');
const batchGenerateGaDialogOpen = ref(false);
const fileTableRef = ref(null);
const batchEditDialogOpen = ref(false);
const batchEditLoading = ref(false);

// 批量编辑按钮标签（带选中数量提示）
const batchEditLabel = computed(() => {
  const base = t('batchEdit.batchEdit', '批量编辑');
  const count = selectedChunkIds.value.length || 0;
  return count > 0 ? `${base} (${count})` : base;
});

// 兼容不同字段命名，确保表格能展示
const filesDisplay = computed(() =>
  (files.value || []).map((f) => ({
    ...f,
    id: f.id || f.fileId,
    file_name: f.file_name || f.fileName || f.name,
    size: f.size || f.file_size || f.filesize,
  })),
);

// 根据筛选条件过滤文本块
const filteredChunks = computed(() => {
  let result = [...chunks.value];

  // 根据选中文件过滤（如果选中了文件）
  if (selectedFileIds.value.length > 0) {
    // 获取选中文件对应的文件名列表
    const selectedFileNames = filesDisplay.value
      .filter((f) => selectedFileIds.value.includes(String(f.id || f.fileId)))
      .map((f) => f.file_name || f.fileName || f.name);
    
    // 根据 fileId 或 fileName 过滤文本块
    result = result.filter((chunk) => {
      const chunkFileId = String(chunk.fileId || chunk.file_id || '');
      const chunkFileName = chunk.fileName || chunk.file_name || '';
      
      // 检查是否匹配选中的文件ID或文件名
      return (
        selectedFileIds.value.includes(chunkFileId) ||
        selectedFileNames.some((name) => name === chunkFileName)
      );
    });
  }

  // 内容关键词筛选
  if (advancedFilters.value.contentKeyword) {
    const keyword = advancedFilters.value.contentKeyword.toLowerCase();
    result = result.filter((chunk) => {
      const content = (chunk.content || '').toLowerCase();
      return content.includes(keyword);
    });
  }

  // 字数范围筛选
  const [minSize, maxSize] = advancedFilters.value.sizeRange;
  result = result.filter((chunk) => {
    const size = chunk.size || 0;
    return size >= minSize && size <= maxSize;
  });

  // 问题状态筛选
  if (advancedFilters.value.hasQuestions !== null) {
    result = result.filter((chunk) => {
      const questions = chunk.Questions || chunk.questions || [];
      const hasQuestions = questions.length > 0;
      return hasQuestions === advancedFilters.value.hasQuestions;
    });
  }

  return result;
});

// 计算活跃筛选条件数
const activeFilterCount = computed(() => {
  let count = 0;
  if (advancedFilters.value.contentKeyword) count++;
  if (advancedFilters.value.sizeRange[0] > 0 || advancedFilters.value.sizeRange[1] < 10000) count++;
  if (advancedFilters.value.hasQuestions !== null) count++;
  return count;
});

// 渲染 TOC 为 HTML
const renderedToc = computed(() => {
  if (!tocData.value) return '';
  const tocText = typeof tocData.value === 'string' ? tocData.value : Array.isArray(tocData.value) ? tocData.value.join('\n') : '';
  return md.render(tocText);
});

// 获取标签树
const fetchTags = async () => {
  try {
    tagsLoading.value = true;
    const response = await fetchTagsApi(projectId);
    // http 拦截器已经处理了响应格式，直接使用 response
    tags.value = response?.tags || [];
  } catch (error) {
    console.error('获取标签失败', error);
    ElMessage.error(error?.message || t('domain.errors.fetchFailed', '获取标签失败'));
    tags.value = [];
  } finally {
    tagsLoading.value = false;
  }
};

// 打开添加一级标签对话框
const handleAddRootTag = () => {
  tagDialogMode.value = 'add';
  tagCurrentNode.value = null;
  tagParentNode.value = '';
  tagLabelValue.value = '';
  tagDialogOpen.value = true;
};

// 打开编辑标签对话框
const handleEditTag = (node) => {
  tagDialogMode.value = 'edit';
  tagCurrentNode.value = { id: node.id, label: node.label };
  tagLabelValue.value = node.label;
  tagDialogOpen.value = true;
};

// 打开添加子标签对话框
const handleAddChildTag = (parentNode) => {
  tagDialogMode.value = 'addChild';
  tagParentNode.value = parentNode.label;
  tagCurrentNode.value = parentNode;
  tagLabelValue.value = '';
  tagDialogOpen.value = true;
};

// 打开删除标签对话框
const handleDeleteTag = (node) => {
  tagCurrentNode.value = node;
  tagDeleteDialogOpen.value = true;
};

// 查找并更新节点
const findAndUpdateNode = (nodes, targetNode, newLabel) => {
  return nodes.map((node) => {
    // 使用 id 或引用比较
    if ((node.id && targetNode.id && node.id === targetNode.id) || node === targetNode) {
      return { ...node, label: newLabel };
    }
    if (node.child && node.child.length > 0) {
      return { ...node, child: findAndUpdateNode(node.child, targetNode, newLabel) };
    }
    return node;
  });
};

// 查找并删除节点
const findAndDeleteNode = (nodes, targetNode) => {
  return nodes
    .filter((node) => {
      // 使用 id 或引用比较
      return !((node.id && targetNode.id && node.id === targetNode.id) || node === targetNode);
    })
    .map((node) => {
      if (node.child && node.child.length > 0) {
        return { ...node, child: findAndDeleteNode(node.child, targetNode) };
      }
      return node;
    });
};

// 查找并添加子节点
const findAndAddChildNode = (nodes, parentNode, childLabel) => {
  return nodes.map((node) => {
    // 使用 id 或引用比较
    if ((node.id && parentNode.id && node.id === parentNode.id) || node === parentNode) {
      const childArray = node.child || [];
      return {
        ...node,
        child: [...childArray, { label: childLabel, child: [] }],
      };
    }
    if (node.child && node.child.length > 0) {
      return { ...node, child: findAndAddChildNode(node.child, parentNode, childLabel) };
    }
    return node;
  });
};
 
// 保存标签更改（发送单个标签对象到后端）
const saveTagChanges = async (tagData) => {
  tagSaving.value = true;
  try {
    await saveTag(projectId, tagData);
    // http 拦截器已经处理了响应格式和错误
    await fetchTags();
    ElMessage.success(t('domain.messages.updateSuccess', '更新成功'));
  } catch (error) {
    console.error('保存标签失败', error);
    ElMessage.error(error?.message || t('domain.errors.saveFailed', '保存标签失败'));
  } finally {
    tagSaving.value = false;
  }
};

// 提交标签表单
const handleSubmitTag = async () => {
  if (!tagLabelValue.value?.trim()) {
    ElMessage.warning(t('domain.errors.labelRequired', '标签名称不能为空'));
    return;
  }

  let tagData = {};

  if (tagDialogMode.value === 'add') {
    // 添加一级标签
    tagData = {
      id: null,
      label: tagLabelValue.value,
      parentId: null,
    };
  } else if (tagDialogMode.value === 'edit') {
    // 编辑标签
    tagData = {
      id: tagCurrentNode.value.id,
      label: tagLabelValue.value,
      parentId: tagCurrentNode.value.parentId || null,
    };
  } else if (tagDialogMode.value === 'addChild') {
    // 添加子标签
    tagData = {
      id: null,
      label: tagLabelValue.value,
      parentId: tagCurrentNode.value.id,
    };
  }

  await saveTagChanges(tagData);
  tagDialogOpen.value = false;
};

// 确认删除标签
const handleConfirmDeleteTag = async () => {
  if (!tagCurrentNode.value) return;

  try {
    tagSaving.value = true;
    await deleteTagApi(projectId, tagCurrentNode.value.id);
    // http 拦截器已经处理了响应格式和错误
    ElMessage.success(t('common.deleteSuccess', '删除成功'));
    await fetchTags();
  } catch (error) {
    console.error('删除标签失败', error);
    ElMessage.error(error?.message || t('common.deleteFailed', '删除失败'));
  } finally {
    tagSaving.value = false;
    tagDeleteDialogOpen.value = false;
  }
};

const refreshChunks = async () => {
  try {
    loading.value = true;
    const resp = await fetchChunks(projectId);
    const data = resp?.data || resp;
    chunks.value = data?.chunks || [];
    tocData.value = data?.toc || data?.fileResult?.toc || '';
  } catch (error) {
    console.error('获取文本块失败', error);
    ElMessage.error(error?.message || t('textSplit.fetchChunksFailed', '获取文本块失败'));
  } finally {
    loading.value = false;
  }
};

// polling for active generation tasks temporarily disabled to avoid UI lag
/* 
let taskRefreshInterval = null;
const fetchActiveGenerationTasks = async () => {
  // implementation temporarily disabled
};
onMounted(() => {
  taskRefreshInterval = setInterval(() => {
    // fetchActiveGenerationTasks();
  }, 5000);
});
onUnmounted(() => {
  if (taskRefreshInterval) clearInterval(taskRefreshInterval);
});
*/

// const handleFilterChange = () => {
//   refreshChunks();
// };

// 开始分割选中的文件
const handleSplit = async () => {
  // 获取选中的文件
  if (selectedFileIds.value.length === 0) {
    ElMessage.warning(t('textSplit.selectFilesFirst', '请先选择要分割的文件'));
    return;
  }

  const model = modelStore.selectedModelInfo;
  if (!model) {
    ElMessage.warning(t('questions.selectModelFirst', '请先选择模型'));
    return;
  }

  // 提取选中文件的文件名
  const fileNames = filesDisplay.value
    .filter((f) => selectedFileIds.value.includes(String(f.id || f.fileId)))
    .map((f) => f.file_name || f.fileName || f.name)
    .filter(Boolean);

  if (fileNames.length === 0) {
    ElMessage.warning(t('textSplit.fileNamesRequired', '请填写文件名'));
    return;
  }

  // 检查是否是第一次上传（没有已存在的文件）
  const isFirstUpload = filesTotal.value === fileNames.length;

  // 如果不是第一次上传，需要选择领域树处理方式
  if (!isFirstUpload) {
    selectedDomainTreeAction.value = 'revise'; // 默认选择修订
    domainTreeActionDialogOpen.value = true;
    pendingSplitAction.value = { fileNames, model };
    return;
  }

  // 第一次上传，直接使用 rebuild
  await executeSplit(fileNames, model, 'rebuild');
};

// 执行分割操作
const executeSplit = async (fileNames, model, action) => {
  try {
    splitting.value = true;
    const language = locale.value === 'zh' ? 'zh-CN' : 'en';
    const resp = await splitFiles(projectId, {
      fileNames,
      model,
      language,
      domainTreeAction: action,
    });
    const data = resp?.data || resp;
    // 合并新生成的 chunks
    const newChunks = data?.chunks || [];
    if (newChunks.length > 0) {
      chunks.value = [...newChunks, ...chunks.value];
    }
    // 更新 toc
    tocData.value = data?.toc || data?.fileResult?.toc || tocData.value;
    // 刷新文本块列表
    await refreshChunks();
    ElMessage.success(t('textSplit.splitSuccess', '分割任务已完成'));
  } catch (error) {
    console.error('分割失败', error);
    ElMessage.error(error?.message || t('textSplit.splitFailed', '分割失败'));
  } finally {
    splitting.value = false;
  }
};

// 领域树处理对话框
const domainTreeActionDialogOpen = ref(false);
const pendingSplitAction = ref(null);
const pendingUploadAction = ref(null);

// 计算是否是第一次上传
const isFirstUpload = computed(() => {
  // 如果当前没有已上传的文件，则是第一次上传
  return filesTotal.value === 0;
});

// 计算对话框标题
const domainTreeDialogTitle = computed(() => {
  if (isFirstUpload.value) {
    return t('textSplit.domainTree.firstUploadTitle', '首次上传文档');
  }
  if (pendingSplitAction.value) {
    return t('textSplit.domainTree.splitTitle', '选择领域树处理方式');
  }
  return t('textSplit.domainTree.uploadTitle', '选择领域树处理方式');
});

// 处理领域树操作选择
const handleDomainTreeAction = (action) => {
  domainTreeActionDialogOpen.value = false;
  domainTreeAction.value = action;
  selectedDomainTreeAction.value = action;

  // 执行挂起的操作
  if (pendingSplitAction.value) {
    const { fileNames, model } = pendingSplitAction.value;
    executeSplit(fileNames, model, action);
    pendingSplitAction.value = null;
  } else if (pendingUploadAction.value) {
    const { files } = pendingUploadAction.value;
    executeUploadWithDomainTree(files, action);
    pendingUploadAction.value = null;
  }
};

const handleViewChunk = (row) => {
  currentChunk.value = row;
  viewDialogOpen.value = true;
};

const handleDeleteChunk = async (row) => {
  try {
    await ElMessageBox.confirm(
      t('textSplit.deleteChunkConfirm', '确定删除该文本块？'),
      t('common.confirmDelete', '确认删除'),
      {
        confirmButtonText: t('common.confirm', '确认'),
        cancelButtonText: t('common.cancel', '取消'),
        type: 'warning',
      },
    );
    await deleteChunk(projectId, row.id);
    chunks.value = chunks.value.filter((c) => c.id !== row.id);
    ElMessage.success(t('common.deleteSuccess', '删除成功'));
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.message || t('common.deleteFailed', '删除失败'));
    }
  }
};

const handleSelectionChange = (rows) => {
  selectedChunkIds.value = rows.map((r) => r.id);
};

const toggleChunk = (id, checked) => {
  if (checked) {
    if (!selectedChunkIds.value.includes(id)) {
      selectedChunkIds.value = [...selectedChunkIds.value, id];
    }
  } else {
    selectedChunkIds.value = selectedChunkIds.value.filter((x) => x !== id);
  }
};

const toggleSelectAll = (checked) => {
  if (checked) {
    selectedChunkIds.value = filteredChunks.value.map((c) => c.id);
  } else {
    selectedChunkIds.value = [];
  }
};

// 处理筛选变化
const handleFilterChange = () => {
  selectedChunkIds.value = []; // 清空选择
  refreshChunks();
};

// 格式化文件大小
const formatFileSize = (size) => {
  if (!size || size === 0) return '0B';
  if (size < 1024) return size + 'B';
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + 'KB';
  if (size < 1024 * 1024 * 1024) return (size / 1024 / 1024).toFixed(2) + 'MB';
  return (size / 1024 / 1024 / 1024).toFixed(2) + 'GB';
};

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch (e) {
    return dateStr;
  }
};

// 切换文件选择
const toggleFile = (fileId, checked) => {
  const id = String(fileId);
  if (checked) {
    if (!selectedFileIds.value.includes(id)) {
      selectedFileIds.value = [...selectedFileIds.value, id];
    }
  } else {
    selectedFileIds.value = selectedFileIds.value.filter((x) => x !== id);
  }
};

// 处理表格选择变化
const handleTableSelectionChange = (selection) => {
  selectedFileIds.value = selection.map((row) => String(row.id || row.fileId));
};

// 同步表格选择状态
const syncTableSelection = () => {
  if (!fileTableRef.value) return;
  // 清除所有选择
  fileTableRef.value.clearSelection();
  // 根据 selectedFileIds 设置选择
  filesDisplay.value.forEach((row) => {
    const id = String(row.id || row.fileId);
    if (selectedFileIds.value.includes(id)) {
      fileTableRef.value.toggleRowSelection(row, true);
    }
  });
};

// 查看文件
const handleViewFile = async (file) => {
  try {
    const response = await fetch(`/api/projects/${projectId}/preview/${file.id || file.fileId}`);
    if (!response.ok) {
      throw new Error(t('textSplit.fetchFileFailed', '获取文件内容失败'));
    }
    const data = await response.json();
    currentChunk.value = {
      id: file.id || file.fileId,
      name: file.file_name || file.fileName,
      content: data.content || data,
    };
    viewDialogOpen.value = true;
  } catch (error) {
    console.error('查看文件失败', error);
    ElMessage.error(error?.message || t('textSplit.fetchFileFailed', '获取文件内容失败'));
  }
};

// 下载文件
const handleDownloadFile = async (file) => {
  try {
    const response = await fetch(`/api/projects/${projectId}/preview/${file.id || file.fileId}`);
    if (!response.ok) {
      throw new Error(t('textSplit.fetchFileFailed', '获取文件内容失败'));
    }
    const data = await response.json();
    const content = data.content || data;
    const fileName = file.file_name || file.fileName || 'download.txt';
    const downloadName = fileName.toLowerCase().endsWith('.pdf') ? fileName.slice(0, -4) + '.md' : fileName;

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = downloadName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('下载文件失败', error);
    ElMessage.error(error?.message || t('textSplit.downloadFailed', '下载文件失败'));
  }
};

// 移除待上传文件
const removePendingFile = (index) => {
  pendingFiles.value.splice(index, 1);
};

// 上传待上传文件
const handleUploadPendingFiles = async () => {
  if (pendingFiles.value.length === 0) return;
  if (!modelStore.selectedModelInfo) {
    ElMessage.warning(t('questions.selectModelFirst', '请先选择模型'));
    return;
  }

  // 检查是否是第一次上传
  const isFirstUpload = filesTotal.value === 0;

  // 如果不是第一次上传，需要选择领域树处理方式
  if (!isFirstUpload) {
    selectedDomainTreeAction.value = 'revise'; // 默认选择修订
    domainTreeActionDialogOpen.value = true;
    pendingUploadAction.value = { files: [...pendingFiles.value] };
    return;
  }

  // 第一次上传，直接使用 rebuild
  await executeUploadWithDomainTree(pendingFiles.value, 'rebuild');
};

// 执行上传并处理领域树
const executeUploadWithDomainTree = async (filesToUpload, action) => {
  try {
    uploading.value = true;
    const uploadedFileNames = [];
    
    // 上传文件
    for (const file of filesToUpload) {
      const result = await uploadFile(projectId, file);
      // 提取文件名
      const fileName = result?.file_name || result?.fileName || file.name;
      if (fileName) {
        uploadedFileNames.push(fileName);
      }
    }
    
    if (uploadedFileNames.length === 0) {
      throw new Error('没有成功上传的文件');
    }
    
    // 创建文件处理任务（参考 Next.js 的 useFileProcessing.js）
    try {
      const currentLanguage = locale.value === 'zh' ? '中文' : 'en';
      const modelInfo = modelStore.selectedModelInfo;
      
      if (!modelInfo) {
        throw new Error('请先选择模型');
      }
      
      // 创建任务
      await createTask(projectId, {
        taskType: 'file-processing',
        modelInfo: typeof modelInfo === 'string' ? modelInfo : JSON.stringify(modelInfo),
        language: currentLanguage,
        detail: '文件处理任务',
        note: {
          projectId,
          fileList: uploadedFileNames, // 文件名数组
          domainTreeAction: action, // 领域树处理方式
          // strategy 和 vsionModel 暂时不传，Django 后端会根据文件类型自动处理
        }
      });
      
      ElMessage.success(t('textSplit.uploadSuccess', '文件上传成功，处理任务已创建'));
    } catch (taskError) {
      console.error('创建处理任务失败', taskError);
      // 即使任务创建失败，文件已经上传成功，所以只显示警告
      ElMessage.warning(t('textSplit.uploadSuccessButTaskFailed', '文件上传成功，但创建处理任务失败，请手动点击"开始分割"按钮'));
    }
    
    pendingFiles.value = [];
    await refreshFiles();
  } catch (error) {
    console.error('文件上传失败', error);
    ElMessage.error(error?.message || t('textSplit.uploadFailed', '文件上传失败'));
  } finally {
    uploading.value = false;
  }
};

// 获取文本块预览
const getChunkPreview = (content, maxLength = 150) => {
  if (!content) return '';
  return content.length > maxLength ? `${content.substring(0, maxLength)}...` : content;
};

// 编辑文本块
const editChunkDialogOpen = ref(false);
const editingChunk = ref(null);
const editingContent = ref('');

const handleEditChunk = async (chunk) => {
  try {
    const data = await getChunk(projectId, encodeURIComponent(chunk.id));
    // http interceptor may unwrap data; ensure we have object
    const chunkData = data?.data || data || data?.chunk || data;
    editingChunk.value = chunkData;
    editingContent.value = chunkData.content || '';
    editChunkDialogOpen.value = true;
  } catch (error) {
    console.error('获取文本块失败', error);
    ElMessage.error(error?.message || t('textSplit.fetchChunkFailed', '获取文本块失败'));
  }
};

const handleSaveEdit = async () => {
  if (!editingChunk.value) return;
  try {
    const payload = { content: editingContent.value };
    const resp = await updateChunk(projectId, encodeURIComponent(editingChunk.value.id), payload);
    // resp may be API wrapper result
    ElMessage.success(t('textSplit.editChunkSuccess', '编辑成功'));
    editChunkDialogOpen.value = false;
    await refreshChunks();
  } catch (error) {
    console.error('编辑文本块失败', error);
    ElMessage.error(error?.message || t('textSplit.editChunkFailed', '编辑文本块失败'));
  }
};

// 文件上传
// 处理文件选择
const handleFileSelect = (file) => {
  if (file.raw) {
    pendingFiles.value.push(file.raw);
  }
};

const refreshFiles = async () => {
  try {
    filesLoading.value = true;
    const params = {
      page: filesPage.value,
      pageSize: filesPageSize.value,
    };
    if (searchFileName.value && searchFileName.value.trim()) {
      params.fileName = searchFileName.value.trim();
    }
    const resp = await fetchFiles(projectId, params);
    const data = resp?.data || resp;
    const list = data?.data || data || [];
    files.value = Array.isArray(list) ? list : [];
    filesTotal.value = data?.total || (Array.isArray(list) ? list.length : 0);
  } catch (error) {
    console.error('获取文件列表失败', error);
    ElMessage.error(error?.message || t('textSplit.fetchFilesFailed', '获取文件列表失败'));
  } finally {
    filesLoading.value = false;
  }
};

// 搜索文件
const handleSearchFiles = () => {
  filesPage.value = 1;
  refreshFiles();
};

// 全选/取消全选文件
const handleToggleSelectAllFiles = async () => {
  if (selectedFileIds.value.length === filesTotal.value) {
    // 取消全选
    selectedFileIds.value = [];
    syncTableSelection();
  } else {
    // 全选：获取所有文件的ID
    try {
      const resp = await fetchFiles(projectId, { getAllIds: 'true' });
      const data = resp?.data || resp;
      const allFileIds = data?.allFileIds || [];
      selectedFileIds.value = allFileIds.map((id) => String(id));
      syncTableSelection();
    } catch (error) {
      console.error('全选文件失败:', error);
      // 如果API调用失败，回退到选择当前页面的文件
      selectedFileIds.value = filesDisplay.value.map((file) => String(file.id || file.fileId));
      syncTableSelection();
    }
  }
};

// 批量生成GA对成功回调
const handleBatchGenerateGaSuccess = () => {
  selectedFileIds.value = [];
  refreshFiles();
};

const handleFilesPageChange = (page) => {
  filesPage.value = page;
  refreshFiles();
};

const handleFilesSizeChange = (size) => {
  filesPageSize.value = size;
  filesPage.value = 1;
  refreshFiles();
};

const handleDeleteFile = async (file) => {
  try {
    await ElMessageBox.confirm(
      t('textSplit.deleteFileConfirm', '确定要删除该文件及其关联的文本块/问题/数据集吗？'),
      t('common.confirmDelete', '确认删除'),
      {
        confirmButtonText: t('common.confirm', '确认'),
        cancelButtonText: t('common.cancel', '取消'),
        type: 'warning',
      },
    );
    await deleteFile(projectId, file.id, domainTreeAction.value);
    ElMessage.success(t('common.deleteSuccess', '删除成功'));
    await refreshFiles();
    await refreshChunks();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除文件失败', error);
      ElMessage.error(error?.message || t('common.deleteFailed', '删除失败'));
    }
  }
};

const toggleUploader = () => {
  uploaderExpanded.value = !uploaderExpanded.value;
};

const openFileListDialog = () => {
  fileListDialogOpen.value = true;
};

const progressDialogOpen = computed(() => loading.value || filesLoading.value || splitting.value);
const progressText = computed(() => {
  if (splitting.value) return t('textSplit.processing', '处理中...');
  if (filesLoading.value) return t('textSplit.fetchingDocuments', '正在获取文档...');
  if (loading.value) return t('textSplit.loading', '加载中...');
  return '';
});

// 生成问题（支持批量或单个）
const handleGenerateQuestions = async (chunkIds) => {
  // normalize ids to an array of strings to avoid "ids is not iterable" errors
  const normalizeIds = (input) => {
    if (!input) return [];
    if (Array.isArray(input)) return input.map((v) => String(v));
    if (typeof input === 'string' || typeof input === 'number') return [String(input)];
    if (typeof input[Symbol.iterator] === 'function') {
      try {
        return Array.from(input).map((v) => String(v));
      } catch (e) {
        // fallthrough
      }
    }
    if (typeof input === 'object') {
      // try extracting values
      try {
        const vals = Object.values(input);
        return vals.reduce((acc, v) => {
          if (Array.isArray(v)) return acc.concat(v.map((x) => String(x)));
          return acc.concat(String(v));
        }, []);
      } catch (e) {
        return [];
      }
    }
    return [];
  };

  const raw = typeof chunkIds !== 'undefined' ? chunkIds : selectedChunkIds.value;
  const ids = normalizeIds(raw);
  if (!ids || ids.length === 0) {
    ElMessage.warning(t('textSplit.selectChunksFirst', '请先选择文本块'));
    return;
  }
  const model = modelStore.selectedModelInfo;
  if (!model) {
    ElMessage.warning(t('questions.selectModelFirst', '请先选择模型'));
    return;
  }
  const language = locale.value === 'zh' ? '中文' : 'en';
  try {
    loading.value = true;
    // For multiple chunks or single chunk, prefer creating a background task
    // Use a distinct taskType for single-chunk generation so tasks can be filtered separately
    if (ids.length > 1) {
      try {
        {
          const taskResp = await createTask(projectId, {
            taskType: 'question-generation',
            modelInfo: model,
            language,
            detail: '批量生成问题',
            note: {
              chunkIds: ids,
              enableGaExpansion: true,
            },
          });
          const taskId = taskResp?.id || taskResp?.taskId || taskResp?.data?.id;
          const tasksUrl = `/projects/${projectId}/tasks`;
          if (taskId) {
            ElMessage({
              message: `${t('tasks.createSuccess', '后台任务已创建，系统将异步生成问题')} <a href="${tasksUrl}?highlight=${taskId}" target="_blank" style="color: #fff; text-decoration: underline;">${t('tasks.viewTask', '查看任务')}</a>`,
              type: 'success',
              dangerouslyUseHTMLString: true,
            });
          } else {
            ElMessage.success(t('tasks.createSuccess', '后台任务已创建，系统将异步生成问题'));
          }
        }
        // refresh chunks list later if backend notifies; for now just return
        return;
      } catch (taskErr) {
        console.error('创建批量生成问题后台任务失败', taskErr);
        ElMessage.error(taskErr?.message || t('tasks.createFailed', '创建任务失败'));
        // fall back to synchronous generation if task creation fails
      }
    }
    // If single id, create a dedicated single-chunk generation task so it appears separately
    if (ids.length === 1) {
      const singleChunkId = ids[0];
      try {
        {
          const taskResp = await createTask(projectId, {
            taskType: 'question-generation-single',
            modelInfo: model,
            language,
            detail: `为文本块 ${singleChunkId} 生成问题`,
            note: {
              chunkId: singleChunkId,
              enableGaExpansion: true,
            },
          });
          const taskId = taskResp?.id || taskResp?.taskId || taskResp?.data?.id;
          const tasksUrl = `/projects/${projectId}/tasks`;
          if (taskId) {
            ElMessage({
              message: `${t('tasks.createSuccess', '后台任务已创建，系统将异步生成问题')} <a href="${tasksUrl}?highlight=${taskId}" target="_blank" style="color: #fff; text-decoration: underline;">${t('tasks.viewTask', '查看任务')}</a>`,
              type: 'success',
              dangerouslyUseHTMLString: true,
            });
          } else {
            ElMessage.success(t('tasks.createSuccess', '后台任务已创建，系统将异步生成问题'));
          }
        }
        return;
      } catch (taskErr) {
        console.error('创建单个文本块生成问题后台任务失败，回退至同步生成', taskErr);
        ElMessage.warning(t('tasks.createFailed', '创建任务失败') + ': ' + (taskErr?.message || ''));
        // fall through to synchronous generation as fallback
      }
    }

    // Fallback synchronous generation (for single or when task creation failed)
    for (const chunkId of ids) {
      await generateQuestionsForChunk(projectId, chunkId, {
        model,
        language,
        enableGaExpansion: true,
      });
    }
    ElMessage.success(t('textSplit.generateQuestionsSuccess', '问题生成完成'));
    await refreshChunks();
  } catch (error) {
    console.error('生成问题失败', error);
    ElMessage.error(error?.message || t('textSplit.generateQuestionsFailed', '生成问题失败'));
  } finally {
    // ensure all processing flags are cleared so the processing dialog closes
    loading.value = false;
    filesLoading.value = false;
    splitting.value = false;
  }
};

// 数据清洗（支持批量或单个）
const handleDataCleaning = async (chunkIds) => {
  const ids = chunkIds || selectedChunkIds.value;
  if (!ids || ids.length === 0) {
    ElMessage.warning(t('textSplit.selectChunksFirst', '请先选择文本块'));
    return;
  }
  const model = modelStore.selectedModelInfo;
  if (!model) {
    ElMessage.warning(t('questions.selectModelFirst', '请先选择模型'));
    return;
  }
  const language = locale.value === 'zh' ? '中文' : 'en';
  try {
    loading.value = true;
    for (const chunkId of ids) {
      await cleanChunk(projectId, chunkId, {
        model,
        language,
      });
    }
    ElMessage.success(t('textSplit.dataCleaningSuccess', '数据清洗完成'));
    await refreshChunks();
  } catch (error) {
    console.error('数据清洗失败', error);
    ElMessage.error(error?.message || t('textSplit.dataCleaningFailed', '数据清洗失败'));
  } finally {
    loading.value = false;
  }
};

// 应用筛选
const handleApplyFilters = () => {
  filterDialogOpen.value = false;
  // filteredChunks 会自动更新
};

// 重置筛选
const handleResetFilters = () => {
  advancedFilters.value = {
    contentKeyword: '',
    sizeRange: [0, 10000],
    hasQuestions: null,
  };
};

// 自动提取问题（创建后台任务）
const handleAutoGenerateQuestions = async () => {
  if (!modelStore.selectedModelInfo) {
    ElMessage.warning(t('questions.selectModelFirst', '请先选择模型'));
    return;
  }

  try {
    await createTask(projectId, {
      taskType: 'question-generation',
      modelInfo: modelStore.selectedModelInfo,
      language: locale.value === 'zh' ? '中文' : 'en',
      detail: '批量生成问题任务',
    });
    ElMessage.success(t('tasks.createSuccess', '后台任务已创建，系统将自动处理未生成问题的文本块'));
  } catch (error) {
    console.error('创建自动提取问题任务失败', error);
    ElMessage.error(t('tasks.createFailed', '创建任务失败') + ': ' + error?.message || '');
  }
};

// 自动数据清洗（创建后台任务）
const handleAutoDataCleaning = async () => {
  if (!modelStore.selectedModelInfo) {
    ElMessage.warning(t('questions.selectModelFirst', '请先选择模型'));
    return;
  }

  try {
    await createTask(projectId, {
      taskType: 'data-cleaning',
      modelInfo: modelStore.selectedModelInfo,
      language: locale.value === 'zh' ? '中文' : 'en',
      detail: '批量数据清洗任务',
    });
    ElMessage.success(t('tasks.createSuccess', '后台任务已创建，系统将自动处理所有文本块进行数据清洗'));
  } catch (error) {
    console.error('创建自动数据清洗任务失败', error);
    ElMessage.error(t('tasks.createFailed', '创建任务失败') + ': ' + (error?.message || ''));
  }
};

// 处理更多菜单命令
const handleMoreCommand = (command) => {
  switch (command) {
    case 'batchEdit':
      if (selectedChunkIds.value.length === 0) {
        ElMessage.warning(t('textSplit.selectChunksFirst', '请先选择文本块'));
        return;
      }
      batchEditDialogOpen.value = true;
      break;
    case 'batchDelete':
      handleBatchDelete();
      break;
    case 'export':
      handleExportChunks();
      break;
  }
};

// 批量删除
const handleBatchDelete = async () => {
  if (selectedChunkIds.value.length === 0) {
    ElMessage.warning(t('textSplit.selectChunksFirst', '请先选择文本块'));
    return;
  }

  try {
    await ElMessageBox.confirm(
      t('textSplit.batchDeleteConfirm', { count: selectedChunkIds.value.length }, `确定要删除选中的 ${selectedChunkIds.value.length} 个文本块吗？`),
      t('common.confirmDelete', '确认删除'),
      {
        confirmButtonText: t('common.confirm', '确认'),
        cancelButtonText: t('common.cancel', '取消'),
        type: 'warning',
      },
    );

    for (const chunkId of selectedChunkIds.value) {
      await deleteChunk(projectId, chunkId);
    }
    ElMessage.success(t('common.deleteSuccess', '删除成功'));
    selectedChunkIds.value = [];
    await refreshChunks();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败', error);
      ElMessage.error(error?.message || t('common.deleteFailed', '删除失败'));
    }
  }
};

// 处理批量编辑确认
const handleConfirmBatchEdit = async (editData) => {
  const chunkIds = editData.chunkIds && editData.chunkIds.length > 0 ? editData.chunkIds : selectedChunkIds.value;
  if (!chunkIds || chunkIds.length === 0) {
    ElMessage.warning(t('textSplit.selectChunksFirst', '请先选择文本块'));
    return;
  }

  try {
    batchEditLoading.value = true;
    const payload = {
      position: editData.position,
      content: editData.content,
      chunkIds,
    };
    const result = await batchEditChunks(projectId, payload);

    // result is backend response (Next.js returns { success: true, ... })
    if (result?.success) {
      ElMessage.success(t('batchEdit.success', '批量编辑成功'));
      selectedChunkIds.value = [];
      batchEditDialogOpen.value = false;
      await refreshChunks();
    } else {
      throw new Error(result?.message || '批量编辑失败');
    }
  } catch (error) {
    console.error('批量编辑失败', error);
    ElMessage.error(error?.message || t('batchEdit.failed', '批量编辑失败'));
  } finally {
    batchEditLoading.value = false;
  }
};

// 导出文本块
const handleExportChunks = () => {
  if (!chunks.value || chunks.value.length === 0) {
    ElMessage.warning(t('textSplit.noChunks', '暂无文本块'));
    return;
  }

  const exportData = chunks.value.map((chunk) => ({
    name: chunk.name,
    projectId: chunk.projectId,
    fileName: chunk.fileName || chunk.file_name,
    content: chunk.content,
    summary: chunk.summary,
    size: chunk.size,
  }));

  const jsonString = JSON.stringify(exportData, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `text-chunks-export-${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

// 初始加载
refreshChunks();
refreshFiles();
fetchTags();

// 监听文件列表变化，同步表格选择状态
watch(
  () => filesDisplay.value,
  () => {
    nextTick(() => {
      syncTableSelection();
    });
  },
  { deep: true }
);

// 监听全屏对话框打开，同步表格选择状态
watch(
  () => fileListDialogOpen.value,
  (val) => {
    if (val) {
      nextTick(() => {
        syncTableSelection();
      });
    }
  }
);
</script>

<style scoped>
.text-split-view {
  padding: 20px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 16px;
}

.header-content,
.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-content {
  justify-content: space-between;
  flex-wrap: wrap;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.uploader-card {
  margin-bottom: 16px;
}

.uploader-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: stretch;
}

.top-form {
  margin-top: 0;
}

.upload-left {
  background: var(--el-bg-color);
  border: 1px dashed var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.upload-inner {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
  text-align: center;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.upload-title {
  font-weight: 600;
  font-size: 16px;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.uploader-tips {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin-top: 8px;
  line-height: 1.5;
}

.uploader-tips p {
  margin: 0;
}

.pending-files {
  margin-top: 5px;
  padding-top: 5px;
  border-top: 1px solid var(--el-border-color-lighter);
  width: 100%;
  max-width: 100%;
  text-align: left; /* 文件列表区域左对齐 */
  box-sizing: border-box;
  overflow: hidden;
}

.pending-files-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
  text-align: left;
}

.pending-files-list {
  max-height: 200px;
  overflow-y: auto;
  overflow-x: hidden;
  margin-bottom: 12px;
  width: 100%;
  box-sizing: border-box;
}

.pending-file-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px 12px;
  border-radius: 4px;
  background: var(--el-bg-color-page);
  margin-bottom: 4px;
  width: 100%;
  max-width: 100%;
  gap: 8px;
  box-sizing: border-box;
  overflow: hidden;
}

.pending-file-item span {
  font-size: 14px;
  color: var(--el-text-color-primary);
  flex: 1;
  min-width: 0;
  max-width: 100%;
  word-break: break-word;
  word-wrap: break-word;
  white-space: normal;
  text-align: left;
  line-height: 1.5;
  overflow-wrap: break-word;
  overflow: hidden;
  box-sizing: border-box;
}

.pending-file-item .el-button {
  flex-shrink: 0;
  margin-left: 8px;
}

.upload-button {
  width: 100%;
}

.upload-right {
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: var(--el-bg-color-overlay);
  min-height: 0;
  overflow: hidden;
}

.uploaded-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.uploaded-title {
  font-weight: 600;
  font-size: 16px;
}

.uploaded-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
  flex-shrink: 0;
}

.uploaded-table {
  --el-table-header-bg-color: var(--el-bg-color);
}

.uploaded-pagination {
  display: flex;
  justify-content: flex-end;
  padding-top: 6px;
}

.uploaded-files-list {
  max-height: 400px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  transition: all 0.2s;
}

.file-item:hover {
  background: var(--el-bg-color-page);
  border-color: var(--el-color-primary-light-7);
}

.file-icon {
  font-size: 24px;
  color: var(--el-color-primary);
  margin-right: 12px;
}

.file-info {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 12px;
  flex-shrink: 0;
}

/* Chunk view dialog: make content scroll inside dialog instead of body */
.chunk-content {
  max-height: 70vh;
  overflow: hidden;
}
.chunk-content .chunk-markdown {
  max-height: calc(70vh - 120px);
  overflow: auto;
  padding-right: 8px;
}
.chunk-content .chunk-markdown :global(pre) {
  white-space: pre-wrap;
  word-break: break-word;
}

.ga-pairs-wrapper {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  white-space: nowrap;
  min-width: 0;
}

.ga-pairs-wrapper :deep(.el-tag) {
  white-space: nowrap !important;
  flex-shrink: 0;
  display: inline-flex !important;
  align-items: center;
  gap: 4px;
  line-height: 1.5;
  height: auto;
  min-height: 24px;
  padding: 2px 8px;
  max-width: none;
  overflow: visible;
  flex-wrap: nowrap !important;
}

.ga-pairs-wrapper :deep(.el-tag *) {
  white-space: nowrap !important;
  flex-shrink: 0;
  flex-wrap: nowrap !important;
}

.ga-pairs-wrapper :deep(.ga-tag-icon) {
  flex-shrink: 0 !important;
  margin-right: 0;
  display: inline-flex !important;
  align-items: center;
  white-space: nowrap !important;
}

.ga-pairs-wrapper :deep(.ga-tag-text) {
  white-space: nowrap !important;
  display: inline !important;
  flex-shrink: 0;
  flex-wrap: nowrap !important;
}

.filter-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 8px 0;
}

.filter-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.filter-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.filter-value {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.main-row {
  margin-top: 12px;
}

.main-tabs {
  margin-top: 0;
}

.main-card {
  margin-top: 12px;
  padding: 0 4px 12px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
}

.toc-box {
  background: var(--el-bg-color-page);
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;
  padding: 12px;
  min-height: 200px;
  white-space: pre-wrap;
  word-break: break-word;
}

.chunk-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.chunk-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  margin-bottom: 12px;
}

.chunk-toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selection-text {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.chunk-toolbar-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.chunk-list {
  min-height: 200px;
}

.chunk-card {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  margin-bottom: 12px;
  background: var(--el-bg-color);
  transition: all 0.2s ease-in-out;
}

.chunk-card:hover {
  border-color: var(--el-color-primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.chunk-card-selected {
  border-color: var(--el-color-primary);
  background: rgba(64, 158, 255, 0.06);
}

.chunk-card-content {
  display: flex;
  align-items: flex-start;
  padding: 16px 20px;
  gap: 12px;
}

.chunk-checkbox {
  margin-top: 2px;
}

.chunk-main {
  flex: 1;
  min-width: 0;
}

.chunk-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.chunk-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-color-primary-dark-2);
  flex: 1;
  min-width: 0;
}

.chunk-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chunk-tag {
  font-weight: 500;
  border-radius: 4px;
}

.chunk-preview {
  font-size: 14px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  opacity: 0.85;
  word-break: break-word;
}

.chunk-card-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.action-btn {
  transition: all 0.2s;
}

.action-btn:hover {
  transform: scale(1.1);
}

.action-btn-view {
  background: rgba(33, 150, 243, 0.08);
  color: var(--el-color-primary);
}

.action-btn-question {
  background: rgba(2, 136, 209, 0.08);
  color: var(--el-color-info);
}

.action-btn-clean {
  background: rgba(46, 125, 50, 0.08);
  color: var(--el-color-success);
}

.action-btn-edit {
  background: rgba(237, 108, 2, 0.08);
  color: var(--el-color-warning);
}

.action-btn-delete {
  background: rgba(211, 47, 47, 0.08);
  color: var(--el-color-danger);
}

.progress-dialog :deep(.el-dialog__body) {
  padding: 16px 20px;
}

.progress-body {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-icon {
  animation: spin 1s linear infinite;
}

.progress-text {
  font-size: 14px;
}

.progress-hint {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.domain-analysis-card {
  margin-top: 12px;
}

.domain-tabs {
  margin-top: 0;
}

.domain-tree-section,
.domain-structure-section {
  padding: 16px;
}

.domain-tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.domain-tree-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.domain-tree-content {
  min-height: 400px;
  max-height: 800px;
  overflow-y: auto;
}

.domain-tree-list {
  padding: 8px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
}

.domain-structure-section h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
}

.toc-content {
  min-height: 400px;
  max-height: 600px;
  overflow-y: auto;
  padding: 20px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
}

.toc-content::-webkit-scrollbar {
  width: 8px;
}

.toc-content::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}

.toc-content::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 4px;
}

.toc-content::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-darker);
}

.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
  font-size: 14px;
  line-height: 1.8;
  color: var(--el-text-color-primary);
  white-space: normal;
  word-break: break-word;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  margin-top: 20px;
  margin-bottom: 12px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--el-text-color-primary);
}

.markdown-body :deep(h1) {
  font-size: 20px;
  margin-top: 0;
}

.markdown-body :deep(h2) {
  font-size: 18px;
}

.markdown-body :deep(h3) {
  font-size: 16px;
  color: var(--el-color-primary);
  border-bottom: 1px solid var(--el-border-color-lighter);
  padding-bottom: 8px;
  margin-bottom: 16px;
}

.markdown-body :deep(p) {
  margin-bottom: 12px;
  line-height: 1.8;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin-left: 0;
  margin-bottom: 12px;
  padding-left: 24px;
  list-style-position: outside;
}

.markdown-body :deep(ul) {
  list-style-type: disc;
}

.markdown-body :deep(ol) {
  list-style-type: decimal;
}

.markdown-body :deep(li) {
  margin-bottom: 8px;
  line-height: 1.8;
  display: list-item;
}

.markdown-body :deep(ul ul),
.markdown-body :deep(ol ol),
.markdown-body :deep(ul ol),
.markdown-body :deep(ol ul) {
  margin-top: 8px;
  margin-bottom: 8px;
  padding-left: 24px;
}

.markdown-body :deep(ul ul) {
  list-style-type: circle;
}

.markdown-body :deep(ul ul ul) {
  list-style-type: square;
}

.markdown-body :deep(strong) {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.markdown-body :deep(code) {
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.markdown-body :deep(pre) {
  background: var(--el-fill-color-light);
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin-bottom: 12px;
}

.markdown-body :deep(pre code) {
  background: transparent;
  padding: 0;
}

.tag-dialog-content {
  padding: 8px 0;
}

.tag-dialog-content p {
  margin-bottom: 16px;
  color: var(--el-text-color-regular);
}

.tag-delete-content p {
  margin-bottom: 12px;
  color: var(--el-text-color-regular);
}

.domain-tree-radio-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 95%;
}

.domain-tree-radio {
  width: 100%;
  margin: 0;
  padding: 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  transition: all 0.2s;
}

.domain-tree-radio:hover {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.domain-tree-radio.is-checked {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.radio-label {
  margin-left: 8px;
}

.radio-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.radio-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}
</style>

