import { ref, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useModelStore } from '../stores/model';
import { sendChatMessage, sendChatMessageStream } from '../api/playground';

export function useModelPlayground(projectId, defaultModelId = null) {
  const route = useRoute();
  const modelStore = useModelStore();

  const selectedModels = ref(defaultModelId ? [defaultModelId] : []);
  const loading = ref({});
  const userInput = ref('');
  const conversations = ref({});
  const error = ref(null);
  const outputMode = ref('normal'); // 'normal' 或 'streaming'
  const uploadedImage = ref(null);

  const availableModels = computed(() => modelStore.modelConfigList);

  // 从 URL 参数获取 modelId
  if (route.query.modelId && !defaultModelId) {
    selectedModels.value = [route.query.modelId];
  }

  // 初始化会话状态
  watch(
    selectedModels,
    (newModels) => {
      if (newModels.length > 0) {
        const initialConversations = {};
        newModels.forEach((modelId) => {
          if (!conversations.value[modelId]) {
            initialConversations[modelId] = [];
          }
        });
        conversations.value = { ...conversations.value, ...initialConversations };
      }
    },
    { immediate: true },
  );

  // 处理模型选择
  const handleModelSelection = (value) => {
    const selectedValues = Array.isArray(value) ? value : [value];
    // 限制最多选择 3 个模型
    selectedModels.value = selectedValues.slice(0, 3);
  };

  // 处理用户输入
  const handleInputChange = (value) => {
    userInput.value = value;
  };

  // 处理图片上传
  const handleImageUpload = (file) => {
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        uploadedImage.value = reader.result;
      };
      reader.readAsDataURL(file);
    }
  };

  // 删除已上传的图片
  const handleRemoveImage = () => {
    uploadedImage.value = null;
  };

  // 处理输出模式切换
  const handleOutputModeChange = (value) => {
    outputMode.value = value;
  };

  // 发送消息给所有选中的模型
  const handleSendMessage = async () => {
    if (!userInput.value.trim() || Object.values(loading.value).some((v) => v) || selectedModels.value.length === 0) {
      return;
    }

    const input = userInput.value.trim();
    userInput.value = '';
    const image = uploadedImage.value;
    uploadedImage.value = null;

    // 更新所有选中模型的对话
    const updatedConversations = { ...conversations.value };
    selectedModels.value.forEach((modelId) => {
      if (!updatedConversations[modelId]) {
        updatedConversations[modelId] = [];
      }
      const model = availableModels.value.find((m) => m.id === modelId);
      const isVisionModel = model && model.type === 'vision';

      if (isVisionModel && image) {
        updatedConversations[modelId].push({
          role: 'user',
          content: [
            { type: 'text', text: input || '请描述这个图片' },
            { type: 'image_url', image_url: { url: image } },
          ],
        });
      } else {
        updatedConversations[modelId].push({
          role: 'user',
          content: input,
        });
      }
    });

    conversations.value = updatedConversations;

    // 为每个模型设置独立的加载状态
    const updatedLoading = {};
    selectedModels.value.forEach((modelId) => {
      updatedLoading[modelId] = true;
    });
    loading.value = updatedLoading;

    // 为每个模型单独发送请求
    selectedModels.value.forEach(async (modelId) => {
      const model = availableModels.value.find((m) => m.id === modelId);
      if (!model) {
        const modelConversation = [...(updatedConversations[modelId] || [])];
        conversations.value = {
          ...conversations.value,
          [modelId]: [...modelConversation, { role: 'error', content: '模型配置不存在' }],
        };
        loading.value = { ...loading.value, [modelId]: false };
        return;
      }

      try {
        const isVisionModel = model.type === 'vision';
        let requestMessages = [...updatedConversations[modelId]];

        if (isVisionModel && image && requestMessages.length > 0) {
          const lastUserMsgIndex = requestMessages.length - 1;
          requestMessages[lastUserMsgIndex] = {
            role: 'user',
            content: [
              { type: 'text', text: input || '请描述这个图片' },
              { type: 'image_url', image_url: { url: image } },
            ],
          };
        }

        if (outputMode.value === 'streaming') {
          // 流式输出处理
          conversations.value = {
            ...conversations.value,
            [modelId]: [
              ...(conversations.value[modelId] || []),
              {
                role: 'assistant',
                content: '',
                isStreaming: true,
                thinking: '',
                showThinking: true,
              },
            ],
          };

          let isInThinking = false;
          let currentThinking = '';
          let currentContent = '';
          let accumulatedChunk = '';

          await sendChatMessageStream(
            projectId,
            {
              model: model,
              messages: requestMessages,
            },
            (chunk) => {
              accumulatedChunk += chunk;

              // 处理标签
              const thinkStartTag = '<think>';
              const thinkEndTag = '</think>';

              let processed = '';
              let i = 0;

              while (i < accumulatedChunk.length) {
                // 检测开始标签
                if (i + thinkStartTag.length <= accumulatedChunk.length && 
                    accumulatedChunk.substring(i, i + thinkStartTag.length) === thinkStartTag) {
                  isInThinking = true;
                  i += thinkStartTag.length;
                  continue;
                }

                // 检测结束标签
                if (i + thinkEndTag.length <= accumulatedChunk.length && 
                    accumulatedChunk.substring(i, i + thinkEndTag.length) === thinkEndTag) {
                  isInThinking = false;
                  i += thinkEndTag.length;
                  continue;
                }

                // 根据状态添加到对应内容
                const char = accumulatedChunk[i];
                if (isInThinking) {
                  currentThinking += char;
                } else {
                  currentContent += char;
                }
                i++;
              }

              // 更新对话
              conversations.value = {
                ...conversations.value,
                [modelId]: conversations.value[modelId].map((msg, idx) => {
                  if (idx === conversations.value[modelId].length - 1 && msg.role === 'assistant') {
                    return {
                      ...msg,
                      content: currentContent,
                      thinking: currentThinking,
                      showThinking: currentThinking.length > 0,
                    };
                  }
                  return msg;
                }),
              };
            },
          );

          // 完成流式传输
          conversations.value = {
            ...conversations.value,
            [modelId]: conversations.value[modelId].map((msg, idx) => {
              if (idx === conversations.value[modelId].length - 1 && msg.role === 'assistant') {
                return {
                  ...msg,
                  isStreaming: false,
                };
              }
              return msg;
            }),
          };
        } else {
          // 普通输出处理
          const response = await sendChatMessage(projectId, {
            model: {
              ...model,
              extra_body: { enable_thinking: true },
            },
            messages: requestMessages,
          });

          let thinking = '';
          let content = response?.response ?? response?.data?.response ?? '';

          if (content && content.includes('<think>')) {
            const thinkParts = content.split(/<think>(.*?)<\/redacted_reasoning>/s);
            if (thinkParts.length >= 3) {
              thinking = thinkParts[1] || '';
              content = thinkParts.filter((_, i) => i % 2 === 0).join('');
            }
          }

          conversations.value = {
            ...conversations.value,
            [modelId]: [
              ...(conversations.value[modelId] || []),
              {
                role: 'assistant',
                content: content,
                thinking: thinking,
                showThinking: thinking ? true : false,
              },
            ],
          };
        }
      } catch (err) {
        console.error(`请求模型 ${model.modelName} 失败:`, err);
        conversations.value = {
          ...conversations.value,
          [modelId]: [
            ...(conversations.value[modelId] || []),
            { role: 'error', content: `错误: ${err.message || '请求失败'}` },
          ],
        };
      } finally {
        loading.value = { ...loading.value, [modelId]: false };
      }
    });
  };

  // 清空所有对话
  const handleClearConversations = () => {
    const clearedConversations = {};
    selectedModels.value.forEach((modelId) => {
      clearedConversations[modelId] = [];
    });
    conversations.value = clearedConversations;
    loading.value = {};
  };

  // 获取模型名称
  const getModelName = (modelId) => {
    const model = availableModels.value.find((m) => m.id === modelId);
    return model ? `${model.providerName}: ${model.modelName}` : modelId;
  };

  return {
    availableModels,
    selectedModels,
    loading,
    userInput,
    conversations,
    error,
    outputMode,
    uploadedImage,
    handleModelSelection,
    handleInputChange,
    handleImageUpload,
    handleRemoveImage,
    handleSendMessage,
    handleClearConversations,
    handleOutputModeChange,
    getModelName,
  };
}

