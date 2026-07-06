# WuJaw.github.io

Jekyll + GitHub Pages 个人博客，配套自动化脚本和在线工具。

---

## 目录结构

```
WuJaw.github.io/
│
├── _config.yml              # Jekyll 配置
│
├── _layouts/                # 主题布局（极简白底，900px 宽）
│   ├── default.html         #   通用布局（含全部 CSS、搜索框、暗号解锁逻辑）
│   └── post.html            #   文章页布局（标题 + 日期 + TOC 侧边目录 + 代码复制）
│
├── index.html               # 首页（分类卡片 + 实时搜索 + 暗号解锁）
│
├── _posts/                  # 博客文章（Markdown，共 11 篇）
│
├── assets/                  # 静态资源（图片统一放这里，含文章配图）
│
├── tools/                   # 在线工具 + 第三方依赖
│   ├── efr32容量剩余计算.html #  EFR32 芯片 Flash / RAM 容量估算
│   ├── es.exe               #   Everything 命令行搜索工具
│   └── extract.py           #   辅助脚本
│
├── python/                  # 自动化脚本（Python 标准库，零 pip 依赖）
│   ├── add_front_matter.py  #   根据文件名补齐 Jekyll Front Matter
│   ├── auto_number_headings.py # 标题自动编号（h2 → 1. / h3 → 1.1）
│   ├── autocommit.py        #   Git add + commit + push
│   ├── compress_images.py   #   图片压缩
│   ├── download_csdn_images.py # CSDN 文章图片下载
│   ├── export_projects.py   #   项目导出
│   ├── fix_img_path.py      #   图片路径转 Web 格式（含全盘搜索）
│   ├── fix_img_reverse.py   #   Web 路径转 Typora 格式
│   ├── launcher.py          #   工具启动器
│   ├── submit_work_hours.py #   工时自动填报
│   ├── wch_isp_gui_enhanced.py # CH592 ISP 烧录 GUI
│   └── part no.bin          #   CH592 烧录数据文件
│
├── add_fm.bat               # 补齐 Front Matter
├── auto_number.bat          # 标题自动编号
├── autocommit.bat           # Git add + commit + push
├── compress.bat             # 图片压缩
├── git_push.bat             # ★ 一键部署（auto_number → add_fm → fix_img → autocommit）
├── git_reset.bat            # Git 版本回退
├── git_rollback.bat         # Git 回滚
├── typora.bat               # 图片转 Typora 预览格式
├── web.bat                  # 图片转网页格式
│
└── README.md
```

---

## 1. `_config.yml`

Jekyll 核心配置：

- **主题**：`jekyll-theme-primer`（仅声明以满足 GitHub Pages 要求，实际布局由 `_layouts/` 覆盖）
- **Markdown**：kramdown + GFM 输入模式
- **语法高亮**：Rouge（Jekyll 内置），Tomorrow Night Eighties 主题
- **文章 URL**：`/posts/:title/`
- **功能开关**：搜索框、站点目录、文章 TOC、代码复制按钮，可通过 `features` 集中控制
- **私密分类**：`secret_categories` 列出「编程」「博客」两个分类，需在搜索框输入暗号后才显示，支持 localStorage 持久化

---

## 2. `_layouts/` 主题布局

两个 Jekyll Liquid 模板：

| 文件 | 作用 |
|------|------|
| `default.html` | 全站通用骨架，含全部 CSS（极简白底，系统默认中文字体，900px 宽），搜索框，暗号解锁逻辑 |
| `post.html` | 文章页专用布局，继承 default，渲染正文 + Rouge 语法高亮 + 右侧 TOC 目录 + 代码块复制按钮 |

没有页头 logo、页脚、导航栏、暗色模式。

---

## 3. `index.html` 首页

单页分类卡片视图。Jekyll 构建后按 `category` 分组展示所有文章。顶部搜索框支持：

- **实时过滤**：输入即匹配文章标题和分类名
- **空分类隐藏**：某分类下全部过滤掉则卡片消失
- **暗号解锁**：输入特定暗号切换 `secret_categories` 文章的显示/隐藏，解锁状态存 localStorage

---

## 4. `_posts/` 博客文章

文件名格式：`YYYY-MM-DD-分类-标题.md`，Front Matter 声明 `layout: post`。

当前 **11 篇**，覆盖以下分类：

| 分类 | 篇数 | 内容 |
|------|------|------|
| **操作手册** | 5 | A1 蜂巢基站、OTA 升级、数分微站出厂测试、CE/SRRC 认证测试、CH592 Part No 烧录 |
| **编程** | 3 | BW16 驱动与处理逻辑、CH592 开发调试流程、Python 工时自动化工具链 |
| **工具** | 2 | Git 自动提交脚本与常用仓库地址、常用工具下载地址 |
| **博客** | 1 | GitHub Pages & Jekyll 博客搭建全记录 |

其中「编程」和「博客」属于私密分类，需暗号解锁。

### 图片处理

Typora 写作时用 `![desc](../assets/xxx.png)` 预览，push 前运行 `web.bat` 转为 `<img src="/assets/xxx.png">`。继续编辑用 `typora.bat` 转回。图片统一放 `assets/`。

图片搜索脚本支持五层全盘查找：`assets/` → 项目目录 → 常用文件夹（桌面/下载/图片/文档）→ Everything 秒搜 → 全盘兜底。

---

## 5. `python/` 自动化脚本

全部用 Python 标准库编写，零 pip 依赖。由根目录 `.bat` 文件调用。

### 核心脚本

| 脚本 | 功能 |
|------|------|
| `add_front_matter.py` | 扫描 `_posts/`，根据文件名自动写入 Front Matter（layout / title / date / category），幂等操作 |
| `auto_number_headings.py` | 自动给 h2+ 标题编号：h2 → 1. / h3 → 1.1 / h4 → 1.1.1，自动剥除已有编号 |
| `autocommit.py` | `git add .` → `git commit` → `git push`，commit 信息含变更明细 |
| `fix_img_path.py` | Typora 相对路径 → Web 绝对路径，含五层全盘图片搜索 |
| `fix_img_reverse.py` | Web 路径 → Typora 相对路径（继续编辑用） |
| `compress_images.py` | 图片压缩 |

### 辅助脚本

| 脚本 | 功能 |
|------|------|
| `download_csdn_images.py` | CSDN 文章图片下载 |
| `export_projects.py` | 项目导出 |
| `launcher.py` | 工具启动器 |
| `submit_work_hours.py` | 工时自动填报 |
| `wch_isp_gui_enhanced.py` | CH592 ISP 烧录 GUI |
| `part no.bin` | CH592 烧录数据文件 |

---

## 6. 根目录 .bat 启动脚本

双击即可运行：

| 文件 | 功能 |
|------|------|
| `add_fm.bat` | 补齐 Front Matter |
| `auto_number.bat` | 标题自动编号 |
| `autocommit.bat` | 单独 git add + commit + push |
| `compress.bat` | 图片压缩 |
| `git_push.bat` | ★ 一键部署（auto_number → add_fm → fix_img → autocommit） |
| `git_reset.bat` | Git 版本回退 |
| `git_rollback.bat` | Git 回滚 |
| `typora.bat` | 图片路径还原为 Typora 格式 |
| `web.bat` | 图片路径转为网页格式 |

---

## 完整工作流

```
Typora 写文章（Markdown，图片相对路径）
        │
        ▼
web.bat              → 图片转 Web 路径（含全盘搜索散落图片）
        │
        ▼
git_push.bat         → ★ 一键部署
                        ├─ 标题自动编号
                        ├─ 补齐 Front Matter
                        ├─ 图片路径确认（fix_img_path）
                        └─ git add + commit + push
        │
        ▼
GitHub Pages 自动构建部署（1–2 分钟）
        │
        ▼
继续编辑？双击 typora.bat 还原路径
```
