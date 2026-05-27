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

已删除：`articles.html`、`about.html`。导航栏只保留主题切换按钮。

## 写文章规范

- 文件放在 `_posts/` 目录
- 命名格式：`YYYY-MM-DD-标题.md`
- Front Matter 必填：`layout: post`、`title`、`date`

## 设计风格

白底简洁极简风，字体 -apple-system / PingFang SC / Microsoft YaHei，最大宽度 720px，全部样式集中在 `_layouts/default.html`。
