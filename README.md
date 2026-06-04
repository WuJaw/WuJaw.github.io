# WuJaw.github.io

Jekyll + GitHub Pages 个人博客，配套自动化脚本。

---

## 一键部署（推荐）

写完文章，双击 **`deploy.bat`**，自动完成三步：

```
[1/3] 添加 Front Matter → [2/3] 图片路径转 Web 格式 → [3/3] Git 提交推送
```

如果电脑没装 Python，脚本会提示后退出，不会执行任何操作。

---

## 分步操作（可选）

也可以单独跑每一步，方便调试。

### ① 写文章

在 `_posts/` 目录下新建 `.md` 文件，文件名格式：

```
YYYY-MM-DD-分类-标题.md
```

例如：`2026-06-04-博客-jekyll-autocommit.md`

不需要手写 front matter，第②步会自动生成。

---

### ② 添加 Front Matter

双击根目录下的 **`add_fm.bat`**，自动根据文件名生成 front matter：

```
双击 → 扫描 _posts/ → 写入 layout/title/date/category
```

生成内容：

```yaml
---
layout: post
title: "jekyll-autocommit"
date: 2026-06-04
category: 博客
---
```

已有 front matter 的文件会被强制覆盖，始终和文件名保持一致。

---

### ③ Typora 写作 → 转 Web 路径

在 Typora 里写文章时，图片用相对路径插入才能实时预览：

```markdown
![截图](../assets/screenshot.png)
```

但这个路径 push 到 GitHub Pages 后会 404。双击 **`web.bat`**，自动做两件事：

**第一，转换图片引用**

```
![截图](../assets/screenshot.png)
          ↓
![截图](../assets/screenshot.png)

所有文章里的 `![xxx](../assets/...)` 全部替换成 `<img src="/assets/...">`，GitHub Pages 上就能正确加载了。
```



**第二，自动搜集散落的图片**

如果文章引用的图片不在 `assets/` 目录下（比如还在桌面、下载文件夹里），脚本会自动找到它并复制到 `assets/`，不需要手动拖。

---

#### 继续编辑 → 转回 Typora 格式

push 完想继续用 Typora 编辑？双击 **`typora.bat`**，把路径转回去：

```
![截图](../assets/screenshot.png)  ← web.bat 写入的
                  ↓
![截图](../assets/screenshot.png)            ← typora.bat 还原
```

Typora 继续能预览图片。下次 push 前再跑 `web.bat`（`deploy.bat` 里已包含）。

---

### ④ 一键提交推送

双击 **`autocommit.bat`**，自动完成：

```
git add . → git commit（带变更明细） → git push
```

终端会显示本次提交了哪些文件、commit hash 是什么，一目了然。

---

## 完整工作流

```
写文章（Typora）
   ↓
双击 deploy.bat         ← 一键：add_fm → web → autocommit
   ↓
GitHub Pages 自动构建
```

或者分步执行：

```
双击 add_fm.bat         ← 补齐 front matter
   ↓
双击 web.bat            ← 图片路径转 web 格式
   ↓
双击 autocommit.bat     ← add + commit + push
```

---

## 脚本说明

| 文件 | 位置 | 作用 |
|------|------|------|
| **`deploy.bat`** | 根目录 | **一键部署**：add_fm → web → autocommit，自动检测 Python |
| `add_fm.bat` | 根目录 | 根据文件名批量写入 front matter |
| `web.bat` | 根目录 | 图片路径转 web 格式，自动全盘搜索并复制散落图片到 `assets/` |
| `autocommit.bat` | 根目录 | git add + commit + push 一条龙 |
| `typora.bat` | 根目录 | web 格式 → Typora 格式（pull 后恢复本地预览） |
| `python/` | 子目录 | 以上 bat 调用的 Python 脚本 |
| `tools/` | 子目录 | 第三方工具（es.exe，Everything 命令行搜索） |

---

## 图片全盘搜索

`web.bat` 不只做路径转换，还包含**五层图片搜索**。如果文章引用的图片不在 `assets/` 里（比如还在桌面、截图文件夹），脚本会自动找到并复制过来：

| 优先级 | 搜索范围 | 方法 |
|--------|---------|------|
| ① | `assets/` | 直接检查 |
| ② | 项目目录 | `os.walk` |
| ③ | 桌面、下载、图片、文档 | `os.walk` |
| ④ | 全盘 | Everything `es.exe`（秒级） |
| ⑤ | 全盘兜底 | `os.walk` ~ 目录（分钟级） |

第 ④ 层需要安装 [Everything](https://www.voidtools.com/) 搜索工具，`es.exe` 已放在 `tools/` 目录。不装也不影响使用，只是兜底搜索慢一些。

---

## 复制到其他 Jekyll 工程

把整个 `python/`、`tools/` 目录和 `deploy.bat`（以及单独用到的 `typora.bat`）拷过去即可，不需要安装任何依赖（只用 Python 标准库）。

确保目标工程有 `_posts/` 目录，且文章命名符合 `YYYY-MM-DD-分类-标题.md` 格式。
