// 最佳实践配置示例
module.exports = {
  // 优化编译速度
  swcMinify: true, // 使用 SWC 压缩（更快）
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },
  // 优化开发体验
  onDemandEntries: {
    // 页面在内存中保持活动的时间（毫秒）
    maxInactiveAge: 25 * 1000,
    // 同时保持活动的页面数
    pagesBufferLength: 2,
  },
  experimental: {
    serverComponentsExternalPackages: ['@opendocsg/pdf2md', 'pdfjs-dist', '@hyzyla/pdfium'],
    esmExternals: 'loose',
    // 优化编译
    optimizeCss: true,
    // 减少服务器组件的外部包
    serverMinification: true,
  },
  /**
   * When NEXT_PUBLIC_DJANGO_API_BASE (or DJANGO_API_BASE) is set,
   * proxy all /api/* requests from the Next.js dev/SSR server to the
   * Django backend. This allows running the web frontend without
   * starting the Node.js API routes.
   *
   * Example:
   *   NEXT_PUBLIC_DJANGO_API_BASE=http://127.0.0.1:8000
   */
  async rewrites() {
    // 将前端的 /api/* 请求代理到 Django 后端
    // 注意：只代理 /api/* 路径，其他路径（如根路径 /）由 Next.js 处理
    const djangoApiBase = 'http://127.0.0.1:8000';
    const base = djangoApiBase.replace(/\/$/, '');

    return [
      {
        source: '/api/:path*',
        destination: `${base}/api/:path*`
      }
    ];
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.externals.push({
        unpdf: 'window.unpdf',
        'pdfjs-dist': 'window.pdfjsLib'
      });
    } else {
      config.externals.push('pdfjs-dist');
      config.externals.push('@hyzyla/pdfium');
    }
    return config;
  }
};
