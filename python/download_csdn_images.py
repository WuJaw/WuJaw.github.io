import re
import urllib.request
import os
import hashlib

md_path = r"C:\Users\wuergou\Desktop\WuJaw.github.io\_posts\2026-06-16-操作手册-昂科专用蓝牙接收设备操作步骤.md"
assets_dir = r"C:\Users\wuergou\Desktop\WuJaw.github.io\assets"

# 读取 markdown
with open(md_path, "r", encoding="utf-8") as f:
    content = f.read()

# 匹配所有 CSDN 图片链接
# 格式: ![xxx](https://i-blog.csdnimg.cn/blog_migrate/xxxx.png#pic_center) 或 ![...](https://...)
urls = re.findall(r'!\[.*?\]\((https://i-blog\.csdnimg\.cn/blog_migrate/[^)]+)\)', content)

print(f"找到 {len(urls)} 张 CSDN 外链图片")

for i, url in enumerate(urls):
    # 清理 URL（去掉 #pic_center 等后缀）
    clean_url = re.sub(r'#.*$', '', url)
    # 用 URL 的 hash 生成唯一文件名
    filename = "csdn_" + hashlib.md5(clean_url.encode()).hexdigest()[:8] + ".png"
    save_path = os.path.join(assets_dir, filename)

    if os.path.exists(save_path):
        print(f"[{i+1}/{len(urls)}] 已存在: {filename}")
    else:
        try:
            req = urllib.request.Request(clean_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://blog.csdn.net/"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            with open(save_path, "wb") as f:
                f.write(data)
            print(f"[{i+1}/{len(urls)}] 下载成功: {filename} ({len(data)} bytes)")
        except Exception as e:
            print(f"[{i+1}/{len(urls)}] 下载失败: {clean_url} -> {e}")
            continue

    # 替换链接：Markdown 图片语法 -> HTML <img> 标签
    escaped = re.escape(url)
    new_tag = f'<img src="/assets/{filename}" alt="csdn_{filename}">'
    content = re.sub(r'!\[.*?\]\(' + escaped + r'\)', new_tag, content)

# 写回文件
with open(md_path, "w", encoding="utf-8") as f:
    f.write(content)

print("\n替换完成！")
