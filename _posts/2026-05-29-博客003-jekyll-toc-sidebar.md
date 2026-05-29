---
layout: post
title: "Jekyll 博客添加侧边文章大纲：纯前端实现方案"
date: 2026-05-29
category: 博客搭建
---

给文章页加一个侧边悬浮大纲（TOC），自动扫描 h2/h3 生成目录，点击平滑跳转，滚动时高亮当前章节。不引入任何第三方库，纯 HTML + CSS + JS 搞定。

---

## 效果

| 功能 | 说明 |
|---|---|
| 自动扫描 | JS 检测 `.post-content` 里所有 h2 / h3 |
| 平滑跳转 | 点击目录项滚到对应标题处 |
| 滚动高亮 | 当前阅读位置的标题加粗显示 |
| 层级缩进 | h3 比 h2 缩进 12px，层次分明 |
| 窄屏隐藏 | 浏览器宽度 ≤ 1160px 时 TOC 自动消失 |
| 空文章不自嗨 | 标题少于 2 个时整个 TOC 不渲染 |

---

## 文件改动

只改两个文件：

| 文件 | 改动 |
|---|---|
| `_layouts/default.html` | 新增 `.toc-panel` 相关 CSS |
| `_layouts/post.html` | 新增 `<nav>` 标签 + JS 逻辑 |

首页完全不受影响，TOC 只在 `post` 布局里加载。

---

## default.html：CSS 样式

在 `_layouts/default.html` 的 `<style>` 块末尾（响应式代码之前）加入：

```css
/* ========== 文章大纲 TOC ========== */
.toc-panel {
  position: fixed;
  top: 60px;
  /* 定位到正文左侧 20px 处 */
  right: calc(50% + 380px);
  width: 200px;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
  font-size: var(--fs-small);
  line-height: 1.6;
  scrollbar-width: thin;
  scrollbar-color: var(--line) transparent;
}

.toc-panel::-webkit-scrollbar { width: 3px; }
.toc-panel::-webkit-scrollbar-track { background: transparent; }
.toc-panel::-webkit-scrollbar-thumb { background: var(--line); border-radius: 2px; }

.toc-title {
  font-size: var(--fs-meta);
  font-weight: 700;
  color: var(--quiet);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--line);
}

.toc-list { list-style: none; padding: 0; margin: 0; }

.toc-list a {
  display: block;
  padding: 3px 0;
  color: var(--quiet);
  text-decoration: none;
  transition: color 0.15s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.toc-list a:hover { color: var(--ink); }

.toc-list .toc-h3 > a {
  padding-left: 12px;
  font-size: var(--fs-meta);
}

.toc-list a.active {
  color: var(--ink);
  font-weight: 600;
}

@media (max-width: 1160px) {
  .toc-panel { display: none; }
}
```

**定位计算**：正文 `max-width: 720px` + 居中，左边缘在 `50% - 360px` 位置。TOC 宽 200px，通过 `right: calc(50% + 380px)` 让 TOC 右边缘落在正文左边缘外侧 20px 处。

---

## post.html：HTML + JS

替换 `_layouts/post.html` 为以下内容：

```html
---
layout: default
---
<div class="post-header">
  <h1>{{ page.title }}</h1>
  <span class="post-meta">{{ page.date | date: "%Y年%-m月%-d日" }}</span>
</div>

<div class="post-content">
  {{ content }}
</div>

<!-- 右侧大纲 TOC -->
<nav class="toc-panel" id="toc-panel" aria-label="文章大纲"></nav>

<script>
(function () {
  var panel = document.getElementById('toc-panel');
  var content = document.querySelector('.post-content');
  if (!panel || !content) return;

  var headings = Array.from(content.querySelectorAll('h2, h3'));
  if (headings.length < 2) { panel.style.display = 'none'; return; }

  headings.forEach(function (h, i) {
    if (!h.id) h.id = 'heading-' + i;
  });

  var html = '<div class="toc-title">目录</div><ul class="toc-list">';
  headings.forEach(function (h) {
    var cls = h.tagName === 'H3' ? ' class="toc-h3"' : '';
    var text = h.textContent.trim();
    html += '<li' + cls + '><a href="#' + h.id + '">' + text + '</a></li>';
  });
  html += '</ul>';
  panel.innerHTML = html;

  var links = Array.from(panel.querySelectorAll('a'));

  function onScroll() {
    var scrollY = window.scrollY;
    var active = null;
    for (var i = headings.length - 1; i >= 0; i--) {
      if (headings[i].getBoundingClientRect().top + scrollY - 80 <= scrollY) {
        active = i;
        break;
      }
    }
    links.forEach(function (a, i) {
      a.classList.toggle('active', i === active);
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  links.forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      var target = document.getElementById(a.getAttribute('href').slice(1));
      if (target) {
        window.scrollTo({
          top: target.getBoundingClientRect().top + window.scrollY - 70,
          behavior: 'smooth'
        });
      }
    });
  });
})();
</script>
```

---

## JS 逻辑解析

### 1. 收集标题

从 `.post-content` 中 `querySelectorAll('h2, h3')` 拿到所有二级和三级标题。少于 2 个直接隐藏面板。

### 2. 补 id

如果某个标题没有 `id` 属性，自动补上 `heading-0`、`heading-1`……这样才能 `#` 锚点跳转。

### 3. 构建目录

遍历标题数组，拼接 `<ul>` 列表，h3 加上 `.toc-h3` 类实现缩进。

### 4. 滚动高亮

监听 `scroll` 事件，从最后一个标题往前找，第一个 `getBoundingClientRect().top <= 80` 的就是当前阅读位置，对应的 TOC 链接加上 `.active`。

### 5. 平滑跳转

拦截 `<a>` 点击，计算目标元素位置，`window.scrollTo` 加 `behavior: 'smooth'`，再留 70px 顶部间距防止被遮挡。

---

## 部署

push 到 GitHub 后 Pages 自动编译，跟改 CSS 一样零额外步骤。唯一要注意的是文章如果纯靠 h3 起手（没有 h2），TOC 里同样能正常展现，逻辑上 h2 和 h3 平等扫描。
