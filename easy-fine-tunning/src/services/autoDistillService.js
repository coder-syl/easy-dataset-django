import http from '@/api/http';

/**
 * 自动蒸馏服务（前台执行版本）
 * 基本逻辑从 Next.js 的 autoDistillService 迁移而来，改为使用 Django 原始 API（/projects/...）
 */
class AutoDistillService {
  constructor() {
    this.projectName = '';
  }

  /**
   * 执行自动蒸馏任务
   * @param {Object} config
   */
  async executeDistillTask(config) {
    const {
      projectId,
      topic,
      levels,
      tagsPerLevel,
      questionsPerTag,
      model,
      language,
      datasetType = 'single-turn',
      concurrencyLimit = 5,
      onProgress,
      onLog,
    } = config;

    this.projectName = '';

    try {
      // 初始化进度
      onProgress?.({
        stage: 'initializing',
        tagsTotal: 0,
        tagsBuilt: 0,
        questionsTotal: 0,
        questionsBuilt: 0,
        datasetsTotal: 0,
        datasetsBuilt: 0,
        multiTurnDatasetsTotal: 0,
        multiTurnDatasetsBuilt: 0,
      });

      // 获取项目名称（只获取一次）
      try {
        const project = await http.get(`/projects/${projectId}/`);
        const projectData = project?.data && Object.keys(project.data || {}).length ? project.data : project;
        if (projectData?.name) {
          this.projectName = projectData.name;
          this.addLog(onLog, `Using project name "${this.projectName}" as the top-level tag`);
        } else {
          this.projectName = topic;
          this.addLog(onLog, `Could not find project name, using topic "${topic}" as the top-level tag`);
        }
      } catch (err) {
        this.projectName = topic;
        this.addLog(onLog, `Failed to get project name, using topic "${topic}" instead: ${err.message}`);
      }

      this.addLog(
        onLog,
        `Starting to build tag tree for "${topic}", levels: ${levels}, tags per level: ${tagsPerLevel}, questions per tag: ${questionsPerTag}`,
      );

      // 1. 构建标签树
      await this.buildTagTree({
        projectId,
        topic,
        levels,
        tagsPerLevel,
        model,
        language,
        onProgress,
        onLog,
      });

      // 2. 为叶子标签生成问题
      await this.generateQuestionsForTags({
        projectId,
        levels,
        questionsPerTag,
        model,
        language,
        concurrencyLimit,
        onProgress,
        onLog,
      });

      // 3. 生成数据集（单轮、多轮或两者）
      if (datasetType === 'single-turn') {
        await this.generateDatasetsForQuestions({
          projectId,
          model,
          language,
          concurrencyLimit,
          onProgress,
          onLog,
        });
      } else if (datasetType === 'multi-turn') {
        await this.generateMultiTurnDatasetsForQuestions({
          projectId,
          model,
          language,
          concurrencyLimit,
          onProgress,
          onLog,
        });
      } else if (datasetType === 'both') {
        await this.generateDatasetsForQuestions({
          projectId,
          model,
          language,
          concurrencyLimit,
          onProgress,
          onLog,
        });
        await this.generateMultiTurnDatasetsForQuestions({
          projectId,
          model,
          language,
          concurrencyLimit,
          onProgress,
          onLog,
        });
      }

      onProgress?.({ stage: 'completed' });
      this.addLog(onLog, 'Auto distillation task completed');
    } catch (err) {
      console.error('自动蒸馏任务执行失败:', err);
      this.addLog(onLog, `Task execution error: ${err.message || 'Unknown error'}`);
      throw err;
    }
  }

  /**
   * 构建标签树
   */
  async buildTagTree(config) {
    const { projectId, topic, levels, tagsPerLevel, model, language, onProgress, onLog } = config;

    const projectName = this.projectName || topic;

    const buildTagsForLevel = async (parentTag = null, parentTagPath = '', level = 1) => {
      onProgress?.({ stage: `level${level}` });

      if (level > levels) return;

      // 获取当前层级已有标签
      let currentLevelTags = [];
      try {
        const res = await http.get(`/projects/${projectId}/distill/tags/all/`);
        const all = Array.isArray(res) ? res : res?.data || res || [];
        if (parentTag) {
          currentLevelTags = all.filter((tag) => tag.parentId === parentTag.id);
        } else {
          currentLevelTags = all.filter((tag) => !tag.parentId);
        }
      } catch (err) {
        console.error(`获取第 ${level} 级标签失败:`, err);
        this.addLog(onLog, `Failed to get level ${level} tags: ${err.message || 'Unknown error'}`);
        return;
      }

      const targetCount = tagsPerLevel;
      const currentCount = currentLevelTags.length;
      const needToCreate = Math.max(0, targetCount - currentCount);

      if (needToCreate > 0) {
        const parentTagName = level === 1 ? topic : parentTag?.label || '';
        this.addLog(onLog, `Tag tree level ${level}: Creating ${needToCreate} subtags for "${parentTagName}"...`);

        let tagPathWithProjectName;
        if (level === 1) {
          tagPathWithProjectName = projectName;
        } else if (!parentTagPath) {
          tagPathWithProjectName = projectName;
        } else if (!parentTagPath.startsWith(projectName)) {
          tagPathWithProjectName = `${projectName} > ${parentTagPath}`;
        } else {
          tagPathWithProjectName = parentTagPath;
        }

        try {
          const res = await http.post(`/projects/${projectId}/distill/tags/`, {
            parentTag: parentTagName,
            parentTagId: parentTag ? parentTag.id : null,
            tagPath: tagPathWithProjectName || parentTagName,
            count: needToCreate,
            model,
            language,
          });
          const list = Array.isArray(res) ? res : res?.data || [];

          onProgress?.({
            tagsBuilt: list.length,
            updateType: 'increment',
          });

          this.addLog(
            onLog,
            `Successfully created ${list.length} tags: ${list.map((tag) => tag.label).join(', ')}`,
          );

          currentLevelTags = [...currentLevelTags, ...list];
        } catch (err) {
          console.error(`创建第 ${level} 级标签失败:`, err);
          this.addLog(onLog, `Failed to create level ${level} tags: ${err.message || 'Unknown error'}`);
        }
      }

      if (level < levels) {
        for (const tag of currentLevelTags) {
          let tagPath;
          if (parentTagPath) {
            tagPath = `${parentTagPath} > ${tag.label}`;
          } else {
            tagPath = `${projectName} > ${tag.label}`;
          }
          await buildTagsForLevel(tag, tagPath, level + 1);
        }
      }
    };

    const leafTags = Math.pow(tagsPerLevel, levels);
    onProgress?.({ tagsTotal: leafTags });

    await buildTagsForLevel();
  }

  /**
   * 为叶子标签生成问题
   */
  async generateQuestionsForTags(config) {
    const { projectId, levels, questionsPerTag, model, language, concurrencyLimit = 5, onProgress, onLog } = config;

    onProgress?.({ stage: 'questions' });
    this.addLog(onLog, 'Tag tree built, starting to generate questions for leaf tags...');

    try {
      const res = await http.get(`/projects/${projectId}/distill/tags/all/`);
      const allTags = Array.isArray(res) ? res : res?.data || res || [];

      // children map
      const childrenMap = {};
      allTags.forEach((tag) => {
        if (tag.parentId) {
          if (!childrenMap[tag.parentId]) childrenMap[tag.parentId] = [];
          childrenMap[tag.parentId].push(tag);
        }
      });

      const leafTags = [];
      allTags.forEach((tag) => {
        if (!childrenMap[tag.id] && this.getTagDepth(tag, allTags) === levels) {
          leafTags.push(tag);
        }
      });

      this.addLog(onLog, `Found ${leafTags.length} leaf tags, starting to generate questions...`);

      const questionsRes = await http.get(`/projects/${projectId}/questions/tree/`, {
        params: { isDistill: 'yes' },
      });
      const allQuestions = Array.isArray(questionsRes)
        ? questionsRes
        : questionsRes?.data || questionsRes || [];

      const totalQuestionsToGenerate = leafTags.length * questionsPerTag;
      onProgress?.({ questionsTotal: totalQuestionsToGenerate });

      const generateQuestionTasks = [];

      for (const tag of leafTags) {
        const tagPath = this.getTagPath(tag, allTags);
        const existingQuestions = allQuestions.filter((q) => q.label === tag.label);
        const needToCreate = Math.max(0, questionsPerTag - existingQuestions.length);

        if (needToCreate > 0) {
          generateQuestionTasks.push({ tag, tagPath, needToCreate });
          this.addLog(onLog, `Preparing to generate ${needToCreate} questions for tag "${tag.label}"...`);
        } else {
          this.addLog(
            onLog,
            `Tag "${tag.label}" already has ${existingQuestions.length} questions, no need to generate new questions`,
          );
        }
      }

      this.addLog(
        onLog,
        `Total ${generateQuestionTasks.length} tags need questions, concurrency limit: ${concurrencyLimit}`,
      );

      for (let i = 0; i < generateQuestionTasks.length; i += concurrencyLimit) {
        const batch = generateQuestionTasks.slice(i, i + concurrencyLimit);
        await Promise.all(
          batch.map(async (task) => {
            const { tag, tagPath, needToCreate } = task;
            this.addLog(onLog, `Generating ${needToCreate} questions for tag "${tag.label}"...`);
            try {
              const resQ = await http.post(`/projects/${projectId}/distill/questions/`, {
                tagPath,
                currentTag: tag.label,
                tagId: tag.id,
                count: needToCreate,
                model,
                language,
              });
              const list = Array.isArray(resQ) ? resQ : resQ?.data || [];
              onProgress?.({
                questionsBuilt: list.length,
                updateType: 'increment',
              });
              this.addLog(
                onLog,
                `Successfully generated ${list.length} questions for tag "${tag.label}"`,
              );
            } catch (err) {
              console.error(`为标签 "${tag.label}" 生成问题失败:`, err);
              this.addLog(
                onLog,
                `Failed to generate questions for tag "${tag.label}": ${err.message || 'Unknown error'}`,
              );
            }
          }),
        );

        this.addLog(
          onLog,
          `Completed batch ${Math.min(i + concurrencyLimit, generateQuestionTasks.length)}/${
            generateQuestionTasks.length
          } of question generation`,
        );
      }
    } catch (err) {
      console.error('获取标签失败:', err);
      this.addLog(onLog, `Failed to get tags: ${err.message || 'Unknown error'}`);
    }
  }

  /**
   * 为问题生成单轮对话数据集
   */
  async generateDatasetsForQuestions(config) {
    const { projectId, model, language, concurrencyLimit = 5, onProgress, onLog } = config;

    onProgress?.({ stage: 'datasets' });
    this.addLog(onLog, 'Question generation completed, starting to generate answers...');

    try {
      const res = await http.get(`/projects/${projectId}/questions/tree/`, {
        params: { isDistill: 'yes' },
      });
      const allQuestions = Array.isArray(res) ? res : res?.data || res || [];

      const unanswered = allQuestions.filter((q) => !q.answered);
      const answered = allQuestions.filter((q) => q.answered);

      onProgress?.({
        datasetsTotal: allQuestions.length,
        datasetsBuilt: answered.length,
      });

      this.addLog(
        onLog,
        `Found ${unanswered.length} unanswered questions, preparing to generate answers...`,
      );
      this.addLog(onLog, `Dataset generation concurrency limit: ${concurrencyLimit}`);

      for (let i = 0; i < unanswered.length; i += concurrencyLimit) {
        const batch = unanswered.slice(i, i + concurrencyLimit);
        await Promise.all(
          batch.map(async (question) => {
            const label = `${question.label} (ID: ${question.id})`;
            this.addLog(onLog, `Generating answer for "${label}"...`);
            try {
              await http.post(`/projects/${projectId}/datasets/`, {
                projectId,
                questionId: question.id,
                model,
                language: language || 'zh-CN',
              });
              onProgress?.({
                datasetsBuilt: 1,
                updateType: 'increment',
              });
              this.addLog(onLog, `Successfully generated answer for "${label}"`);
            } catch (err) {
              console.error(`Failed to generate dataset for question "${question.id}":`, err);
              this.addLog(
                onLog,
                `Failed to generate answer for "${label}": ${err.message || 'Unknown error'}`,
              );
            }
          }),
        );

        this.addLog(
          onLog,
          `Completed batch ${Math.min(i + concurrencyLimit, unanswered.length)}/${unanswered.length} of dataset generation`,
        );
      }

      this.addLog(onLog, 'Dataset generation completed');
    } catch (err) {
      console.error('Dataset generation failed:', err);
      this.addLog(onLog, `Dataset generation error: ${err.message || 'Unknown error'}`);
      throw err;
    }
  }

  /**
   * 为问题生成多轮对话数据集
   */
  async generateMultiTurnDatasetsForQuestions(config) {
    const { projectId, model, language, concurrencyLimit = 2, onProgress, onLog } = config;

    onProgress?.({ stage: 'multi-turn-datasets' });
    this.addLog(onLog, 'Question generation completed, starting to generate multi-turn conversations...');

    try {
      const taskConfigRaw = await http.get(`/projects/${projectId}/tasks/`);
      const taskConfig =
        taskConfigRaw?.data && Object.keys(taskConfigRaw.data || {}).length
          ? taskConfigRaw.data
          : taskConfigRaw || {};

      const multiTurnConfig = {
        systemPrompt: taskConfig.multiTurnSystemPrompt || '',
        scenario: taskConfig.multiTurnScenario || '',
        rounds: taskConfig.multiTurnRounds || 3,
        roleA: taskConfig.multiTurnRoleA || '',
        roleB: taskConfig.multiTurnRoleB || '',
      };

      if (
        !multiTurnConfig.scenario ||
        !multiTurnConfig.roleA ||
        !multiTurnConfig.roleB ||
        !multiTurnConfig.rounds ||
        multiTurnConfig.rounds < 1
      ) {
        throw new Error('项目未配置多轮对话参数，请先在项目设置中配置多轮对话相关参数');
      }

      const res = await http.get(`/projects/${projectId}/questions/tree/`, {
        params: { isDistill: 'yes' },
      });
      const allQuestions = Array.isArray(res) ? res : res?.data || res || [];
      const answeredQuestions = allQuestions;

      if (!answeredQuestions.length) {
        this.addLog(onLog, 'No answered questions found, skipping multi-turn conversation generation');
        return;
      }

      const convRes = await http.get(`/projects/${projectId}/dataset-conversations/`, {
        params: { pageSize: 1000 },
      });
      const convData = convRes?.data && Array.isArray(convRes.data.conversations)
        ? convRes.data
        : convRes || {};
      const existingConversationIds = new Set(
        (convData.conversations || []).map((conv) => conv.questionId),
      );

      const questionsForMultiTurn = answeredQuestions.filter(
        (q) => !existingConversationIds.has(q.id),
      );

      onProgress?.({
        multiTurnDatasetsTotal: answeredQuestions.length,
        multiTurnDatasetsBuilt: answeredQuestions.length - questionsForMultiTurn.length,
      });

      this.addLog(
        onLog,
        `Found ${questionsForMultiTurn.length} questions ready for multi-turn conversation generation...`,
      );
      this.addLog(onLog, `Multi-turn generation concurrency limit: ${concurrencyLimit}`);

      for (let i = 0; i < questionsForMultiTurn.length; i += concurrencyLimit) {
        const batch = questionsForMultiTurn.slice(i, i + concurrencyLimit);
        await Promise.all(
          batch.map(async (question) => {
            const label = `${question.label} (ID: ${question.id})`;
            this.addLog(onLog, `Generating multi-turn conversation for "${label}"...`);
            try {
              await http.post(`/projects/${projectId}/dataset-conversations/`, {
                questionId: question.id,
                ...multiTurnConfig,
                model,
                language,
              });
              onProgress?.({
                multiTurnDatasetsBuilt: 1,
                updateType: 'increment',
              });
              this.addLog(onLog, `Multi-turn conversation generated for "${label}"`);
            } catch (err) {
              console.error('Failed to generate multi-turn dataset:', err);
              this.addLog(
                onLog,
                `Failed to generate multi-turn conversation for "${label}": ${err.message || 'Unknown error'}`,
              );
            }
          }),
        );
      }

      this.addLog(onLog, 'Multi-turn conversation generation completed');
    } catch (err) {
      console.error('Multi-turn dataset generation failed:', err);
      this.addLog(onLog, `Multi-turn dataset generation error: ${err.message || 'Unknown error'}`);
      throw err;
    }
  }

  /**
   * 获取标签深度
   */
  getTagDepth(tag, allTags) {
    let depth = 1;
    let current = tag;
    while (current.parentId) {
      depth += 1;
      current = allTags.find((t) => t.id === current.parentId);
      if (!current) break;
    }
    return depth;
  }

  /**
   * 获取标签路径，确保以项目名称开头
   */
  getTagPath(tag, allTags) {
    const projectName = this.projectName || '';
    const path = [];
    let current = tag;
    while (current) {
      path.unshift(current.label);
      if (current.parentId) {
        current = allTags.find((t) => t.id === current.parentId);
      } else {
        current = null;
      }
    }
    if (projectName && path.length > 0 && path[0] !== projectName) {
      path.unshift(projectName);
    }
    return path.join(' > ');
  }

  addLog(onLog, message) {
    if (typeof onLog === 'function') {
      onLog(message);
    }
  }
}

export const autoDistillService = new AutoDistillService();
export default autoDistillService;


