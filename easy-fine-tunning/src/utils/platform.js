export function getPlatformNameFromLink(link) {
  if (!link || typeof link !== 'string') return '';
  const l = link.toLowerCase();
  if (l.includes('huggingface')) return 'HuggingFace';
  if (l.includes('kaggle')) return 'Kaggle';
  if (l.includes('github')) return 'GitHub';
  if (l.includes('registry.opendata.aws') || l.includes('aws.')) return 'AWS';
  if (l.includes('opendatalab')) return 'OpenDataLab';
  if (l.includes('datasetsearch.research.google') || l.includes('google')) return 'Google';
  if (l.includes('modelscope')) return 'ModelScope';
  if (l.includes('baai')) return 'BAAI';
  if (l.includes('aistudio') || l.includes('paddle')) return 'Baidu AI Studio';
  try {
    const url = new URL(link);
    const host = url.hostname.replace('www.', '');
    // capitalise host as fallback
    return host.split('.').slice(-2)[0].replace(/(^\w)/, (m) => m.toUpperCase());
  } catch (e) {
    return link;
  }
}

// 返回在前端 public 下可访问的平台图片路径（如 /imgs/huggingface.png）
export function getPlatformImageFromLink(link) {
  if (!link || typeof link !== 'string') return '';
  const l = link.toLowerCase();
  if (l.includes('huggingface')) return '/imgs/huggingface.png';
  if (l.includes('kaggle')) return '/imgs/kaggle.png';
  if (l.includes('github')) return '/imgs/github.png';
  if (l.includes('registry.opendata.aws') || l.includes('aws.')) return '/imgs/aws.png';
  if (l.includes('opendatalab')) return '/imgs/opendatalab.png';
  if (l.includes('datasetsearch.research.google') || l.includes('google')) return '/imgs/google.png';
  if (l.includes('modelscope')) return '/imgs/modelscope.png';
  if (l.includes('luge') || l.includes('lluge') || l.includes('lluga')) return '/imgs/lluga.png';
  if (l.includes('baai')) return '/imgs/baai.png';
  if (l.includes('aistudio') || l.includes('paddle')) return '/imgs/baidu.png';
  try {
    const url = new URL(link);
    const host = url.hostname.replace('www.', '').split('.')[0];
    return `/imgs/${host}.png`;
  } catch (e) {
    return '';
  }
}


