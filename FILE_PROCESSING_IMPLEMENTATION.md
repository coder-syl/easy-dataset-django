# 文件处理功能实现说明

## ✅ 已完成

### 1. 文件处理服务 (`common/services/file_processor.py`)
- ✅ PDF文件处理（使用PyMuPDF）
  - 支持从目录提取章节
  - 支持逐页提取文本
  - 自动转换为Markdown格式
  
- ✅ DOCX文件处理（使用python-docx）
  - 提取段落和标题
  - 处理表格
  - 转换为Markdown格式
  
- ✅ EPUB文件处理（使用ebooklib和BeautifulSoup）
  - 按spine顺序提取章节
  - 提取书籍标题和章节标题
  - 转换为Markdown格式
  
- ✅ 文本文件处理（Markdown、TXT）
  - 支持多种编码（UTF-8、GBK、GB2312）
  - TXT文件自动转换为Markdown

### 2. 文件上传功能增强 (`files/views.py`)
- ✅ 支持多种文件格式上传
  - `.md`, `.markdown` - Markdown文件
  - `.txt` - 文本文件
  - `.pdf` - PDF文件
  - `.docx` - Word文档
  - `.epub` - EPUB电子书

- ✅ 自动文件处理
  - 上传后自动提取内容
  - 转换为Markdown格式
  - 保存原始文件和Markdown文件

### 3. 文件预览功能 (`files/preview_views.py`)
- ✅ 支持预览Markdown文件
- ✅ 支持预览PDF文件（返回原始PDF）
- ✅ 优先返回处理后的Markdown文件

### 4. 依赖包更新 (`requirements.txt`)
已添加以下依赖：
- `PyMuPDF>=1.23.0` - PDF处理
- `python-docx>=1.1.0` - DOCX处理
- `ebooklib>=0.18` - EPUB处理
- `beautifulsoup4>=4.12.0` - HTML解析

## 📝 使用说明

### 安装依赖
```bash
cd easy-dataset-django
pip install -r requirements.txt
```

### 上传文件
```bash
# 上传PDF文件
curl -X POST http://localhost:8000/api/projects/{projectId}/files/ \
  -H "x-file-name: document.pdf" \
  --data-binary @document.pdf

# 上传DOCX文件
curl -X POST http://localhost:8000/api/projects/{projectId}/files/ \
  -H "x-file-name: document.docx" \
  --data-binary @document.docx

# 上传EPUB文件
curl -X POST http://localhost:8000/api/projects/{projectId}/files/ \
  -H "x-file-name: book.epub" \
  --data-binary @book.epub
```

### 预览文件
```bash
# 预览文件（返回Markdown内容）
curl http://localhost:8000/api/projects/{projectId}/files/preview/{fileId}/
```

## 🔧 技术实现

### PDF处理流程
1. 使用PyMuPDF打开PDF文件
2. 尝试从目录（TOC）提取章节结构
3. 如果无目录，逐页提取文本
4. 清理内容（移除空字符、多余空行）
5. 转换为Markdown格式

### DOCX处理流程
1. 使用python-docx打开文档
2. 提取段落和标题（识别样式）
3. 处理表格（转换为Markdown表格）
4. 转换为Markdown格式

### EPUB处理流程
1. 使用ebooklib读取EPUB文件
2. 按spine顺序提取章节
3. 使用BeautifulSoup解析HTML内容
4. 提取标题和正文
5. 转换为Markdown格式

## ⚠️ 注意事项

1. **文件大小限制**: 建议单个文件不超过100MB
2. **编码问题**: 文本文件会自动尝试多种编码
3. **PDF质量**: 扫描版PDF需要OCR，当前实现仅支持文本型PDF
4. **表格处理**: DOCX中的复杂表格可能无法完美转换

## 🚀 后续优化

- [ ] 支持OCR处理扫描版PDF
- [ ] 优化表格转换质量
- [ ] 支持更多文件格式（RTF、ODT等）
- [ ] 添加文件处理进度跟踪
- [ ] 支持批量文件处理

