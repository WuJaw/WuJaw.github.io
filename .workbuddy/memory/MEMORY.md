# WuJaw.github.io 项目记忆

## 博客结构

已于 2026-05-27 启用 Jekyll，当前为单页结构（分类索引即首页）：

```
WuJaw.github.io/
├── _config.yml          # Jekyll 配置
├── _layouts/
│   ├── default.html     # 通用布局（含全部 CSS）
│   └── post.html        # 文章布局
├── _posts/              # Markdown 文章放这里
├── posts/               # 旧 HTML 文章（保留）
└── index.html           # 首页（分类卡片视图）
```

已删除：`articles.html`、`about.html`。已移除页头 logo、页脚、导航栏、主题切换。

## 写文章规范

- 文件放在 `_posts/` 目录
- 命名格式：`YYYY-MM-DD-标题.md`
- Front Matter 必填：`layout: post`、`title`、`date`

## 设计风格

白底简洁极简风，字体 -apple-system / PingFang SC / Microsoft YaHei，最大宽度 720px，全部样式集中在 `_layouts/default.html`。已移除页头、页脚、导航栏和暗色模式。代码块含 Rouge 语法高亮（Tommorow Night Eighties 主题）。

## 搜索功能

首页顶部有纯前端搜索框，输入文字实时过滤文章标题和分类名，空分类卡片自动隐藏。

## 隐藏文章功能

`_config.yml` 中 `secret_categories` 列出需要暗号解锁的分类（原"博客1"已归入此类）。前端在搜索框输入暗号（默认 `open-sesame`）切换解锁，存 localStorage。

已废弃 `hidden_categories`，统一为 `secret_categories`。文章 front matter 也可单独加 `secret: true`。

## 图片方案

Typora 写文章用 `![x](../assets/x.png)`，push 前用 `change/fix_img_path.py` 转为 `<img src="/assets/x.png">`，继续编辑用 `change/fix_img_reverse.py` 转回。图片统一放 `assets/` 目录。配套 `change/typora.bat` 和 `change/web.bat` 双击运行。
