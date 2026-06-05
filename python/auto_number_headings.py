"""
Markdown 标题自动编号

从 h2（##）开始往下累加：
  ## → 1 / 2 / 3
  ### → 1.1 / 1.2 / 2.1
  #### → 1.1.1 / 1.1.2
  以此类推（编号后不加点）

自动去除已有编号再重新编排。跳过 front matter 和围栏代码块。
支持去除：纯数字编号（"1."、"1.1"、"2.3.1"）和中文序号（"一、"、"二、"等）。
"""

import os
import re
import sys

BLOG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 匹配标题行：## 到 ######
HEADING_RE = re.compile(r'^(#{2,6})\s+(.*)$')

# 匹配已有的数字编号前缀（如 "1."、"1.1"、"2.3.1"、"1.1."）
EXISTING_NUM_RE = re.compile(r'^(\d+(?:\.\d+)*)\.?\s+(.+)$')

# 匹配中文序号前缀（如 "一、"、"二、"、"十、"等）
CHINESE_NUM_RE = re.compile(r'^[一二三四五六七八九十百]+[、．.]\s*(.+)$')

# 围栏代码块
FENCE_RE = re.compile(r'^```', re.MULTILINE)


def strip_number(text):
    """循环去除标题已有的编号前缀，直到不匹配为止"""
    while True:
        changed = False
        # 先尝试数字编号（必须后面有空格+内容，避免误匹配纯数字标题）
        m = EXISTING_NUM_RE.match(text)
        if m:
            text = m.group(2).strip()
            changed = True
            continue
        # 再尝试中文序号
        m = CHINESE_NUM_RE.match(text)
        if m:
            text = m.group(1).strip()
            changed = True
            continue
        if not changed:
            break
    return text


def number_headings(content):
    """对正文中的 h2+ 标题自动编号"""
    lines = content.split('\n')
    result = []
    in_front_matter = False
    fm_dashes = 0
    in_code = False

    # 层级计数器，索引 0 对应 h2，1 对应 h3，以此类推
    counters = [0, 0, 0, 0, 0]

    for line in lines:
        # 处理 front matter
        if not in_code:
            if line.strip() == '---':
                fm_dashes += 1
                if fm_dashes == 1:
                    in_front_matter = True
                    result.append(line)
                    continue
                elif fm_dashes == 2:
                    in_front_matter = False
                    result.append(line)
                    continue

        if in_front_matter:
            result.append(line)
            continue

        # 处理代码块
        if FENCE_RE.match(line):
            in_code = not in_code
            result.append(line)
            continue

        if in_code:
            result.append(line)
            continue

        # 匹配标题
        m = HEADING_RE.match(line)
        if m:
            hashes = m.group(1)
            text = m.group(2)
            level = len(hashes) - 2  # h2 → 0, h3 → 1, ...

            # 去掉已有编号
            pure_text = strip_number(text)

            # 更新计数器
            counters[level] += 1
            # 重置所有更深层级的计数器
            for i in range(level + 1, len(counters)):
                counters[i] = 0

            # 生成编号：取从 0 到 level 的计数器
            number = '.'.join(str(c) for c in counters[:level + 1])

            result.append(f'{hashes} {number} {pure_text}')
        else:
            result.append(line)

    return '\n'.join(result)


def main():
    if len(sys.argv) < 2:
        print('用法: python auto_number_headings.py <markdown文件或目录>')
        print('示例: python auto_number_headings.py _posts/2026-06-04-博客-xxx.md')
        print('      python auto_number_headings.py _posts/')
        sys.exit(1)

    target = sys.argv[1]
    if not os.path.isabs(target):
        target = os.path.join(BLOG_ROOT, target)

    if os.path.isfile(target):
        files = [target]
    elif os.path.isdir(target):
        files = sorted(
            os.path.join(target, f)
            for f in os.listdir(target)
            if f.endswith('.md')
        )
    else:
        print(f'找不到: {target}')
        sys.exit(1)

    for md_path in files:
        with open(md_path, 'r', encoding='utf-8') as f:
            original = f.read()

        modified = number_headings(original)

        if modified == original:
            print(f'无需修改: {os.path.basename(md_path)}')
            continue

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(modified)

        print(f'已编号:   {os.path.basename(md_path)}')


if __name__ == '__main__':
    main()
