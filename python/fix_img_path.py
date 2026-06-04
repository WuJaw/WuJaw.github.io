"""
博客图片路径自动替换脚本
1. 将 Markdown 图片替换为 <img> 标签，Typora 和 Jekyll 都能正确显示
2. 如果图片不在 assets/ 目录，自动拷贝过来

用法：python fix_img_path.py [文件路径]
  - 不传参数：处理项目中所有 .md 文件
  - 传文件路径：处理指定文件
"""

import os
import re
import shutil
import subprocess
import sys
import glob

BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BLOG_ROOT, 'assets')
IMG_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
IMG_EXTS = ('png', 'jpg', 'jpeg', 'gif', 'svg', 'webp')
INLINE_CODE = re.compile(r'`[^`]+`')  # 行内代码，里面的图片引用是教学示例，跳过

_ES_EXE = None  # Everything 命令行工具路径（延迟探测）


def _find_es():
    """查找 Everything 命令行工具 es.exe"""
    global _ES_EXE
    if _ES_EXE is not None:
        return _ES_EXE

    # 查找顺序：PATH → 项目自带 → 常见安装路径 → Program Files 递归
    es = shutil.which('es')
    if es:
        _ES_EXE = es
        return es

    # 项目 python/ 目录（兼容旧位置）
    own = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'es.exe')
    if os.path.isfile(own):
        _ES_EXE = own
        return own

    # 项目 tools/ 目录（推荐位置，随脚本分发）
    tools_dir = os.path.join(BLOG_ROOT, 'tools', 'es.exe')
    if os.path.isfile(tools_dir):
        _ES_EXE = tools_dir
        return tools_dir

    # 常见安装路径
    for pfx in [os.environ.get('ProgramFiles', ''), os.environ.get('ProgramFiles(x86)', '')]:
        for sub in ['', 'Everything 1.5a', 'Everything 1.4']:
            cand = os.path.join(pfx, 'Everything', sub, 'es.exe')
            if os.path.isfile(cand):
                _ES_EXE = cand
                return cand

    # Program Files\Everything 递归查找（覆盖自定义子目录安装）
    for pfx in [os.environ.get('ProgramFiles', ''), os.environ.get('ProgramFiles(x86)', '')]:
        ev_dir = os.path.join(pfx, 'Everything')
        if os.path.isdir(ev_dir):
            for root, dirs, files in os.walk(ev_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                if 'es.exe' in files:
                    _ES_EXE = os.path.join(root, 'es.exe')
                    return _ES_EXE

    _ES_EXE = ''  # 标记已探测，避免重复查找
    return ''


def _everything_search(fname):
    """用 Everything 秒搜全盘文件，返回第一个匹配的完整路径"""
    es = _find_es()
    if not es:
        return None
    try:
        r = subprocess.run(
            [es, '-n', '1', '-full-path-and-name', fname],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        )
        line = r.stdout.strip()
        if line and os.path.isfile(line):
            return line
    except Exception:
        pass
    return None


def find_image(fname):
    """全局查找图片文件：项目 → 常用目录 → 全用户目录"""
    if not fname or '.' not in fname:
        return None

    # 1) 已经在 assets/ 里
    target = os.path.join(ASSETS_DIR, fname)
    if os.path.isfile(target):
        return target

    # 2) 在项目目录内搜（排除 .git, _site 等）
    for root, dirs, files in os.walk(BLOG_ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '_site')]
        if fname in files:
            return os.path.join(root, fname)

    # 3) 在用户常用目录搜：桌面、下载、图片、文档
    home = os.path.expanduser('~')
    quick_dirs = [
        os.path.join(home, 'Desktop'),
        os.path.join(home, 'Downloads'),
        os.path.join(home, 'Pictures'),
        os.path.join(home, 'Documents'),
    ]
    for qdir in quick_dirs:
        if not os.path.isdir(qdir):
            continue
        for root, dirs, files in os.walk(qdir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            if fname in files:
                return os.path.join(root, fname)

    # 4) 用 Everything 全盘秒搜（如果装了的话）
    print(f'    Everything 搜索: {fname} ...', end='', flush=True)
    result = _everything_search(fname)
    if result:
        print(' 找到')
        return result

    # 5) Everything 不可用时，os.walk 兜底
    print(' 回退 os.walk ...', end='', flush=True)
    skip_dirs = {
        '.git', 'node_modules', '_site', '__pycache__',
        'AppData', '.cache', '.npm', '.cargo', '.rustup',
        '.local', '.config', '.vscode', '.workbuddy',
    }
    for root, dirs, files in os.walk(home):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        if fname in files:
            print(' 找到')
            return os.path.join(root, fname)
    print(' 未找到')

    return None


def fix_file(md_path):
    """处理单个 Markdown 文件"""
    md_dir = os.path.dirname(os.path.abspath(md_path))

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    changes = 0
    copies = 0
    not_found = []

    def replacer(match):
        nonlocal changes, copies
        desc = match.group(1)
        raw_path = match.group(2)

        # 已经是 <img> 标签格式，跳过
        if raw_path.startswith('/assets/'):
            return match.group(0)

        # 已经是 <img src="/assets/...">，跳过
        if '<img' in match.group(0) and '/assets/' in match.group(0):
            return match.group(0)

        # 处理 Liquid 标签，提取文件名
        if '{{' in raw_path:
            m = re.search(r'/assets/([^"}\s]+)', raw_path)
            if m:
                fname = m.group(1)
                changes += 1
                return f'<img src="/assets/{fname}" alt="{desc}">'
            return match.group(0)

        # 提取文件名
        fname = os.path.basename(raw_path)
        if not fname or '.' not in fname:
            return match.group(0)
        ext = fname.rsplit('.', 1)[-1].lower()
        if ext not in IMG_EXTS:
            return match.group(0)

        # 检查图片是否已在 assets/
        dest = os.path.join(ASSETS_DIR, fname)
        if not os.path.isfile(dest):
            # 尝试从原始路径找到图片
            src = None
            rel_path = os.path.normpath(os.path.join(md_dir, raw_path))
            if os.path.isfile(rel_path):
                src = rel_path
            if not src and os.path.isabs(raw_path):
                cleaned = raw_path.lstrip('/')
                if os.path.isfile(cleaned):
                    src = cleaned
            if not src:
                src = find_image(fname)

            if src:
                print(f'    复制: {fname} <- {src}')
                shutil.copy2(src, dest)
                copies += 1
            else:
                not_found.append(fname)
                return match.group(0)

        changes += 1
        return f'<img src="/assets/{fname}" alt="{desc}">'

    def _process_chunk(text):
        """对非代码块文本应用图片替换，跳过行内代码"""
        parts = []
        last = 0
        for m in INLINE_CODE.finditer(text):
            # 行内代码外的部分：正常匹配替换
            parts.append(IMG_PATTERN.sub(replacer, text[last:m.start()]))
            # 行内代码部分：原样保留（教学示例中的 ![](x) 之类）
            parts.append(text[m.start():m.end()])
            last = m.end()
        parts.append(IMG_PATTERN.sub(replacer, text[last:]))
        return ''.join(parts)

    # 按 fenced code block 分段：代码块内跳过，只处理代码块外的图片引用
    FENCE = re.compile(r'^```', re.MULTILINE)
    LEADING_FENCE = re.compile(r'^```[^\n]*\n')  # chunk 开头残留的 fence 行
    fence_positions = [m.start() for m in FENCE.finditer(content)]

    if len(fence_positions) % 2 != 0:
        # 奇数个 fence（未闭合的代码块），保守处理：从最后一个 fence 到文件末尾也视为代码块内
        fence_positions.append(len(content))

    result_parts = []
    prev = 0
    in_code = False
    for pos in fence_positions:
        chunk = content[prev:pos]
        if not in_code:
            # 非代码块可能以 ``` 行开头（上一个块的关闭标记），临时去掉再处理
            maybe_fence = ''
            fm = LEADING_FENCE.match(chunk)
            if fm:
                maybe_fence = fm.group()
                chunk = chunk[fm.end():]
            chunk = _process_chunk(chunk)
            chunk = maybe_fence + chunk  # 把 ``` 行放回去
        result_parts.append(chunk)
        in_code = not in_code
        prev = pos
    # 最后一个 chunk：fence 之后的剩余内容
    if prev < len(content):
        chunk = content[prev:]
        if not in_code:
            maybe_fence = ''
            fm = LEADING_FENCE.match(chunk)
            if fm:
                maybe_fence = fm.group()
                chunk = chunk[fm.end():]
            chunk = _process_chunk(chunk)
            chunk = maybe_fence + chunk
        result_parts.append(chunk)

    new_content = ''.join(result_parts)

    if new_content != content:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

    if changes or copies:
        print(f'  路径修复 {changes} 处，复制图片 {copies} 张')
    if not_found:
        print(f'  未找到图片: {", ".join(not_found)}')
    if not changes and not not_found:
        print('  无需修改')


def main():
    if len(sys.argv) > 1:
        targets = []
        for arg in sys.argv[1:]:
            if os.path.isdir(arg):
                targets.extend(glob.glob(os.path.join(arg, '**', '*.md'), recursive=True))
            elif os.path.isfile(arg):
                targets.append(arg)
    else:
        targets = sorted(glob.glob(os.path.join(BLOG_ROOT, '**', '*.md'), recursive=True))
        targets = [t for t in targets if '_site' not in t]

    if not targets:
        print('未找到 Markdown 文件')
        return

    os.makedirs(ASSETS_DIR, exist_ok=True)

    print(f'共 {len(targets)} 个文件待处理：')
    for path in targets:
        print(f'  {os.path.relpath(path, BLOG_ROOT)}')
        fix_file(path)
    print('\n完成')


if __name__ == '__main__':
    main()
