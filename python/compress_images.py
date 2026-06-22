"""
compress_images.py
------------------
压缩 assets/ 目录下的所有图片（PNG / JPG / JPEG）。

策略：
  - PNG：转为 RGBA/RGB 后以 optimize=True 重新保存（无损优化）
         若文件 > 200KB，额外将尺寸等比缩小至最长边 1280px
  - JPG/JPEG：quality=82 有损压缩，最长边同样限制 1280px
  - 原始文件直接覆盖（可改 BACKUP=True 先备份）

用法：
  直接双击运行 compress.bat，或
  python compress_images.py [assets目录路径]
"""

import io
import os
import sys

# Windows 控制台强制 UTF-8 输出
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from PIL import Image

# ── 配置 ────────────────────────────────────────────────
MAX_LONG_EDGE = 1280     # 最长边上限（像素），超过则等比缩小
PNG_SIZE_THRESHOLD = 200 * 1024   # PNG 超过此字节数才缩放（200 KB）
JPG_QUALITY = 82         # JPG 压缩质量（1-95）
BACKUP = False           # True 时先把原文件备份为 .bak
# ────────────────────────────────────────────────────────

SUPPORTED = {".png", ".jpg", ".jpeg"}


def resize_if_needed(img: Image.Image, max_edge: int) -> Image.Image:
    w, h = img.size
    if max(w, h) <= max_edge:
        return img
    if w >= h:
        new_w = max_edge
        new_h = int(h * max_edge / w)
    else:
        new_h = max_edge
        new_w = int(w * max_edge / h)
    return img.resize((new_w, new_h), Image.LANCZOS)


def compress(path: Path) -> tuple[int, int]:
    """返回 (原始字节, 压缩后字节)，压缩失败则两者相同。"""
    orig_size = path.stat().st_size
    try:
        img = Image.open(path)
        ext = path.suffix.lower()

        if ext == ".png":
            # 只在超过阈值时才缩放
            if orig_size > PNG_SIZE_THRESHOLD:
                img = resize_if_needed(img, MAX_LONG_EDGE)
            # 保持透明通道
            mode = "RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB"
            img = img.convert(mode)
            if BACKUP:
                path.rename(path.with_suffix(path.suffix + ".bak"))
            img.save(path, format="PNG", optimize=True)

        elif ext in (".jpg", ".jpeg"):
            img = resize_if_needed(img, MAX_LONG_EDGE)
            img = img.convert("RGB")
            if BACKUP:
                path.rename(path.with_suffix(path.suffix + ".bak"))
            img.save(path, format="JPEG", quality=JPG_QUALITY, optimize=True)

        new_size = path.stat().st_size
        return orig_size, new_size
    except Exception as e:
        print(f"  ⚠ 跳过 {path.name}：{e}")
        return orig_size, orig_size


def main():
    if len(sys.argv) > 1:
        assets_dir = Path(sys.argv[1])
    else:
        # 默认：脚本在 python/ 目录，assets/ 在上一层
        assets_dir = Path(__file__).parent.parent / "assets"

    if not assets_dir.is_dir():
        print(f"目录不存在：{assets_dir}")
        sys.exit(1)

    images = [p for p in assets_dir.iterdir() if p.suffix.lower() in SUPPORTED]
    if not images:
        print("没有找到图片文件。")
        sys.exit(0)

    print(f"找到 {len(images)} 张图片，开始压缩...\n")

    total_orig = total_new = 0
    saved_count = 0

    for img_path in sorted(images):
        orig, new = compress(img_path)
        total_orig += orig
        total_new += new
        delta = orig - new
        ratio = (1 - new / orig) * 100 if orig > 0 else 0
        if delta > 0:
            saved_count += 1
            print(f"  ✓ {img_path.name:<45} {orig/1024:>6.1f} KB → {new/1024:>6.1f} KB  (-{ratio:.0f}%)")
        else:
            print(f"  - {img_path.name:<45} {orig/1024:>6.1f} KB  (无需压缩)")

    total_saved = total_orig - total_new
    print(f"\n完成！共节省 {total_saved/1024:.1f} KB "
          f"({total_orig/1024:.1f} KB → {total_new/1024:.1f} KB，"
          f"{len(images)} 张中 {saved_count} 张被压缩)")


if __name__ == "__main__":
    main()
