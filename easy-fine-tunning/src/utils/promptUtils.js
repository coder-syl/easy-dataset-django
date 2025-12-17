/**
 * 提示词设置相关工具函数
 */

/**
 * 从提示词键名解析语言
 * @param {string} promptKey 提示词键名
 * @returns {string} 语言代码 ('zh-CN' 或 'en')
 */
export const getLanguageFromPromptKey = (promptKey) => {
  return promptKey?.endsWith('_EN') ? 'en' : 'zh-CN';
};

/**
 * 判断是否应该显示当前提示词（基于语言）
 * @param {string} promptKey 提示词键名
 * @param {string} currentLanguage 当前界面语言
 * @returns {boolean} 是否应该显示
 */
export const shouldShowPrompt = (promptKey, currentLanguage) => {
  const promptLang = getLanguageFromPromptKey(promptKey);
  return promptLang === currentLanguage;
};

