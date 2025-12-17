// 默认项目任务配置
export const DEFAULT_SETTINGS = {
  textSplitMinLength: 2500,
  textSplitMaxLength: 4000,
  questionGenerationLength: 240,
  questionMaskRemovingProbability: 60,
  huggingfaceToken: '',
  concurrencyLimit: 5,
  visionConcurrencyLimit: 5,
  // 多轮对话数据集默认配置
  multiTurnSystemPrompt: '',
  multiTurnScenario: '',
  multiTurnRounds: 3,
  multiTurnRoleA: '',
  multiTurnRoleB: '',
  // 分块策略默认值
  splitType: 'recursive',
  chunkSize: 3000,
  chunkOverlap: 200,
  separator: '\\n\\n',
  customSeparator: '---',
  separatorsInput: '|,##,>,-',
  separators: ['|', '##', '>', '-'],
  splitLanguage: 'js',
};

