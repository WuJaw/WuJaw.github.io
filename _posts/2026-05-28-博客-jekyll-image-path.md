---
layout: post
title: "jekyll-image-path"
date: 2026-05-28
category: 博客
---

Typora 写 Markdown、Jekyll 生成网页，两者的图片路径解析机制不同，导致一个路径格式无法同时满足两端预览。记录下最终方案和配套脚本。

---

## 问题根源

Jekyll 构建时，文章页面生成在 `/posts/文章标题/index.html`，而 Markdown 源文件在 `_posts/` 目录下。两者的目录层级不同：

| 路径写法 | Typora 预览 | Jekyll 网页 |
|---|---|---|
| `![x](/assets/x.png)` | 不显示（找不到绝对路径） | 正常 |
| `![x](../assets/x.png)` | 正常 | 不显示（解析为 `/posts/assets/x.png`） |
| `<img src="/assets/x.png">` | 不显示 | 正常 |
| {% raw %}`{{ "/assets/x.png" \| relative_url }}`{% endraw %} | 不解析 Liquid 标签 | 正常 |

另外，Jekyll 以下划线 `_` 开头的目录（如 `_posts/assets/`）中的文件不会被打包到 `_site`，图片放进去线上也找不到。

**结论**：不存在一个路径格式同时满足 Typora 和 Jekyll，只能通过脚本切换。

---

## 图片存放位置

图片统一放在项目根目录的 `assets/` 下（不带 `_` 前缀，Jekyll 会原样复制到 `_site/assets/`）：

```
WuJaw.github.io/
├── assets/              # 图片存放目录
│   ├── image-xxx.png
│   └── ...
├── _posts/              # 文章 Markdown
└── change/              # 转换脚本
```

---

## 解决方案：双脚本切换

### 工作流

```
Typora 编辑 → push 前 → 网页发布
```

- **编辑阶段**：图片路径为 `![desc](../assets/xxx.png)`，Typora 能正常预览
- **发布阶段**：路径转为 `<img src="/assets/xxx.png">`，网页能正常显示
- **继续编辑**：路径转回 `![desc](../assets/xxx.png)`

### 工具目录

```
change/
├── typora.bat          # 双击：转回 Typora 预览格式
├── web.bat             # 双击：转为网页发布格式
├── fix_img_path.py     # 转为网页格式
└── fix_img_reverse.py  # 转为 Typora 格式
```

### `fix_img_path.py` — 发布前转换

功能：
- 将所有 `![desc](路径)` 替换为 `<img src="/assets/xxx.png" alt="desc">`
- 如果图片不在 `assets/` 目录，自动查找并复制过去（支持相对路径、绝对路径、全局搜索）
- 已是正确格式的自动跳过

```bash
# 处理所有文章
python fix_img_path.py

# 只处理指定文件
python fix_img_path.py "_posts/某文章.md"
```

### `fix_img_reverse.py` — 编辑前还原

功能：
- 将 `<img src="/assets/xxx.png" alt="desc">` 转回 `![desc](../assets/xxx.png)`
- 将 `![desc](/assets/xxx.png)` 转回 `![desc](../assets/xxx.png)`

```bash
# 处理所有文章
python fix_img_reverse.py
```

---

## Typora 设置建议

在 Typora 偏好设置中配置图片自动复制：

1. 打开 **偏好设置 → 图像**
2. **插入图片时** 选择 **复制到指定路径**
3. 填入：`../assets`
4. 勾选 **优先使用相对路径**

这样粘贴截图时 Typora 自动把图片存到 `assets/` 并使用 `../assets/xxx.png` 路径引用，无需手动拖动图片文件。

---

## 完整操作流程

1. 用 Typora 正常写文章，粘贴截图
2. 写完后双击 `change/typora.bat`（确保路径是 Typora 格式）
3. git add、commit、push 之前，双击 `change/web.bat`
4. 脚本自动完成路径转换和图片复制，网页和 Typora 各取所需

---

## 踩坑记录

- `_posts/assets/` 里的图片不会被 Jekyll 发布，必须放根目录的 `assets/`
- {% raw %}`{{ relative_url }}`{% endraw %} Liquid 标签 Typora 完全无法识别，没有配置能解决
- Typora 不支持 `typora-root-url` 设置 Image Root Folder（部分旧版没有这个选项）
- `baseurl` 为空时 `/assets/xxx.png` 在网页端直接可用，无需 `relative_url` filter
