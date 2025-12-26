import { defineStore } from 'pinia';
import { fetchModelConfigs } from '../api/model';

export const useModelStore = defineStore('model', {
  state: () => ({
    modelConfigList: [],
    selectedModelInfo: null,
  }),

  actions: {
    setModelConfigList(list) {
      this.modelConfigList = Array.isArray(list) ? list : [];
    },

    setSelectedModel(model) {
      this.selectedModelInfo = model;
    },

    async loadModelConfigs() {
      try {
        // 直接调用全局模型配置接口（不需要 projectId）
        const response = await fetchModelConfigs();
         
        // HTTP 拦截器已经解包了 { code: 0, data: {...} } 格式，返回的是 data 部分
        // Django 返回格式: { code: 0, data: { data: [...], defaultModelConfigId: "..." } }
        // HTTP 拦截器返回: { data: [...], defaultModelConfigId: "..." }
        const responseData = response;
        
        // 处理可能的嵌套 data 字段
        let configList = [];
        let defaultModelConfigId = null;
        
        if (Array.isArray(responseData)) {
          // 如果 response 直接是数组
          configList = responseData;
        } else if (responseData && typeof responseData === 'object') {
          // 如果 response 是对象，尝试获取 data 字段
          configList = Array.isArray(responseData.data) ? responseData.data : [];
          defaultModelConfigId = responseData.defaultModelConfigId || responseData.default_model_config_id || null;
        }
        
    
        
        // 规范化字段
        const normalizedList = Array.isArray(configList)
          ? configList.map((item) => ({
              ...item,
              id: item.id,
              providerId: item.providerId || item.provider_id,
              providerName: item.providerName || item.provider_name,
              endpoint: item.endpoint,
              apiKey: item.apiKey || item.api_key,
              modelId: item.modelId || item.model_id,
              modelName: item.modelName || item.model_name,
              type: item.type,
              temperature: item.temperature,
              maxTokens: item.maxTokens || item.max_tokens,
              topP: item.topP || item.top_p,
              topK: item.topK || item.top_k,
              status: item.status,
            }))
          : [];

        this.setModelConfigList(normalizedList);
 
        // 设置默认模型
        if (defaultModelConfigId) {
          const defaultModel = normalizedList.find((item) => {
            const match = item.id === defaultModelConfigId;
            if (!match) {
              console.log('[ModelStore] ID 不匹配:', item.id, '!==', defaultModelConfigId);
            }
            return match;
          });
          console.log('[ModelStore] 查找默认模型:', defaultModelConfigId, '找到:', defaultModel ? defaultModel.modelName : '未找到');
          if (defaultModel) {
            this.setSelectedModel(defaultModel);
            console.log('[ModelStore] ✅ 已设置默认模型:', defaultModel.modelName, 'ID:', defaultModel.id);
          } else {
            console.warn('[ModelStore] ⚠️ 默认模型ID存在但未在列表中找到，使用第一个模型');
            if (normalizedList.length > 0) {
              this.setSelectedModel(normalizedList[0]);
            } else {
              this.setSelectedModel(null);
            }
          }
        } else if (normalizedList.length > 0) {
          // 如果没有默认模型，选择第一个
   
          this.setSelectedModel(normalizedList[0]);
        } else {
 
          this.setSelectedModel(null);
        }
      } catch (error) {
 
        this.setModelConfigList([]);
        this.setSelectedModel(null);
      }
    },
  },
});

