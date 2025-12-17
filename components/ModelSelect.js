'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { FormControl, Select, MenuItem, useTheme, ListSubheader, Box, IconButton, Tooltip } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useAtom, useAtomValue } from 'jotai/index';
import { modelConfigListAtom, selectedModelInfoAtom } from '@/lib/store';
import axios from 'axios';
import { toast } from 'sonner';
import SmartToyIcon from '@mui/icons-material/SmartToy';

// 获取模型对应的图标路径
const getModelIcon = modelName => {
  if (!modelName) return '/imgs/models/default.svg';

  // 将模型名称转换为小写以便比较
  const lowerModelName = modelName.toLowerCase();

  // 定义已知模型前缀映射
  const modelPrefixes = [
    { prefix: 'doubao', icon: 'doubao.svg' },
    { prefix: 'qwen', icon: 'qwen.svg' },
    { prefix: 'gpt', icon: 'gpt.svg' },
    { prefix: 'gemini', icon: 'gemini.svg' },
    { prefix: 'claude', icon: 'claude.svg' },
    { prefix: 'llama', icon: 'llama.svg' },
    { prefix: 'mistral', icon: 'mistral.svg' },
    { prefix: 'yi', icon: 'yi.svg' },
    { prefix: 'deepseek', icon: 'deepseek.svg' },
    { prefix: 'chatglm', icon: 'chatglm.svg' },
    { prefix: 'wenxin', icon: 'wenxin.svg' },
    { prefix: 'glm', icon: 'glm.svg' },
    { prefix: 'hunyuan', icon: 'hunyuan.svg' }

    // 添加更多模型前缀映射...
  ];

  // 查找匹配的模型前缀
  const matchedPrefix = modelPrefixes.find(({ prefix }) => lowerModelName.includes(prefix));

  // 返回对应的图标路径，如果没有匹配则返回默认图标
  return `/imgs/models/${matchedPrefix ? matchedPrefix.icon : 'default.svg'}`;
};

export default function ModelSelect({
  size = 'small',
  minWidth = 50,
  projectId,
  minHeight = 36,
  required = false,
  onError
}) {
  const theme = useTheme();
  const { t } = useTranslation();
  const modelsRaw = useAtomValue(modelConfigListAtom);
  // 确保 models 始终是数组
  const models = Array.isArray(modelsRaw) ? modelsRaw : [];
  const [selectedModelInfo, setSelectedModelInfo] = useAtom(selectedModelInfoAtom);
  // 确保始终使用字符串值初始化 selectedModel，避免从非受控变为受控
  const [selectedModel, setSelectedModel] = useState(() => {
    if (selectedModelInfo && selectedModelInfo.id) {
      return selectedModelInfo.id;
    } else if (models && models.length > 0 && models[0]?.id) {
      return models[0].id;
    }
    return '';
  });
  const [error, setError] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  // 调试：检查 projectId 是否正确传递
  useEffect(() => {
    console.log('[ModelSelect] Component mounted/updated', { projectId, modelsCount: models.length });
    if (!projectId) {
      console.warn('[ModelSelect] ⚠️ WARNING: projectId is missing or undefined!');
    }
  }, [projectId, models.length]);
  const handleModelChange = event => {
    console.log('[ModelSelect] handleModelChange called', { event, projectId });
    
    if (!event || !event.target) {
      console.warn('[ModelSelect] handleModelChange: Invalid event');
      return;
    }
    
    const newModelId = event.target.value;
    console.log('[ModelSelect] New model selected:', newModelId);

    // 清除错误状态
    if (error) {
      setError(false);
      if (onError) onError(false);
    }

    // 找到选中的模型对象
    const selectedModelObj = models.find(model => model.id === newModelId);
    console.log('[ModelSelect] Selected model object:', selectedModelObj);
    
    if (selectedModelObj) {
      setSelectedModel(newModelId);
      // 将完整的模型信息存储到 localStorage
      setSelectedModelInfo(selectedModelObj);
      console.log('[ModelSelect] Calling updateDefaultModel with:', { projectId, modelId: newModelId });
      updateDefaultModel(newModelId);
    } else {
      console.warn('[ModelSelect] Model object not found for ID:', newModelId);
      setSelectedModelInfo({
        id: newModelId
      });
    }

    // 选择模型后，延迟收回到图标状态
    setTimeout(() => {
      setIsHovered(false);
      setIsOpen(false);
    }, 200);
  };

  const updateDefaultModel = async id => {
    console.log('[ModelSelect] updateDefaultModel called', { projectId, modelId: id });
    
    // 检查 projectId 是否存在
    if (!projectId) {
      console.error('[ModelSelect] ❌ Project ID is missing, cannot update default model config');
      console.error('[ModelSelect] Current projectId value:', projectId);
      toast.error('项目ID缺失，无法更新默认模型配置');
      return;
    }

    // 检查模型 ID 是否存在
    if (!id) {
      console.error('[ModelSelect] ❌ Model ID is missing, cannot update default model config');
      console.error('[ModelSelect] Current modelId value:', id);
      toast.error('模型ID缺失，无法更新默认模型配置');
      return;
    }

    try {
      const url = `/api/projects/${projectId}`;
      const payload = { default_model_config_id: id };
      
      console.log('[ModelSelect] 📤 Sending PUT request:', { url, payload });
      console.log('[ModelSelect] Full URL:', `${window.location.origin}${url}`);
      
      const res = await axios.put(url, payload);
      
      console.log('[ModelSelect] 📥 Received response:', { 
        status: res.status, 
        statusText: res.statusText,
        data: res.data 
      });
      
      if (res.status === 200) {
        console.log('[ModelSelect] ✅ Default model config updated successfully:', id);
        console.log('[ModelSelect] Response data:', res.data);
        
        // 处理 Django 返回格式：{code, message, data: {...}}
        const responseData = res.data?.data || res.data;
        const updatedValue = responseData?.default_model_config_id;
        
        // 验证返回的数据中是否包含更新后的 default_model_config_id
        if (updatedValue === id) {
          console.log('[ModelSelect] ✅✅ Confirmed: default_model_config_id saved to database');
          toast.success('默认模型配置已更新');
        } else {
          console.warn('[ModelSelect] ⚠️ Warning: Response does not match expected value');
          console.warn('[ModelSelect] Expected:', id, 'Got:', updatedValue);
        }
      } else {
        console.warn('[ModelSelect] ⚠️ Update response status:', res.status);
      }
    } catch (error) {
      console.error('[ModelSelect] ❌ Failed to update default model config:', error);
      console.error('[ModelSelect] Error details:', {
        message: error.message,
        response: error.response,
        request: error.request,
        config: error.config
      });
      
      // 显示错误提示，让用户知道更新失败
      const errorMessage = error.response?.data?.error || error.message || '更新默认模型配置失败';
      console.error('[ModelSelect] Error message:', errorMessage);
      
      // 显示错误提示
      toast.error(`更新默认模型配置失败: ${errorMessage}`);
    }
  };

  // 检查是否选择了模型
  const validateModel = () => {
    if (required && (!selectedModel || selectedModel === '')) {
      setError(true);
      if (onError) onError(true);
      return false;
    }
    return true;
  };

  useEffect(() => {
    if (selectedModelInfo && selectedModelInfo.id) {
      setSelectedModel(selectedModelInfo.id);
    } else {
      setSelectedModel('');
    }
  }, [selectedModelInfo]);

  // 初始检查
  useEffect(() => {
    if (required) {
      validateModel();
    }
  }, [required]);

  // 获取当前选中模型的显示内容
  const renderSelectedValue = value => {
    const selectedModelObj = models.find(model => model.id === value);
    if (!selectedModelObj) return null;

    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box
          component="img"
          src={getModelIcon(selectedModelObj.modelName)}
          alt={selectedModelObj.modelName}
          sx={{
            width: 20,
            height: 20,
            objectFit: 'contain',
            flexShrink: 0,
            background: '#ffffffc9',
            borderRadius: '50%',
            marginBottom: '-2px'
          }}
          onError={e => {
            e.target.src = '/imgs/models/default.svg';
          }}
        />
        {selectedModelObj.modelName}
      </Box>
    );
  };

  // 获取当前选中模型的图标
  const currentModelIcon = useMemo(() => {
    const selectedModelObj = models.find(model => model.id === selectedModel);
    return selectedModelObj ? getModelIcon(selectedModelObj.modelName) : null;
  }, [selectedModel, models]);

  // 判断是否应该显示完整的 Select
  const shouldShowFullSelect = isHovered || isOpen;

  return (
    <Box
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => {
        setIsHovered(false);
        // 确保菜单关闭后才能收回
        if (!isOpen) {
          setIsOpen(false);
        }
      }}
      sx={{
        position: 'relative',
        display: 'flex',
        alignItems: 'center'
      }}
    >
      {/* 默认显示的图标按钮 */}
      {!shouldShowFullSelect && (
        <Tooltip
          title={
            selectedModel
              ? models.find(m => m.id === selectedModel)?.modelName
              : t('playground.selectModelFirst', '请先选择模型')
          }
          placement="bottom"
        >
          <IconButton
            size="medium"
            sx={{
              bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(255, 255, 255, 0.69)',
              color: theme.palette.mode === 'dark' ? 'inherit' : 'white',
              borderRadius: 1.5,
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              '&:hover': {
                bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(255, 255, 255, 0.35)'
              },
              ...(error && {
                animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                '@keyframes pulse': {
                  '0%, 100%': {
                    opacity: 1
                  },
                  '50%': {
                    opacity: 0.5
                  }
                }
              })
            }}
          >
            {currentModelIcon ? (
              <Box
                component="img"
                src={currentModelIcon}
                alt="model icon"
                sx={{
                  width: 20,
                  height: 20,
                  objectFit: 'contain'
                }}
                onError={e => {
                  e.target.src = '/imgs/models/default.svg';
                }}
              />
            ) : (
              <SmartToyIcon
                fontSize="small"
                color="red"
                sx={{
                  color: error ? 'red' : 'red'
                }}
              />
            )}
          </IconButton>
        </Tooltip>
      )}

      {/* 悬浮时显示的完整 Select */}
      <FormControl
        size={size}
        sx={{
          minWidth: shouldShowFullSelect ? 200 : 0,
          minHeight,
          opacity: shouldShowFullSelect ? 1 : 0,
          width: shouldShowFullSelect ? 'auto' : 0,
          overflow: 'hidden',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          position: shouldShowFullSelect ? 'relative' : 'absolute',
          pointerEvents: shouldShowFullSelect ? 'auto' : 'none'
        }}
        error={error}
      >
        <Select
          value={selectedModel}
          onChange={handleModelChange}
          displayEmpty
          variant="outlined"
          onBlur={validateModel}
          renderValue={renderSelectedValue}
          onOpen={() => setIsOpen(true)}
          onClose={() => setIsOpen(false)}
          sx={{
            bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(255, 255, 255, 0.2)',
            color: theme.palette.mode === 'dark' ? 'inherit' : 'white',
            borderRadius: 1.5,
            '& .MuiSelect-select': {
              display: 'flex',
              alignItems: 'center',
              padding: '6px 32px 6px 12px'
            },
            '& .MuiSelect-icon': {
              color: theme.palette.mode === 'dark' ? 'inherit' : 'white',
              right: '8px'
            },
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: 'transparent'
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: 'transparent'
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: theme.palette.mode === 'dark' ? 'primary.main' : 'rgba(255, 255, 255, 0.5)'
            },
            minHeight: '36px'
          }}
          MenuProps={{
            PaperProps: {
              elevation: 2,
              sx: {
                mt: 1,
                borderRadius: 2,
                '& .MuiMenuItem-root': {
                  minHeight: '30px'
                }
              }
            }
          }}
        >
          <MenuItem value="" disabled>
            {error ? t('models.pleaseSelectModel') : t('playground.selectModelFirst')}
          </MenuItem>
          {(() => {
            // 按 provider 分组
            const filteredModels = models.filter(m => {
              if (m.providerId?.toLowerCase() === 'ollama') {
                return m.modelName && m.endpoint;
              } else {
                return m.modelName && m.endpoint && m.apiKey;
              }
            });

            // 获取所有 provider
            const providers = [...new Set(filteredModels.map(m => m.providerName || 'Other'))];

            return providers.map(provider => {
              const providerModels = filteredModels.filter(m => (m.providerName || 'Other') === provider);
              return [
                <ListSubheader
                  key={`header-${provider}`}
                  sx={{
                    pl: 2,
                    color: theme.palette.text.secondary,
                    fontWeight: 500,
                    mt: 1,
                    mb: 0.5
                  }}
                >
                  {provider || 'Other'}
                </ListSubheader>,
                ...providerModels.map(model => (
                  <MenuItem
                    key={model.id}
                    value={model.id}
                    sx={{
                      pl: 3,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 2,
                      minHeight: '30px',
                      '&.Mui-selected': {
                        bgcolor: theme.palette.action.selected,
                        '&:hover': {
                          bgcolor: theme.palette.action.selected
                        }
                      }
                    }}
                  >
                    <Box
                      component="img"
                      src={getModelIcon(model.modelName)}
                      alt={model.modelName}
                      sx={{
                        width: 20,
                        height: 20,
                        objectFit: 'contain',
                        flexShrink: 0
                      }}
                      onError={e => {
                        e.target.src = '/imgs/models/default.svg';
                      }}
                    />
                    <Box component="span" sx={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {model.modelName}
                    </Box>
                  </MenuItem>
                ))
              ];
            });
          })()}
        </Select>
      </FormControl>
    </Box>
  );
}
