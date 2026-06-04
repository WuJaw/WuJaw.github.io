---
layout: post
title: "jekyll-liquid-escape111"
date: 2026-06-04
category: 博客
---

写 Jekyll 博客教程时，代码块里展示的 Liquid 模板代码被 Jekyll 当成真实指令执行了，导致 GitHub Pages 构建静默失败——日志在渲染某篇文章时截断，没有任何报错。

---

## 现象

`git push` 后 GitHub Actions 构建失败，日志长这样：

```
Rendering: _posts/2026-05-29-博客-jekyll-search.md
Pre-Render Hooks: _posts/2026-05-29-博客-jekyll-search.md
Rendering Liquid: _posts/2026-05-29-博客-jekyll-search.md
Rendering Markup:
```

然后日志就断掉了——没有 error 行，没有堆栈信息，构建直接超时或 OOM。

一开始怀疑是主题配置问题，折腾了一圈 `theme: null`、`theme: jekyll-theme-primer`，最后发现和主题没关系。

---

## 根因

**Jekyll 的处理顺序是：Liquid 模板引擎 → kramdown Markdown 渲染。**

代码块里的 {% raw %}`{%` `%}` 和 `{{` `}}`{% endraw %} 会被 Liquid 先抓走执行，kramdown 收到的已经是执行后的结果，根本不是"代码示例"了。

---

## 具体逃逸：两处

### 第一处：`jekyll-build` 文章

文章的代码块里写了首页模板的 Liquid 循环：

{% raw %}
```html
{% for post in site.posts %}
<li class="post-item">
  <a href="{{ post.url }}">{{ post.title }}</a>
  <span>{{ post.date | date: "%Y年%-m月%-d日" }}</span>
</li>
{% endfor %}
```
{% endraw %}

`{% raw %}`{% for post in site.posts %}`{% endraw %}` 被 Jekyll 真的执行，渲染时遍历了所有文章的元数据，往页面注入了一大堆 HTML 链接。

### 第二处：`jekyll-toc-sidebar` 文章

展示 `post.html` 布局代码的代码块里有：

{% raw %}
```html
<div class="post-content">
  {{ content }}
</div>
```
{% endraw %}

`{% raw %}{{ content }}{% endraw %}` 被 Jekyll 真的执行，它会递归渲染当前文章自身——把自己嵌进自己，再嵌进自己……直接死循环，这就是日志无声截断的原因。

---

## 正确写法

在代码块的外层用 raw 标签包裹。以 jekyll-build 中的循环为例：

源码（发送给 Jekyll 前）：

{% raw %}
```liquid
{% raw %}
```html
{% for post in site.posts %}
<li class="post-item">
  <a href="{{ post.url }}">{{ post.title }}</a>
  <span>{{ post.date | date: "%Y年%-m月%-d日" }}</span>
</li>
{% endfor %}
```
{% {% endraw %}{% raw %}endraw %}
```
{% endraw %}

Jekyll 处理时：最外层的 raw 让中间所有 Liquid 标签全部原样输出。最终页面里渲染出来的就是一份干净的 Liquid 模板示例，不会被当成真实指令执行。

一句话记住：**只要文章正文里出现了 Liquid 模板标签，就用 raw 标签包起来。**

---

## 避坑：raw 不能嵌套

Liquid 的 raw 模式不支持嵌套——第一个 raw 闭合标签就会结束全部 raw 层，没有"层数"的概念。

这意味着当你的文章源码自身就包含 raw 标签时（比如本文），不能简单地在最外层包一个 raw 了事——因为文章内部展示的 raw 闭合标签会提前关闭外层 raw，导致后面独立的 raw 闭合标签报错。

解决办法是把 raw 标签拆成两半，用两个普通 raw 块夹住中间真正的代码部分：

第一段 raw 输出代码块开头和 raw 开始标签；第二段 raw 包裹要展示的 Liquid 代码（保证不被执行）；最后用 Liquid 变量输出 raw 闭合标签。整个过程拆成三次 raw 块 + 一次变量输出，核心思路是让 Jekyll 永远看不到一个完整的内部 raw 闭合标签——要么在 raw 块外面用变量拼出来，要么在 raw 块里面拆散写。

---

## 总结

| 问题 | 原因 | 修复 |
|---|---|---|
| 构建日志截断、无报错 | 代码块里的 Liquid 被真实执行 | 用 raw 标签包裹 |
| content 变量导致构建超时 | 递归渲染自身 | 同上 |
| for 循环污染输出 | 遍历全部文章注入 HTML | 同上 |

核心规则很简单：**只要文章里包含 Liquid 模板标签，就用 raw 标签包起来。** 唯一的例外是当文章自身就是要讲解 raw 标签的——这时候用分段 raw 的技巧来处理。
