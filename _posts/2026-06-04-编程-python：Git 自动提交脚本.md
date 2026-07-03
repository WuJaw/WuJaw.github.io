---
layout: post
title: "python：Git 自动提交脚本"
date: 2026-06-04
category: 编程
---

每次改完代码要 `git add` → `git commit` → `git push`，敲三句命令不可怕，可怕的是 commit message 写什么。顺手写 `update` 太敷衍，写详细又不想费脑子。

于是写了个 Python 脚本，双击 `autocommit.bat`，自动完成三步操作，commit message 用 `git status` 的输出代替——哪个文件改了、是新增还是删除，一目了然。

---

## 1 效果

双击 bat 后终端输出：

```
==================================================
变更文件：
  M  _posts/2026-06-04-博客-git-autocommit.md
  M  change/autocommit.py
  A  autocommit.bat

提交成功 [a1b2c3d]
--------------------------------------------------
提交内容：
Auto-commit:
  M _posts/2026-06-04-博客-git-autocommit.md
  M change/autocommit.py
  A autocommit.bat
共 3 个文件
--------------------------------------------------
共 3 个文件
推送成功。
==================================================
```

看一眼就知道这次 push 了什么。

---

## 2 目录结构

在工程根目录放两个文件：

```
你的工程/
├── autocommit.bat       ← 双击入口
└── change/
    └── autocommit.py    ← 实际逻辑
```

---

## 3 autocommit.bat

```batch
@echo off
chcp 65001 >nul
cd /d "%~dp0"
python change\autocommit.py
pause
```

三件事：切 UTF-8 编码、跳到 bat 所在目录、执行 Python 脚本。`pause` 让窗口不要一闪而过。

---

## 4 autocommit.py

```python
#!/usr/bin/env python3
"""
自动 git add / commit / push，生成包含变更文件列表的 commit message。
"""

import os
import subprocess
import sys
import tempfile

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git(*args):
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false"] + list(args),
        cwd=ROOT_DIR,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return result


def main():
    # add all
    git("add", ".")

    # check status
    r = git("status", "--porcelain")
    if r.returncode != 0:
        print(f"git status 失败: {r.stderr.strip()}")
        sys.exit(1)

    lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
    if not lines:
        print("无变更，跳过提交。")
        return

    # 显示变更文件列表
    print("=" * 50)
    print("变更文件：")
    for line in lines:
        status = line[:2]
        path = line[3:]
        print(f"  {status}  {path}")

    # write commit message to temp file
    msg_fd, msg_path = tempfile.mkstemp(suffix=".txt", prefix="autocommit_")
    try:
        with os.fdopen(msg_fd, "w", encoding="utf-8") as f:
            f.write("Auto-commit:\n")
            for line in lines:
                f.write(f"  {line}\n")
            f.write(f"共 {len(lines)} 个文件\n")

        # commit
        r = git("commit", "-F", msg_path)
        if r.returncode != 0:
            print(f"\n提交失败: {r.stderr.strip()}")
            sys.exit(1)

        # 获取 commit hash
        hash_r = git("rev-parse", "--short", "HEAD")
        commit_hash = hash_r.stdout.strip()

        print(f"\n提交成功 [{commit_hash}]")
        print("-" * 50)
        print("提交内容：")
        with open(msg_path, "r", encoding="utf-8") as f:
            commit_msg = f.read().strip()
        print(commit_msg)
        print("-" * 50)
        print(f"共 {len(lines)} 个文件")

        # push
        r = git("push")
        if r.returncode != 0:
            print(f"\n推送失败: {r.stderr.strip()}")
            sys.exit(1)
        print("推送成功。")
        print("=" * 50)
    finally:
        os.unlink(msg_path)


if __name__ == "__main__":
    main()
```

步骤拆开看：

1. `git add .` — 暂存所有变更
2. `git status --porcelain` — 拿到变更文件列表（`M`/`A`/`D` + 路径）
3. 用这个列表生成 commit message，写入临时文件
4. `git commit -F` 从临时文件读 message 提交
5. `git rev-parse --short HEAD` 获取 commit hash 显示出来
6. `git push` 推送
7. 清理临时文件

---

## 5 复制到其他工程

只需要三步：

**1. 把两个文件拷过去**

```
目标工程/
├── autocommit.bat         ← 拷过来
└── change/
    └── autocommit.py      ← 拷过来
```

**2. 确保 Python 可用**

命令行跑一下：

```bash
python --version
```

脚本用的是标准库，不需要 pip 装任何东西。

**3. 双击 `autocommit.bat`**

就这么简单。前提是目标工程已经初始化了 git 仓库（`git init` 过），并且 `autocommit.py` 放在 `change/` 子目录下。

---

## 6 几点说明

**为什么用临时文件写 commit message？**

因为 `git commit -m` 处理换行很别扭，多行 message 需要多次 `-m`，而中文路径在命令行传参容易被 shell 截断。写入临时文件再用 `-F` 读取更干净。

**为什么路径检测靠 `__file__` 而非 `os.getcwd()`？**

`bat` 里用了 `cd /d "%~dp0"`，所以 `__file__` 和 cwd 通常一致。但万一有人在别处调用，`__file__` 保证定位到脚本自身位置并以此推导工程根目录，不会跑偏。

**`core.quotepath=false` 是什么？**

git 默认把非 ASCII 路径编码成 `\344\270\255\346\226\207` 这种转义形式。加上这个参数后，`git status` 直接输出原始中文路径名，提交记录里才看得懂。
