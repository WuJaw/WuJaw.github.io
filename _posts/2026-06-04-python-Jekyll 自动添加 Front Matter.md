---
layout: post
title: "Jekyll 自动添加 Front Matter"
date: 2026-06-04
category: python
---

Jekyll 文章的 front matter 和文件名里的日期 / 分类 / 标题其实是一一对应的，但手写 front matter 很容易和文件名脱节——改完文件名忘了改里面的 `title:`，或者 `date:` 和文件名对不上，构建不会报错但页面显示就乱了。

写了个 Python 脚本，扫描 `_posts/` 下所有 `.md` 文件，根据文件名强制重写 front matter。不用担心改漏——旧 front matter 会被剥掉再重新生成，始终和文件名保持一致。

---

## 1 效果

双击 `add_fm.bat`：

```
扫描 14 个文件...

  写入: 2026-06-02-送检-CE 检测.md  ->  category=送检, title=CE 检测
  写入: 2026-06-03-物联网-SI446x双路射频频率配置.md  ->  category=物联网, title=SI446x双路射频频率配置
  跳过（文件名不匹配格式）: about.md

完成：写入 13 个，跳过 1 个
```

文件名格式不对的（比如没有日期前缀）会自动跳过，不破坏内容。

---

## 2 文件命名规则

脚本依赖的文件名格式：

```
YYYY-MM-DD-分类-标题.md
```

例如：

```
2026-06-02-送检-CE 检测.md
```

拆出来就是：

| 段 | 内容 | 对应 front matter |
|----|------|-------------------|
| `2026-06-02` | 日期 | `date: 2026-06-02` |
| `送检` | 分类 | `category: 送检` |
| `CE 检测` | 标题 | `title: "CE 检测"` |

分类和标题之间用第一个 `-` 分隔，标题内部可以有空格。

---

## 3 目录结构

```
你的工程/
├── add_fm.bat             ← 双击入口
└── change/
    └── add_front_matter.py ← 实际逻辑
```

---

## 4 add_fm.bat

```batch
@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
python change\add_front_matter.py
pause
```

---

## 5 add_front_matter.py

```python
#!/usr/bin/env python3
"""
根据文件名强制重写 _posts/ 下 .md 文件的 front matter。

文件名格式：YYYY-MM-DD-分类-标题.md
例如：2026-06-02-送检-CE 检测.md
生成：
  ---
  layout: post
  title: "CE 检测"
  date: 2026-06-02
  category: 送检
  ---

已有 front matter 的会先剥掉再重新生成，确保和文件名一致。
"""

import os
import re
import sys

POSTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_posts")

# 文件名格式：YYYY-MM-DD-分类-标题.md
FILE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+?)-(.+)\.md$")


def strip_front_matter(content):
    """剥掉已有的 front matter，返回纯正文"""
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            return content[end + 3:].lstrip("\n")
    return content


def process_file(filepath):
    """强制根据文件名重写 front matter"""
    filename = os.path.basename(filepath)

    m = FILE_PATTERN.match(filename)
    if not m:
        print(f"  跳过（文件名不匹配格式）: {filename}")
        return False

    date_str = m.group(1)
    category = m.group(2)
    title = m.group(3)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 剥掉旧 front matter，拿纯正文
        body = strip_front_matter(content)

        # 用文件名重新生成
        front_matter = f'---\nlayout: post\ntitle: "{title}"\ndate: {date_str}\ncategory: {category}\n---\n\n'

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(front_matter + body)

        print(f"  写入: {filename}  ->  category={category}, title={title}")
        return True
    except PermissionError:
        print(f"  跳过（文件被占用）: {filename}")
        return False


def main():
    if not os.path.isdir(POSTS_DIR):
        print(f"_posts 目录不存在: {POSTS_DIR}")
        sys.exit(1)

    md_files = sorted(f for f in os.listdir(POSTS_DIR) if f.endswith(".md"))
    if not md_files:
        print("_posts/ 下没有 .md 文件")
        return

    print(f"扫描 {len(md_files)} 个文件...\n")
    done = 0
    skip = 0
    for md in md_files:
        if process_file(os.path.join(POSTS_DIR, md)):
            done += 1
        else:
            skip += 1

    print(f"\n完成：写入 {done} 个，跳过 {skip} 个")


if __name__ == "__main__":
    main()
```

---

## 6 逻辑拆解

1. **剥旧** — `strip_front_matter()` 找到第一个 `---` 到第二个 `---` 之间的内容，整段切掉，只留正文
2. **解析文件名** — 正则 `(\d{4}-\d{2}-\d{2})-(.+?)-(.+)\.md$` 提取日期 / 分类 / 标题
3. **生成新 front matter** — 四个字段：`layout` / `title` / `date` / `category`
4. **拼回去** — 新 front matter + 原正文，覆盖写入

整个过程是**幂等的**——重复跑不会叠多层 front matter，因为每次都是先剥再写。

---

## 7 复制到其他 Jekyll 工程

三步：

**1. 拷文件**

```
目标工程/
├── add_fm.bat              ← 拷过来
└── change/
    └── add_front_matter.py  ← 拷过来
```

**2. 确保 `_posts/` 目录存在**

脚本硬编码了 `_posts/` 路径，如果你的文章放在别处，改这一行：

```python
POSTS_DIR = os.path.join(..., "你的目录名")
```

**3. 文件名符合规则后双击 bat**

分类建议用两三个字的中文标签（如"博客""送检""物联网"），方便后续在首页按分类聚合。

---

## 8 和 autocommit 配合

整套工作流是：

1. 写文章 → 存到 `_posts/YYYY-MM-DD-分类-标题.md`
2. 双击 `add_fm.bat` → 自动补齐 front matter
3. 双击 `autocommit.bat` → git add / commit / push 一条龙

全程不需要手写 front matter，也不需要手打 git 命令。
