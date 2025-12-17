// 获取项目详情
import { deleteProject, getProject, updateProject, getTaskConfig } from '@/lib/db/projects';

export async function GET(request, { params }) {
  try {
    const { projectId } = params;
    const project = await getProject(projectId);
    const taskConfig = await getTaskConfig(projectId);
    if (!project) {
      return Response.json({ error: '项目不存在' }, { status: 404 });
    }
    return Response.json({ ...project, taskConfig });
  } catch (error) {
    console.error('获取项目详情出错:', String(error));
    return Response.json({ error: String(error) }, { status: 500 });
  }
}

// 更新项目
export async function PUT(request, { params }) {
  const startTime = Date.now();
  
  try {
    console.log('='.repeat(80));
    console.log(`[API] 🚀 PUT /api/projects/[projectId] - Request received at ${new Date().toISOString()}`);
    
    const { projectId } = params;
    console.log(`[API] 📋 Project ID from params:`, projectId);
    
    if (!projectId) {
      console.error('[API] ❌ ERROR: projectId is missing from params');
      return Response.json({ error: '项目ID不能为空' }, { status: 400 });
    }

    // 解析请求体
    let projectData;
    try {
      projectData = await request.json();
      console.log(`[API] 📦 Request body parsed successfully:`, JSON.stringify(projectData, null, 2));
    } catch (parseError) {
      console.error('[API] ❌ ERROR: Failed to parse request body:', parseError);
      return Response.json({ error: '请求体格式错误' }, { status: 400 });
    }

    // 记录更新请求
    console.log(`[API] 🔄 Updating project ${projectId} with data:`, projectData);
    console.log(`[API] 📝 Fields to update:`, Object.keys(projectData));

    // 验证：如果传了 name 字段，则 name 不能为空
    if (projectData.hasOwnProperty('name') && !projectData.name) {
      console.warn('[API] ⚠️ Validation failed: name is empty');
      return Response.json({ error: '项目名称不能为空' }, { status: 400 });
    }

    // 验证：至少要有要更新的字段
    const validFields = Object.keys(projectData).filter(key => key !== 'projectId');
    if (validFields.length === 0) {
      console.warn('[API] ⚠️ Validation failed: No valid fields to update');
      return Response.json({ error: '没有要更新的字段' }, { status: 400 });
    }

    console.log(`[API] ✅ Validation passed. Valid fields:`, validFields);

    // 特别关注 default_model_config_id
    if (projectData.default_model_config_id) {
      console.log(`[API] 🎯 Updating default_model_config_id:`, projectData.default_model_config_id);
    }

    console.log(`[API] 💾 Calling updateProject function...`);
    const updatedProject = await updateProject(projectId, projectData);

    if (!updatedProject) {
      console.error(`[API] ❌ ERROR: Project ${projectId} not found in database`);
      return Response.json({ error: '项目不存在' }, { status: 404 });
    }

    console.log(`[API] ✅ Project updated successfully`);
    console.log(`[API] 📊 Updated project data:`, JSON.stringify(updatedProject, null, 2));

    // 记录更新成功
    if (projectData.default_model_config_id) {
      console.log(`[API] ✅✅ Successfully updated default_model_config_id to:`, projectData.default_model_config_id);
      console.log(`[API] ✅✅ Confirmed in database:`, updatedProject.defaultModelConfigId);
      
      if (updatedProject.defaultModelConfigId === projectData.default_model_config_id) {
        console.log(`[API] ✅✅✅ VERIFIED: default_model_config_id matches in database!`);
      } else {
        console.error(`[API] ❌❌❌ MISMATCH: Expected ${projectData.default_model_config_id}, got ${updatedProject.defaultModelConfigId}`);
      }
    }

    const duration = Date.now() - startTime;
    console.log(`[API] ⏱️ Request completed in ${duration}ms`);
    console.log('='.repeat(80));

    return Response.json(updatedProject);
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error('[API] ❌❌❌ ERROR in PUT /api/projects/[projectId]:', error);
    console.error('[API] Error stack:', error.stack);
    console.error(`[API] ⏱️ Request failed after ${duration}ms`);
    console.log('='.repeat(80));
    return Response.json({ error: String(error) }, { status: 500 });
  }
}

// 删除项目
export async function DELETE(request, { params }) {
  try {
    const { projectId } = params;
    const success = await deleteProject(projectId);

    if (!success) {
      return Response.json({ error: '项目不存在' }, { status: 404 });
    }

    return Response.json({ success: true });
  } catch (error) {
    console.error('删除项目出错:', error);
    return Response.json({ error: error.message }, { status: 500 });
  }
}
