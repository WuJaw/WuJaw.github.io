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
