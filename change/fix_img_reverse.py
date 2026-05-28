"""
博客图片路径反转脚本
将 <img src="/assets/xxx.png"> 或 ![desc](/assets/xxx.png) 转换回 Typora 可预览的 ![desc](../assets/xxx.png)

用法：python fix_img_reverse.py [文件路径]
  - 不传参数：处理项目中所有 .md 文件
  - 传文件路径：处理指定文件
"""

import os
import re
import sys
import glob

BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 匹配 <img src="/assets/xxx.png" alt="xxx">
IMG_TAG_PATTERN = re.compile(r'<img\s+src="(/assets/[^"]+)"\s+alt="([^"]*)"\s*>')
# 匹配 ![desc](/assets/xxx.png)
MD_ABS_PATTERN = re.compile(r'!\[([^\]]*)\]\(/assets/([^)]+)\)')


def fix_file(md_path):
    """处理单个 Markdown 文件：转为 Typora 相对路径格式"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # <img src="/assets/xxx.png" alt="desc"> -> ![desc](../assets/xxx.png)
    content = IMG_TAG_PATTERN.sub(lambda m: f'![{m.group(2)}](../assets/{m.group(1).split("/")[-1]})', content)

    # ![desc](/assets/xxx.png) -> ![desc](../assets/xxx.png)
    content = MD_ABS_PATTERN.sub(lambda m: f'![{m.group(1)}](../assets/{m.group(2)})', content)

    if content != original:
        count = len(IMG_TAG_PATTERN.findall(original)) + len(MD_ABS_PATTERN.findall(original))
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  转换 {count} 处为 Typora 格式')
    else:
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

    print(f'共 {len(targets)} 个文件待处理：')
    for path in targets:
        print(f'  {os.path.relpath(path, BLOG_ROOT)}')
        fix_file(path)
    print('\n完成（已转为 Typora 预览格式）')


if __name__ == '__main__':
    main()
