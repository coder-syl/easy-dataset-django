/**
 * 对比 Node.js API 路由和 Django 视图
 * 检查功能是否一致
 */

const fs = require('fs');
const path = require('path');

// Node.js API 路由目录
const nodeApiDir = path.join(__dirname, '../app/api');
// Django 视图目录
const djangoViewsDir = path.join(__dirname, '../easy-dataset-django');

/**
 * 递归获取所有路由文件
 */
function getRouteFiles(dir, basePath = '') {
  const files = [];
  const items = fs.readdirSync(dir, { withFileTypes: true });

  for (const item of items) {
    const fullPath = path.join(dir, item.name);
    const relativePath = path.join(basePath, item.name);

    if (item.isDirectory()) {
      files.push(...getRouteFiles(fullPath, relativePath));
    } else if (item.name === 'route.js') {
      files.push(relativePath.replace(/\\/g, '/'));
    }
  }

  return files;
}

/**
 * 将路由路径转换为 API 路径
 */
function routeToApiPath(routePath) {
  // 移除 route.js，转换为 API 路径
  let apiPath = routePath.replace(/\/route\.js$/, '');
  
  // 处理动态路由 [param] -> <param>
  apiPath = apiPath.replace(/\[([^\]]+)\]/g, '<$1>');
  
  // 确保以 /api 开头
  if (!apiPath.startsWith('/api')) {
    apiPath = '/api' + (apiPath.startsWith('/') ? '' : '/') + apiPath;
  }
  
  // 确保路径格式正确
  if (!apiPath.startsWith('/')) {
    apiPath = '/' + apiPath;
  }
  
  return apiPath;
}

/**
 * 获取 Django URL 模式
 */
function getDjangoUrls() {
  const urlsFile = path.join(djangoViewsDir, 'easy_dataset/urls.py');
  if (!fs.existsSync(urlsFile)) {
    return [];
  }

  const content = fs.readFileSync(urlsFile, 'utf-8');
  const urlPatterns = [];
  
  // 简单的正则匹配 path() 调用
  const pathRegex = /path\(['"]([^'"]+)['"]/g;
  let match;
  while ((match = pathRegex.exec(content)) !== null) {
    urlPatterns.push(match[1]);
  }

  return urlPatterns;
}

// 主函数
function main() {
  console.log('🔍 开始对比 Node.js API 路由和 Django 视图...\n');

  // 获取 Node.js 路由
  const nodeRoutes = getRouteFiles(nodeApiDir);
  console.log(`📁 找到 ${nodeRoutes.length} 个 Node.js API 路由文件\n`);

  // 获取 Django URL 模式
  const djangoUrls = getDjangoUrls();
  console.log(`📁 找到 ${djangoUrls.length} 个 Django URL 模式\n`);

  // 转换为 API 路径
  const nodeApiPaths = nodeRoutes.map(routeToApiPath);
  
  console.log('📋 Node.js API 路由:');
  nodeApiPaths.forEach(path => console.log(`  - ${path}`));
  
  console.log('\n📋 Django URL 模式:');
  djangoUrls.forEach(url => console.log(`  - ${url}`));

  // 检查缺失的路由
  console.log('\n🔎 检查缺失的路由...\n');
  
  const missingInDjango = [];
  for (const nodePath of nodeApiPaths) {
    // 简化匹配逻辑
    const nodePathSimplified = nodePath.replace(/<[^>]+>/g, '*');
    const found = djangoUrls.some(djangoUrl => {
      const djangoUrlSimplified = djangoUrl.replace(/<[^>]+>/g, '*');
      return djangoUrlSimplified.includes(nodePathSimplified) || 
             nodePathSimplified.includes(djangoUrlSimplified);
    });
    
    if (!found) {
      missingInDjango.push(nodePath);
    }
  }

  if (missingInDjango.length > 0) {
    console.log('⚠️  以下 Node.js 路由在 Django 中可能缺失:');
    missingInDjango.forEach(path => console.log(`  - ${path}`));
  } else {
    console.log('✅ 所有 Node.js 路由在 Django 中都有对应实现');
  }

  console.log('\n✨ 对比完成！');
}

main();

