"""
PDF processing utilities for converting PDF to Markdown.
Provides a simple 'default' strategy using pdfminer.six to extract text.
"""
from pathlib import Path
import logging
from typing import Dict

logger = logging.getLogger('files.pdf_processing')


def default_processing(project_id: str, file_name: str, options: Dict = None) -> Dict:
    """
    Default PDF -> Markdown conversion using pdfminer.six text extraction.
    Writes converted markdown to local-db/<project_id>/files/<base>.md
    """
    try:
        from pdfminer.high_level import extract_text
    except Exception as e:
        logger.warning('pdfminer.six not available: %s, falling back to PyPDF2 if available', e)
        try:
            # fallback: try PyPDF2 text extraction
            import PyPDF2  # type: ignore
            def extract_text_fallback(path):
                text_parts = []
                with open(path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        try:
                            text_parts.append(page.extract_text() or '')
                        except Exception:
                            continue
                return '\n'.join(text_parts)
            extract_text = extract_text_fallback
        except Exception:
            logger.error('No suitable PDF text extraction library available (pdfminer or PyPDF2).')
            raise

    project_path = Path('local-db') / project_id / 'files'
    project_path.mkdir(parents=True, exist_ok=True)
    pdf_path = project_path / file_name
    if not pdf_path.exists():
        raise FileNotFoundError(f'PDF file not found: {pdf_path}')

    base_name = Path(file_name).stem
    convert_name = f"{base_name}.md"
    output_path = project_path / convert_name

    logger.info(f'Converting PDF to Markdown: {pdf_path} -> {output_path}')
    # extract text (single block)
    text = extract_text(str(pdf_path))
    # basic normalization and write
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text or '')

    return {'success': True, 'fileName': convert_name, 'pageCount': 1}


def _extract_text_by_page(pdf_path: Path):
    """
    Extract text per page using pdfminer (fallback may be slower).
    Returns list of page texts.
    """
    try:
        from pdfminer.pdfpage import PDFPage
        from pdfminer.high_level import extract_text
    except Exception:
        # If pdfminer isn't available, attempt fallback by extracting entire text and splitting roughly by form feed
        text_all = extract_text(str(pdf_path))
        # best-effort split by page break marker
        pages = text_all.split('\f') if text_all else [text_all or '']
        return pages

    pages = []
    with open(pdf_path, 'rb') as f:
        page_count = 0
        # Count pages first
        for _ in PDFPage.get_pages(f):
            page_count += 1
    # extract per page (pdfminer supports page_numbers)
    for i in range(page_count):
        try:
            page_text = extract_text(str(pdf_path), page_numbers=[i]) or ''
        except Exception:
            page_text = ''
        pages.append(page_text)
    return pages


def _to_markdown_preserve_structure(page_text: str):
    """
    Simple heuristics to convert plain text to Markdown:
    - Collapse multiple blank lines
    - Detect headings (short lines without trailing punctuation) and prefix '## '
    - Join lines into paragraphs
    """
    import re
    lines = [ln.rstrip() for ln in page_text.splitlines()]
    out_lines = []
    buf = []
    def flush_buf():
        nonlocal buf, out_lines
        if not buf:
            return
        para = ' '.join([ln.strip() for ln in buf]).strip()
        if para:
            out_lines.append(para)
        buf = []

    for idx, ln in enumerate(lines):
        if not ln.strip():
            # blank line -> paragraph break
            flush_buf()
            continue
        # heading heuristic
        stripped = ln.strip()
        is_heading = False
        if len(stripped) <= 80 and not re.search(r'[。！？\.\?\!,:;]', stripped) and stripped[0].isupper():
            is_heading = True
        if stripped.startswith('#'):
            is_heading = True

        if is_heading:
            flush_buf()
            # add as heading (h2)
            heading = stripped
            if not heading.startswith('#'):
                heading = '## ' + heading
            out_lines.append(heading)
        else:
            buf.append(ln)
    flush_buf()
    # join with double newlines and normalize whitespace
    md = '\n\n'.join(out_lines)
    # trim repeated empty lines
    md = re.sub(r'\n{3,}', '\n\n', md)
    return md


def mineru_processing(project_id: str, file_name: str, options: Dict = None) -> Dict:
    """
    MinerU strategy: call external MinerU API to convert PDF to Markdown.
    Follows Node logic:
      1. read token from local-db/<project>/task-config.json (minerUToken)
      2. call /file-urls/batch to get upload URL and batch id
      3. upload file via PUT
      4. poll /extract-results/batch/{batchId} until state == done
      5. download full_zip_url and extract .md into files dir
    Returns dict with success and fileName. Raises on error.
    """
    import requests
    import json
    import time
    import zipfile
    from io import BytesIO

    MINERU_API_BASE = options.get('mineru_base') if options and options.get('mineru_base') else 'https://mineru.net/api/v4'
    POLL_INTERVAL = options.get('poll_interval', 3)

    project_path = Path('local-db') / project_id / 'files'
    pdf_path = project_path / file_name
    if not pdf_path.exists():
        raise FileNotFoundError(f'PDF file not found: {pdf_path}')

    # read task-config to get minerUToken (same location as Node)
    task_config_path = Path('local-db') / project_id / 'task-config.json'
    if not task_config_path.exists():
        raise FileNotFoundError('task-config.json not found for project: ' + str(project_id))
    with open(task_config_path, 'r', encoding='utf-8') as f:
        task_conf = json.load(f)
    key = task_conf.get('minerUToken') or task_conf.get('minerUToken', '')
    if not key:
        raise ValueError('minerUToken not configured in task-config.json')

    # 1. request upload urls
    request_options = {
        "enable_formula": True,
        "layout_model": "doclayout_yolo",
        "enable_table": True,
        "files": [{"name": file_name, "is_ocr": True, "data_id": "abcd"}]
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    r = requests.post(f"{MINERU_API_BASE}/file-urls/batch", headers=headers, json=request_options, timeout=60)
    if r.status_code < 200 or r.status_code >= 300:
        raise RuntimeError(f"mineru file-urls request failed: {r.status_code} {r.text}")
    url_response = r.json()
    if url_response.get('code') != 0 or not url_response.get('data', {}).get('file_urls'):
        raise RuntimeError("failed to get file upload url: " + json.dumps(url_response))

    upload_url = url_response['data']['file_urls'][0]
    batch_id = url_response['data'].get('batch_id')
    # 2. upload file via PUT
    with open(pdf_path, 'rb') as f:
        put_resp = requests.put(upload_url, data=f, timeout=120)
        if put_resp.status_code not in (200, 201):
            raise RuntimeError(f"upload failed: {put_resp.status_code} {put_resp.text}")

    # 3. poll extract-results
    while True:
        r2 = requests.get(f"{MINERU_API_BASE}/extract-results/batch/{batch_id}", headers=headers, timeout=30)
        if r2.status_code < 200 or r2.status_code >= 300:
            raise RuntimeError(f"mineru extract-results request failed: {r2.status_code} {r2.text}")
        data = r2.json()
        extract = data.get('data', {}).get('extract_result', [{}])[0]
        state = extract.get('state')
        progress = extract.get('extract_progress') or {}
        extracted_pages = progress.get('extracted_pages', 0)
        total_pages = progress.get('total_pages', 0)

        # Update caller-provided task progress if available
        try:
            update_cb = options.get('update_task') if options else None
            task_obj = options.get('task') if options else None
            message_obj = options.get('message') if options else None
            if message_obj is not None:
                message_obj.setdefault('current', {})
                message_obj['current']['processedPage'] = extracted_pages
                message_obj['current']['totalPage'] = total_pages
                message_obj['stepInfo'] = f'processing {file_name} {extracted_pages}/{total_pages} pages progress: {((extracted_pages / total_pages) * 100) if total_pages else 0}%'
            if update_cb and callable(update_cb) and task_obj:
                try:
                    update_cb(task_obj.id, {
                        'completed_count': extracted_pages,
                        'detail': json.dumps(message_obj) if message_obj is not None else json.dumps({'current': {'processedPage': extracted_pages, 'totalPage': total_pages}})
                    })
                except Exception:
                    # ignore update failures
                    pass
        except Exception:
            pass

        if data.get('code') == 0 and state == 'done':
            zip_url = extract.get('full_zip_url')
            if not zip_url:
                raise RuntimeError('mineru done but no zip url')
            # download zip and extract md
            zresp = requests.get(zip_url, headers={}, timeout=120)
            if zresp.status_code < 200 or zresp.status_code >= 300:
                raise RuntimeError(f"failed to download result zip: {zresp.status_code}")
            zbuf = BytesIO(zresp.content)
            with zipfile.ZipFile(zbuf) as zf:
                md_entries = [entry for entry in zf.infolist() if entry.filename.lower().endswith('.md')]
                if not md_entries:
                    raise RuntimeError('no md file found in mineru zip')
                # prefer entry whose basename matches original PDF base name
                base_name = pdf_path.stem
                chosen = None
                for entry in md_entries:
                    if Path(entry.filename).stem.lower() == base_name.lower():
                        chosen = entry
                        break
                if not chosen:
                    chosen = md_entries[0]
                content_bytes = zf.read(chosen)
                # attempt utf-8, fallback to gbk then latin-1
                content = None
                for enc in ('utf-8', 'gbk', 'latin-1'):
                    try:
                        content = content_bytes.decode(enc)
                        break
                    except Exception:
                        content = None
                if content is None:
                    content = content_bytes.decode('utf-8', errors='replace')
                outpath = project_path / (Path(chosen.filename).name)
                with open(outpath, 'w', encoding='utf-8') as outf:
                    outf.write(content)
                return {'success': True, 'fileName': outpath.name, 'pageCount': total_pages}
        if data.get('code') != 0 or state == 'failed':
            raise RuntimeError(f"mineru processing failed: {json.dumps(data)}")
        time.sleep(POLL_INTERVAL)


def vision_processing(project_id: str, file_name: str, options: Dict = None) -> Dict:
    """
    基于视觉的PDF处理方法：
    - 首选使用 Node.js 实现的 pdf2md-js 工具进行PDF转Markdown，保证与Node端结果一致；
    - 若Node工具不可用，则回退为本地OCR（如pytesseract）进行逐页图片识别；
    - 支持通过 options 传入自定义的提示词和参数；
    参数说明:
        project_id: 项目ID字符串
        file_name: 项目下 PDF 文件名
        options: 可选参数(字典)，可包括
            - language: 指定语言 (如'zh-CN', 'en'等)
            - prompt, textPrompt: 自定义提示词
            - concurrency: 并发数（如流程支持）
    返回:
        dict，主要包含 keys: success, fileName, pageCount 等
    """
    """
    Vision-based processing: render pages to images and OCR using pytesseract.
    Falls back to mineru_processing if necessary libraries are unavailable.
    """
    project_path = Path('local-db') / project_id / 'files'
    pdf_path = project_path / file_name
    if not pdf_path.exists():
        raise FileNotFoundError(f'PDF file not found: {pdf_path}')

    # Pure-Python vision strategy (no Node): render pages and OCR, optionally call vision-capable LLM
    from common.services.prompt_service import get_pdf_to_markdown_prompt
    language = options.get('language') if options and options.get('language') else 'zh-CN'
    prompt_template = get_pdf_to_markdown_prompt(language, project_id)
    model_config = options.get('model') if options else None
    use_vision_model = bool(model_config)

    try:
        import fitz  # PyMuPDF
    except Exception as e:
        logger.warning('PyMuPDF (fitz) not available: %s', e)
        return mineru_processing(project_id, file_name, options)

    doc = fitz.open(str(pdf_path))
    page_count = doc.page_count
    base_name = pdf_path.stem
    convert_name = f"{base_name}.md"
    output_path = project_path / convert_name

    md_parts = []
    page_infos = []
    for i in range(page_count):
        try:
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes(output='png')
            page_text = ''
            # If a vision model configured, send image to model's vision API
            if use_vision_model:
                try:
                    import base64
                    b64 = base64.b64encode(img_bytes).decode('utf-8')
                    from common.services.llm_service import LLMService
                    llm = LLMService(model_config)
                    # LLM's vision interface expects prompt and base64 image
                    resp = llm.get_vision_response(prompt_template, b64, 'image/png')
                    page_text = resp.get('answer') or resp.get('text') or ''
                except Exception as e:
                    logger.warning('Vision model call failed on page %d: %s', i + 1, str(e))
                    page_text = ''
            else:
                # fallback to pytesseract OCR
                try:
                    from PIL import Image
                    import pytesseract
                    from io import BytesIO
                    img = Image.open(BytesIO(img_bytes)).convert('RGB')
                    ocr_lang = options.get('ocr_lang', 'chi_sim+eng') if options else 'eng'
                    page_text = pytesseract.image_to_string(img, lang=ocr_lang)
                except Exception as e:
                    logger.warning('pytesseract OCR failed on page %d: %s', i + 1, str(e))
                    page_text = ''

            # Extract visual block metadata for this page to help LLM judge headings/layout
            visual_blocks = []
            try:
                page_dict = page.get_text("dict")
                blocks = page_dict.get("blocks", []) if isinstance(page_dict, dict) else []
                for bi, block in enumerate(blocks):
                    bbox = block.get("bbox", [])
                    # collect snippet from first 120 chars of the block text
                    block_text = ""
                    if "lines" in block:
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                block_text += span.get("text", "")
                    snippet = (block_text or "")[:120].replace("\n", " ")
                    # try extract font size / bold from first span
                    font_size = None
                    is_bold = False
                    try:
                        first_span = block.get("lines", [])[0].get("spans", [])[0]
                        font_size = first_span.get("size")
                        font_name = first_span.get("font", "") or ""
                        if "Bold" in font_name or "Bold" in first_span.get("flags", ""):
                            is_bold = True
                    except Exception:
                        pass
                    visual_blocks.append({
                        "block_index": bi,
                        "bbox": bbox,
                        "font_size": font_size,
                        "is_bold": bool(is_bold),
                        "snippet": snippet
                    })
            except Exception:
                visual_blocks = []

            # refine via LLM if model_config provided (non-vision model can also be used to clean/structure)
            md_page = ""
            if page_text and page_text.strip():
                try:
                    if model_config:
                        from common.services.llm_service import LLMService
                        llm_refine = LLMService(model_config)
                        # include visual metadata as JSON appendix to prompt to help LLM determine heading levels
                        import json as _json
                        visual_info_text = _json.dumps(visual_blocks, ensure_ascii=False)
                        refine_prompt = prompt_template.replace('{{text}}', page_text) + "\n\nVisualBlocks:\n" + visual_info_text
                        resp = llm_refine.get_response_with_cot(refine_prompt)
                        md_page = resp.get('answer') or resp.get('text') or ''
                    else:
                        md_page = _to_markdown_preserve_structure(page_text)
                except Exception:
                    md_page = _to_markdown_preserve_structure(page_text)
            else:
                md_page = ""

            md_parts.append(f"<!-- PAGE {i+1} -->\n\n" + (md_page or ''))
            page_infos.append({'page': i + 1, 'length': len(page_text or ''), 'markdownLength': len(md_page or '')})
        except Exception as e:
            logger.error('Failed processing page %d: %s', i + 1, str(e), exc_info=True)
            md_parts.append(f"<!-- PAGE {i+1} -->\n\n")
            page_infos.append({'page': i + 1, 'length': 0, 'markdownLength': 0})

    full_md = '\n\n'.join(md_parts)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_md)

    return {'success': True, 'fileName': convert_name, 'pageCount': page_count, 'pages': page_infos}


def process_pdf(strategy: str = 'default', project_id: str = '', file_name: str = '', options: Dict = None) -> Dict:
    """
    Entry for PDF processing. Strategy can be extended.
    """
    strategy = (strategy or 'default').lower()
    if strategy == 'default':
        return default_processing(project_id, file_name, options or {})
    elif strategy == 'mineru':
        return mineru_processing(project_id, file_name, options or {})
    elif strategy == 'vision':
        return vision_processing(project_id, file_name, options or {})
    else:
        raise ValueError(f'Unsupported pdf processing strategy: {strategy}')


