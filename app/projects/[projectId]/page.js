'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { toast } from 'sonner';
import { useSetAtom } from 'jotai/index';
import { modelConfigListAtom, selectedModelInfoAtom } from '@/lib/store';

export default function ProjectPage({ params }) {
  const router = useRouter();
  const setConfigList = useSetAtom(modelConfigListAtom);
  const setSelectedModelInfo = useSetAtom(selectedModelInfoAtom);
  const { projectId } = params;

  // 默认重定向到文本分割页面
  useEffect(() => {
    getModelConfigList(projectId);
    router.push(`/projects/${projectId}/text-split`);
  }, [projectId, router]);

  const getModelConfigList = projectId => {
    axios
      .get(`/api/projects/${projectId}/model-config`)
      .then(response => {
        // Django API 返回格式: {code: 200, message: "Success", data: {data: [...], defaultModelConfigId: ...}}
        // 提取嵌套的 data 字段
        const responseData = response.data?.data || response.data;
        const modelConfigList = responseData?.data || responseData || [];
        const defaultModelConfigId = responseData?.defaultModelConfigId || response.data?.defaultModelConfigId;
        
        setConfigList(Array.isArray(modelConfigList) ? modelConfigList : []);

        if (defaultModelConfigId) {
          const defaultModel = modelConfigList.find(item => item.id === defaultModelConfigId);
          setSelectedModelInfo(defaultModel || null);
        } else {
          setSelectedModelInfo(null);
        }
      })
      .catch(error => {
        toast.error('get model list error');
      });
  };

  return null;
}
