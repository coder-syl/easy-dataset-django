import { NextResponse } from 'next/server';

/**
 * Next.js 中间件
 * 当使用 Django 后端时，拦截 /api/* 请求并转发到 Django
 * 
 * 注意：
 * 1. 中间件的优先级高于 API 路由，所以可以拦截请求
 * 2. 前端代码应该统一不带尾部斜杠（如：/api/projects/123/model-config）
 * 3. 中间件会自动为所有非静态文件的 API 请求添加尾部斜杠
 * 4. 这样 Django 就不需要适配前端的请求格式，统一使用尾部斜杠的路由
 */
export async function middleware(request) {
  // Django 后端地址
  const djangoApiBase = 'http://127.0.0.1:8000';
  
  // 只处理 /api/* 路径的请求
  if (request.nextUrl.pathname.startsWith('/api/')) {
   

    try {
      const url = request.nextUrl.clone();
      let pathname = url.pathname;
      
      // 检测是否为静态文件（包含文件扩展名，如 .pdf, .jpg 等）
      const isStaticFile = pathname.includes('.') && pathname.match(/\.[a-zA-Z0-9]+$/);
      
      // Django 路由需要尾部斜杠，但静态文件不需要
      // 前端代码统一不带尾部斜杠，中间件负责自动添加
      if (!pathname.endsWith('/') && !isStaticFile) {
        pathname = pathname + '/';
      }
      
      const djangoUrl = new URL(pathname + url.search, djangoApiBase);
      
      // 调试日志（开发环境）
      if (process.env.NODE_ENV === 'development') {
        console.log(`[Middleware] ${request.method} ${url.pathname} -> ${djangoUrl.toString()}`);
        console.log(`[Middleware] Original pathname: "${url.pathname}", Modified pathname: "${pathname}"`);
      }
      
      // 准备请求头
      const headers = new Headers();
      request.headers.forEach((value, key) => {
        // 跳过一些可能导致问题的头部
        if (key.toLowerCase() !== 'host' && key.toLowerCase() !== 'connection') {
          headers.set(key, value);
        }
      });
      
      // 获取请求体（如果有）
      let body = null;
      if (request.method !== 'GET' && request.method !== 'HEAD') {
        try {
          const clonedRequest = request.clone();
          body = await clonedRequest.text();
        } catch (e) {
          // 如果无法读取 body，继续使用原始请求
          body = request.body;
        }
      }

      // 如果没有 body，删除 content-length，避免 UND_ERR_REQ_CONTENT_LENGTH_MISMATCH
      if (!body && headers.has('content-length')) {
        headers.delete('content-length');
      }
      
      // 转发请求到 Django 后端
      const response = await fetch(djangoUrl.toString(), {
        method: request.method,
        headers: headers,
        body: body || undefined, // 确保无 body 时不发送 content-length
      });
      
      // 读取响应数据
      const responseData = await response.text();
      
      // 调试日志：记录 404 错误
      if (process.env.NODE_ENV === 'development' && response.status === 404) {
        console.error(`[Middleware] ⚠️  404 Error Detected:`);
        console.error(`  Original request: ${request.method} ${url.pathname}`);
        console.error(`  Forwarded to: ${djangoUrl.toString()}`);
        console.error(`  Response status: ${response.status}`);
        console.error(`  Response preview: ${responseData.substring(0, 300)}`);
        console.error(`  Please check:`);
        console.error(`  1. Is Django running on ${djangoApiBase}?`);
        console.error(`  2. Does the route exist in Django urls.py?`);
        console.error(`  3. Try accessing directly: ${djangoUrl.toString()}`);
      }
      
      // 创建响应头
      const responseHeaders = new Headers();
      response.headers.forEach((value, key) => {
        // 跳过一些可能导致问题的头部
        if (key.toLowerCase() !== 'connection' && key.toLowerCase() !== 'transfer-encoding') {
          responseHeaders.set(key, value);
        }
      });
      
      // 设置 CORS 头部（如果需要）
      responseHeaders.set('Access-Control-Allow-Origin', '*');
      responseHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      responseHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      
      // 返回响应
      return new NextResponse(responseData, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
      });
    } catch (error) {
      console.error('Django API 代理错误:', error);
      return NextResponse.json(
        { 
          error: '无法连接到 Django 后端', 
          details: error.message,
          hint: '请确保 Django 后端运行在 http://127.0.0.1:8000'
        },
        { status: 502 }
      );
    }
  }
  
  // 非 API 请求，继续正常处理
  return NextResponse.next();
}

// 配置中间件匹配的路径
export const config = {
  matcher: '/api/:path*',
};

