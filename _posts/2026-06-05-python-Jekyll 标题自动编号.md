---
layout: post
title: "Jekyll 标题自动编号"
date: 2026-06-05
category: python
---

写文章时手写章节编号很麻烦：调整结构之后编号全乱，还得一个个改。写了个 Python 脚本，自动扫描 `_posts/` 下的 Markdown 文件，对 `##` 以下的标题按层级编号，重复跑幂等——旧编号先剥掉再重写。

---

## 1 效果

输入：

```markdown
## 简介

### 背景

### 目的

## 一、中文序号章节

### 1.1 已有旧编号的子节
```

运行后：

```markdown
## 1 简介

### 1.1 背景

### 1.2 目的

## 2 中文序号章节

### 2.1 已有旧编号的子节
```

规则：
- `##` → `1`、`2`、`3`……（h2 级，不加尾点）
- `###` → `1.1`、`1.2`、`2.1`……（h3 级）
- `####` → `1.1.1`、`1.1.2`……（h4 级，依此类推）
- 自动剥除旧编号：数字编号（`1.`、`1.1`、`2.3.1`）和中文序号（`一、`、`二、`）都支持
- `#`（h1）不参与编号
- Front matter 和代码块内容跳过

---

## 2 目录结构

```
你的博客/
├── auto_number.bat          ← 双击入口
└── python/
    └── auto_number_headings.py
```

---

## 3 auto_number.bat

```batch
@echo off
chcp 65001 >nul
cd /d "%~dp0"
python python\auto_number_headings.py _posts\
pause
```

切到博客根目录，对整个 `_posts/` 批量编号。如果只想处理单个文件：

```batch
python python\auto_number_headings.py _posts\2026-06-05-xxx.md
```

---

## 4 auto_number_headings.py

```python
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
    """循除去标题已有的编号前缀，直到不匹配为止"""
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
```

---

## 5 逻辑拆解

**编号逻辑**

维护一个 5 位计数器数组 `counters`，索引 0 对应 `##`，索引 1 对应 `###`，以此类推。遇到标题时：

1. 当前层级计数器 +1
2. 所有更深层级计数器清零
3. 把 `counters[0]` 到 `counters[level]` 用 `.` 连接，得到编号

例如：

```
## 标题  →  counters = [1,0,0,0,0]  →  "1"
## 标题  →  counters = [2,0,0,0,0]  →  "2"
### 子节 →  counters = [2,1,0,0,0]  →  "2.1"
### 子节 →  counters = [2,2,0,0,0]  →  "2.2"
## 标题  →  counters = [3,0,0,0,0]  →  "3"
```

**剥旧编号**

`strip_number` 用两个正则**循环**匹配，剥到干净为止：

```python
# 数字编号：必须数字后跟空格+内容，避免误匹配纯数字标题
EXISTING_NUM_RE = re.compile(r'^(\d+(?:\.\d+)*)\.?\s+(.+)$')

# 中文序号：一、二、三……
CHINESE_NUM_RE = re.compile(r'^[一二三四五六七八九十百]+[、．.]\s*(.+)$')
```

数字编号要求后面有空格和内容，所以 `## 42` 这种纯数字标题不会被误识别。

**为什么要循环**：标题可能出现多层编号叠加的情况。比如先手写了中文序号 `一、开发环境准备`，脚本跑完变成 `## 1 一、开发环境准备`——上次的编号没剥干净。单次匹配只会剥掉 `1` 而留下 `一、`，导致中文序号永远残留。循环剥除可以处理任意层级叠加的脏编号。

**跳过规则**

- Front matter（`---` 到 `---` 之间）：完整跳过
- 围栏代码块（` ``` ` 包裹的内容）：完整跳过，内部的 `##` 不处理

---

## 6 和 deploy.bat 配合

整套发布流程：

```
写文章
  ↓
双击 web.bat        （图片路径转换，Typora 相对路径 → 网站绝对路径）
  ↓
双击 add_fm.bat     （补齐 front matter）
  ↓
双击 auto_number.bat（标题自动编号）
  ↓
双击 autocommit.bat （git add / commit / push）
```

或者直接用 `deploy.bat` 一步走完后三步。
