---
layout: post
title: "浏览器登录后获取Cookie"
date: 2026-06-09
category: python
---

## 1 步骤

1. **浏览器登录目标系统**
2. **F12 打开开发者工具** → 点 `Network`（网络）标签
3. **随便点一下页面**，触发一个请求（比如刷新列表、翻页）
4. **左侧点一个请求** → 右侧点 `Headers`（标头）
5. **往下滚找到 `Request Headers`** → 复制 `Cookie:` 后面的整串值

![F12 Network 面板获取 Cookie](/assets/images/cookie-devtools.png)

完事。

## 2 注意

不要用 `copy(document.cookie)`，它拿不到 HttpOnly 的 Cookie，复制出来是不完整的。F12 Network 里看到的才是完整的。
