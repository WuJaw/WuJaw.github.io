"""
博客图片路径自动替换脚本
1. 将 Markdown 中的图片路径统一替换为 /assets/xxx.png 格式（Typora + Jekyll 通用）
2. 自动添加 typora-root-url 到 front matter（如果没有的话）
3. 如果图片不在 assets/ 目录，自动拷贝过来

用法：python fix_img_path.py [文件路径]
  - 不传参数：处理项目中所有 .md 文件
  - 传文件路径：处理指定文件
"""

import os
import re
import shutil
import sys
import glob

BLOG_ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BLOG_ROOT, 'assets')
IMG_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
IMG_EXTS = ('png', 'jpg', 'jpeg', 'gif', 'svg', 'webp')
FRONT_MATTER = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)


def find_image(fname):
    """在整个项目中查找图片文件"""
    if not fname or '.' not in fname:
        return None
    target = os.path.join(ASSETS_DIR, fname)
    if os.path.isfile(target):
        return target
    for root, dirs, files in os.walk(BLOG_ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '_site')]
        if fname in files:
            return os.path.join(root, fname)
    return None


def add_typora_root_url(content):
    """在 front matter 中添加 typora-root-url（如果没有）"""
    match = FRONT_MATTER.match(content)
    if not match:
        return content

    fm = match.group(1)
    if 'typora-root-url' in fm:
        return content

    # 在 front matter 末尾添加
    new_fm = fm.rstrip() + '\ntypora-root-url: ..\\..\n'
    new_content = content[:match.start()] + '---\n' + new_fm + '---' + content[match.end():]
    return new_content


def fix_file(md_path):
    """处理单个 Markdown 文件"""
    md_dir = os.path.dirname(os.path.abspath(md_path))

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 添加 typora-root-url
    content = add_typora_root_url(content)

    changes = 0
    copies = 0
    not_found = []

    def replacer(match):
        nonlocal changes, copies
        desc = match.group(1)
        raw_path = match.group(2)

        # 已经是正确格式 /assets/xxx.png，跳过
        if raw_path.startswith('/assets/'):
            return match.group(0)

        # 跳过 Liquid 标签（兼容旧格式，替换为新格式）
        if '{{' in raw_path:
            # 从 Liquid 标签中提取文件名
            m = re.search(r'/assets/([^"}]+)', raw_path)
            if m:
                fname = m.group(1)
                changes += 1
                return f'![{desc}](/assets/{fname})'
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
        return f'![{desc}](/assets/{fname})'

    new_content = IMG_PATTERN.sub(replacer, content)

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
