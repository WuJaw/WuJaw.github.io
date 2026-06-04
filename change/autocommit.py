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
        status = line[:2]  # XY status code
        path = line[3:]    # file path
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
        # 读取 commit message 内容
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
