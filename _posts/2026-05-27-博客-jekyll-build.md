---
layout: post
title: "jekyll-build"
date: 2026-05-27
category: 博客
---

把个人博客从纯 HTML 迁移到 Jekyll，顺便记录下整个流程和用到的工具，方便以后回顾。

---

## 目录结构

```
WuJaw.github.io/

├── _layouts/            # 页面模板
│   ├── default.html     # 通用布局（导航栏 + 页脚 + 全局 CSS）
│   └── post.html        # 文章布局（标题 + 日期 + 正文）
├── _posts/              # 所有文章放这里，Markdown 格式
├── assets				 # 博客图片都放到这里面来
├── change				 # 切换图片格式脚本
├── _config.yml          # Jekyll 核心配置
└── index.html           # 首页，Liquid 模板自动列出文章
```

---

## 配置流程

### 1. `_config.yml` - Jekyll 核心

这个是 GitHub Pages 识别 Jekyll 的关键文件，有了它就会自动编译：

```yaml
title: Wu-X
description: just as well
baseurl: ""
url: "https://wujaw.github.io"

markdown: kramdown        # Markdown 解析引擎
kramdown:
  input: GFM              # 兼容 GitHub Flavored Markdown
  hard_wrap: false

permalink: /posts/:title/  # 文章 URL 格式

exclude:                   # 排除不编译的文件
  - README.md

plugins:
  - jekyll-feed            # RSS 订阅
```

### 2. 布局模板

**`_layouts/default.html`** 是骨架：导航栏、页脚、所有 CSS 都在这里。其他页面继承它就完事了。

**`_layouts/post.html`** 是文章专用布局，在 default 的基础上加了标题区和日期展示：

```html
---
layout: default
---
<div class="post-header">
  <h1>{{ page.title }}</h1>
  <span>{{ page.date | date: "%Y年%-m月%-d日" }}</span>
</div>
<div class="post-content">
  {{ content }}
</div>
```

### 3. 首页改造

把原来手动加链接的 `<ul>` 改成 Liquid 循环：

```html
{% for post in site.posts %}
<li class="post-item">
  <a href="{{ post.url }}">{{ post.title }}</a>
  <span>{{ post.date | date: "%Y年%-m月%-d日" }}</span>
</li>
{% endfor %}
```

之后新增文章完全不用改首页，自动列出来。

---

## 工具链

| 工具 | 用途 |
|------|------|
| **Jekyll** | 静态站点生成器，GitHub Pages 原生支持 |
| **kramdown** | Markdown 渲染引擎，兼容 GFM 语法 |
| **Liquid** | Jekyll 模板语言，循环、条件、变量全靠它 |
| **GitHub Pages** | 免费托管，push 即部署 |
| **wincred** | Windows 凭据管理器，免密 git push |

---

## 写文章规范

1. 在 `_posts/` 下新建文件，命名：`YYYY-MM-DD-标题.md`
2. 文件开头必填 Front Matter：

```markdown
---
layout: post
title: "文章标题"
date: 2026-05-27
---

正文写在这里，标准的 Markdown 语法。
```

3. `git push` 后 GitHub Pages 自动编译部署，1-2 分钟生效

---

## 推送踩坑

Git Bash 环境下 push 时遇到 TTY 认证问题：

```
fatal: could not read Username for 'https://github.com': No such file or directory
```

**解决方案**：Git Bash 没有 `/dev/tty` 时无法弹出交互式认证，但 Windows 凭据管理器（wincred）可以读取缓存的 GitHub 密码：

```bash
git -c credential.helper=wincred push
```

如果 wincred 也没缓存，提前手动设置一次：

```bash
git config --global credential.helper wincred
```

---

## 设计风格

保持极简：白底、720px 最大宽度、系统默认中文字体（PingFang SC / Microsoft YaHei），所有样式集中在 `default.html` 里，不引入外部 CSS 框架。
