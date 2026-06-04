---
layout: post
title: "GitHub Pages Fork 部署"
date: 2026-05-29
category: 博客
---

这篇记录如何把别人的 GitHub Pages 博客仓库复制一份，改成自己的站点。不涉及 Fork 之后提 PR 回源仓库，纯粹是拿过来当自己的起点。

## 前提

- 有一个 GitHub 账号
- 对方仓库是公开的（public）
- 会用 git 基本命令

## 操作步骤

### 1. 克隆仓库

```bash
git clone https://github.com/用户名/用户名.github.io.git
cd 用户名.github.io
```

### 2. 切断与原仓库的关联

删掉原来的 remote，换成你自己的：

```bash
git remote remove origin
git remote add origin https://github.com/你的用户名/你的用户名.github.io.git
```

这一步之后，`git push` 就会推到你的仓库，而不是原作者的。

### 3. 在 GitHub 上创建同名仓库

在你的 GitHub 页面新建仓库，名称必须是 `你的用户名.github.io`（大小写敏感，GitHub 用户名全是小写）。

创建时 **不要**勾选 "Add a README"、"Add .gitignore"、选择 License —— 这些都别加，空仓库即可。

### 4. 推送代码

```bash
git push -u origin main
```

如果你的默认分支是 `master`：

```bash
git push -u origin master
```

### 5. 启用 GitHub Pages

进入仓库 → **Settings** → **Pages**：

- **Source**: Deploy from a branch
- **Branch**: `main`（或 `master`），目录选 `/ (root)`
- 点 **Save**

等一两分钟，访问 `https://你的用户名.github.io` 就能看到页面了。

### 6. 修改 `_config.yml`

把里面的个人信息改成你自己的：

```yaml
title: 你的博客名
description: 你的描述
url: "https://你的用户名.github.io"
baseurl: ""
```

### 7. 删掉对方的文章，开始写自己的

`_posts/` 目录下是原作者的 Markdown 文章，删掉或保留参考都可以。写新文章按 Jekyll 格式放进去就行。

## 注意事项

| 问题 | 说明 |
|---|---|
| **LICENSE** | 复刻前看一眼原仓库的 LICENSE 文件。MIT / Apache 2.0 等宽松协议可以直接用，GPL 类可能有限制 |
| **个人信息泄露** | `_config.yml` 和 `CNAME` 文件里可能有原作者的域名、邮箱等，记得改掉 |
| **Google Analytics 等** | 原站可能有统计代码、评论系统配置，不需要的话删掉对应 JS |
| **自定义域名** | 如果你有自己的域名，新建 `CNAME` 文件写域名，再去 DNS 配 CNAME 指向 `你的用户名.github.io` |
| **GitHub Actions** | 如果有 `.github/workflows/` 目录，看看里面是什么。Jekyll 一般用 GitHub 内置构建就行，不需要额外 workflow |

## 和 Fork 的区别

GitHub 页面右上角点 **Fork** 也行，但 Fork 会在你的仓库页显示 "forked from xxx"，而且默认提 PR 会指回原仓库。如果你只是想要一个干净的副本当自己的博客起点，按上面的方法 `remote remove` 最干净。

## 总结

```bash
# 五行命令搞定
git clone https://github.com/原作者/原作者.github.io.git
cd 原作者.github.io
git remote remove origin
git remote add origin https://github.com/你的用户名/你的用户名.github.io.git
git push -u origin main
```

剩下的就是改配置、删旧文、写新文，一个属于自己的 Jekyll 博客就搭好了。
