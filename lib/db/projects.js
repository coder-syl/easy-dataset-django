'use server';

import fs from 'fs';
import path from 'path';
import { getProjectRoot, readJsonFile } from './base';
import { DEFAULT_SETTINGS } from '@/constant/setting';
import { db } from '@/lib/db/index';
import { nanoid } from 'nanoid';

// 创建新项目
export async function createProject(projectData) {
  try {
    let projectId = nanoid(12);
    const projectRoot = await getProjectRoot();
    const projectDir = path.join(projectRoot, projectId);
    // 创建项目目录
    await fs.promises.mkdir(projectDir, { recursive: true });
    // 创建子目录
    await fs.promises.mkdir(path.join(projectDir, 'files'), { recursive: true }); // 原始文件
    return await db.projects.create({
      data: {
        id: projectId,
        name: projectData.name,
        description: projectData.description
      }
    });
  } catch (error) {
    console.error('Failed to create project in database');
    throw error;
  }
}

export async function isExistByName(name) {
  try {
    const count = await db.projects.count({
      where: {
        name: name
      }
    });
    return count > 0;
  } catch (error) {
    console.error('Failed to get project by name in database');
    throw error;
  }
}

// 获取所有项目
export async function getProjects() {
  try {
    return await db.projects.findMany({
      include: {
        _count: {
          select: {
            Datasets: true,
            Questions: true
          }
        }
      },
      orderBy: {
        createAt: 'desc'
      }
    });
  } catch (error) {
    console.error('Failed to get projects in database');
    throw error;
  }
}

// 获取项目详情
export async function getProject(projectId) {
  try {
    return await db.projects.findUnique({ where: { id: projectId } });
  } catch (error) {
    console.error('Failed to get project by id in database');
    throw error;
  }
}

// 更新项目配置
export async function updateProject(projectId, projectData) {
  const startTime = Date.now();
  
  try {
    console.log('[DB] 🔄 updateProject called');
    console.log('[DB] 📋 Parameters:', { projectId, projectData: JSON.stringify(projectData, null, 2) });
    
    // 删除 projectId（如果存在）
    const originalProjectId = projectData.projectId;
    delete projectData.projectId;
    if (originalProjectId) {
      console.log('[DB] 🗑️ Removed projectId from update data');
    }
    
    // 记录数据库更新操作
    if (projectData.defaultModelConfigId) {
      console.log(`[DB] 🎯 Updating project ${projectId} defaultModelConfigId to:`, projectData.defaultModelConfigId);
    }
    
    console.log('[DB] 💾 Executing Prisma update query...');
    console.log('[DB] 📝 Update data:', JSON.stringify(projectData, null, 2));
    
    const result = await db.projects.update({
      where: { id: projectId },
      data: { ...projectData }
    });
    
    const duration = Date.now() - startTime;
    console.log(`[DB] ✅ Database update completed in ${duration}ms`);
    console.log('[DB] 📊 Updated record:', JSON.stringify(result, null, 2));
    
    // 确认更新结果
    if (projectData.defaultModelConfigId) {
      console.log(`[DB] ✅✅ Project ${projectId} updated successfully`);
      console.log(`[DB] ✅✅ New defaultModelConfigId in database:`, result.defaultModelConfigId);
      
      if (result.defaultModelConfigId === projectData.defaultModelConfigId) {
        console.log(`[DB] ✅✅✅ VERIFIED: defaultModelConfigId saved correctly!`);
      } else {
        console.error(`[DB] ❌❌❌ MISMATCH: Expected ${projectData.defaultModelConfigId}, got ${result.defaultModelConfigId}`);
      }
    }
    
    return result;
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error('[DB] ❌❌❌ ERROR in updateProject:', error);
    console.error('[DB] Error name:', error.name);
    console.error('[DB] Error message:', error.message);
    console.error('[DB] Error stack:', error.stack);
    console.error(`[DB] ⏱️ Operation failed after ${duration}ms`);
    throw error;
  }
}

// 删除项目
export async function deleteProject(projectId) {
  try {
    const projectRoot = await getProjectRoot();
    const projectPath = path.join(projectRoot, projectId);
    await db.projects.delete({ where: { id: projectId } });
    if (fs.existsSync(projectPath)) {
      await fs.promises.rm(projectPath, { recursive: true });
    }
    return true;
  } catch (error) {
    return false;
  }
}

// 获取任务配置
export async function getTaskConfig(projectId) {
  const projectRoot = await getProjectRoot();
  const projectPath = path.join(projectRoot, projectId);
  const taskConfigPath = path.join(projectPath, 'task-config.json');
  const taskData = await readJsonFile(taskConfigPath);
  if (!taskData) {
    return DEFAULT_SETTINGS;
  }
  return taskData;
}
