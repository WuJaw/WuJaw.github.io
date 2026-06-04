# WuJaw.github.io

Jekyll + GitHub Pages 个人博客，配套自动化脚本和在线工具。

---

## 目录结构

```
WuJaw.github.io/
│
├── _config.yml              # Jekyll 配置
│
├── _layouts/                # 主题布局（极简白底，720px 宽）
│   ├── default.html         #   通用布局（含全部 CSS、搜索框）
│   └── post.html            #   文章页布局
│
├── index.html               # 首页（分类卡片 + 实时搜索）
│
├── _posts/                  # 博客文章（Markdown）
│   ├── *-定位-*.md           #   定位技术类
│   ├── *-博客-*.md           #   博客搭建系列
│   ├── *-工具-*.md           #   在线工具类
│   ├── *-送检-*.md           #   产品送检记录
│   ├── *-物联网-*.md         #   物联网技术类
│   ├── *-ADC验证-*.md        #   ADC 芯片验证
│   └── *-python-*.md         #   Python 自动化脚本
│
├── assets/                  # 静态资源（图片）
│   └── 操作步骤/img/         #   配图按文章分目录存放
│
├── tools/                   # 在线工具 + 第三方依赖
│   ├── CRC16校验工具.html    #   CRC16 Modbus 在线计算
│   ├── efr32容量剩余计算.html #  EFR32 芯片 Flash/RAM 容量估算
│   └── es.exe               #   Everything 命令行搜索工具
│
├── python/                  # 自动化脚本（Python 标准库，零依赖）
│   ├── add_front_matter.py   #   根据文件名补齐 Jekyll Front Matter
│   ├── fix_img_path.py       #   图片路径转 Web 格式 + 全盘搜索
│   ├── auto_number_headings.py # 标题自动编号（h2 → 1. / h3 → 1.1）
│   ├── fix_img_reverse.py    #   Web 路径转 Typora 格式
│   └── autocommit.py         #   Git add + commit + push
│
├── deploy.bat               # 一键部署（自动编号 → add_fm → web → autocommit）
├── add_fm.bat               # 单独执行：补齐 Front Matter
├── auto_number.bat          # 单独执行：标题自动编号
├── web.bat                  # 单独执行：图片转 Web 路径
├── typora.bat               # 单独执行：图片转 Typora 路径
├── autocommit.bat           # 单独执行：Git 提交推送
│
└── README.md
```

---

## 1. `_config.yml`

Jekyll 核心配置，指定主题、Markdown 引擎、语法高亮等。

```yaml
theme: jekyll-theme-primer
markdown: kramdown
kramdown:
  input: GFM
  syntax_highlighter: rouge
```

实际布局由 `_layouts/` 目录覆盖，不依赖远程主题。

---

## 2. `_layouts/` 主题布局

两个 Jekyll Liquid 模板，实现了整套博客外观：

| 文件 | 作用 |
|------|------|
| `default.html` | 全站通用框架，含全部 CSS（极简白底，-apple-system 字体，720px 宽），首页搜索框 |
| `post.html` | 文章页专用布局，继承 default，渲染 Markdown 正文 + Rouge 语法高亮 |

没有页头 logo、页脚、导航栏、暗色模式。一切从简。

---

## 3. `index.html` 首页

单页分类卡片视图。Jekyll 构建后按 `category` 分组展示所有文章，每张卡片列出该分类下的文章链接。顶部搜索框支持实时过滤（纯前端 JS，输入即过滤文章标题和分类名，空分类自动隐藏）。

---

## 4. `_posts/` 博客文章

文件名格式：`YYYY-MM-DD-分类-标题.md`，Front Matter 声明 `layout: post`。

按分类分组：

| 分类 | 内容 |
|------|------|
| **定位** | A1 系列蜂巢基站、蓝牙定位数据上行协议 |
| **博客** | Jekyll 搭建、图片路径、搜索、语法高亮、TOC 侧边栏、GitHub Pages Fork、Liquid 逃逸、图片全盘搜索 |
| **工具** | 在线工具合集 |
| **送检** | CE 检测、BG22 射频认证操作步骤 |
| **物联网** | SI446x 双路射频频率配置 |
| **ADC验证** | CS5556、CS1232 芯片验证 |
| **python** | Git 自动提交、Jekyll 自动添加 Front Matter |

### 写文章规范

- 文件放在 `_posts/`，命名符合 `YYYY-MM-DD-分类-标题.md`
- 只需写正文，Front Matter 由 `deploy.bat` 自动生成
- 图片在 Typora 中用相对路径 `![desc](../assets/xxx.png)` 插入，push 前脚本自动转换

### 图片方案

Typora 写作时用 `![desc](../assets/xxx.png)` 实时预览，push 前 `deploy.bat` 自动转为 `<img src="/assets/xxx.png" alt="desc">`。继续编辑用 `typora.bat` 转回。图片统一放在 `assets/`。

---

## 5. `assets/` 静态资源

所有文章引用的图片统一存放。子目录 `操作步骤/img/` 等按文章分组管理配图。

图片搜索脚本（`python/fix_img_path.py`）支持五层全盘查找——即使图片散落在桌面、下载文件夹也能自动搜到并复制过来。

---

## 6. `tools/` 在线工具 + 第三方依赖

### HTML 工具页面

Jekyll 构建后可直接通过 URL 访问的独立工具页：

| 文件 | 功能 |
|------|------|
| `CRC16校验工具.html` | CRC16 Modbus 在线计算器，输入 hex 自动出结果 |
| `efr32容量剩余计算.html` | EFR32 系列芯片 Flash / RAM 容量估算 |

### 第三方工具

| 文件 | 说明 |
|------|------|
| `es.exe` | [Everything](https://www.voidtools.com/) 命令行接口，`fix_img_path.py` 图片全盘搜索依赖此工具（可选） |

`tools/` 目录跟随项目分发，不依赖系统安装路径。

---

## 7. `python/` 自动化脚本

全部用 Python 标准库编写，零 pip 依赖。由根目录 `.bat` 文件调用。

| 脚本 | 功能 |
|------|------|
| `add_front_matter.py` | 扫描 `_posts/`，根据文件名自动写入 `layout`、`title`、`date`、`category` |
| `auto_number_headings.py` | 自动给 h2+ 标题编号：h2 → 1. / h3 → 1.1 / h4 → 1.1.1，自动去除已有编号 |
| `fix_img_path.py` | Typora 相对路径 → Web 绝对路径；含五层全盘图片搜索（支持 Everything 秒搜） |
| `fix_img_reverse.py` | Web 路径 → Typora 相对路径（push 后继续本地编辑用） |
| `autocommit.py` | `git add .` → `git commit`（带变更明细） → `git push` |

### 图片搜索五层策略

`fix_img_path.py` 查找文章引用的图片时，按以下优先级逐层搜索：

| 优先级 | 范围 | 方法 | 速度 |
|--------|------|------|------|
| ① | `assets/` | 直接 `isfile` | 瞬间 |
| ② | 项目目录 | `os.walk` | 快 |
| ③ | 桌面、下载、图片、文档 | `os.walk` | 几秒 |
| ④ | 全盘 | Everything `es.exe` | 秒级 |
| ⑤ | 全盘兜底 | `os.walk` ~ 目录 | 分钟级 |

第 ④ 层需要安装 [Everything](https://www.voidtools.com/)，不装也能用（自动降级到第 ⑤ 层）。

---

## 8. 根目录 .bat 启动脚本

双击即可运行，适合不习惯命令行的场景。

| 文件 | 功能 |
|------|------|
| **`deploy.bat`** | **一键部署**：① 标题自动编号 → ② 补齐 Front Matter → ③ 图片转 Web 路径 → ④ Git 提交推送 |
| `add_fm.bat` | 单独补齐 Front Matter |
| `auto_number.bat` | 单独执行标题自动编号（h2 → 1. / h3 → 1.1） |
| `web.bat` | 单独执行图片路径转换 |
| `typora.bat` | 单独执行图片路径还原 |
| `autocommit.bat` | 单独执行 Git 提交推送 |

`deploy.bat` 启动时自动检测 Python 是否可用，不可用则提示退出。

---

## 完整工作流

```
Typora 写文章（Markdown，图片相对路径）
        │
        ▼
双击 deploy.bat
   ├── [1/3] add_front_matter   → 补齐 YAML 头部
   ├── [2/3] fix_img_path       → 图片转 Web 路径，全局搜索散落图片
   └── [3/3] autocommit         → git add + commit + push
        │
        ▼
GitHub Pages 自动构建部署
        │
        ▼
继续编辑？双击 typora.bat 还原路径
```

---

## 复制到其他 Jekyll 工程

把以下目录拷到目标工程根目录即可，不需要装任何依赖：

```
python/         ← 自动化脚本
tools/          ← 在线工具 + es.exe
deploy.bat      ← 一键部署入口
typora.bat      ← 可选：路径还原
```

要求：
- 目标工程有 `_posts/` 目录
- 文章命名符合 `YYYY-MM-DD-分类-标题.md`
- 系统已安装 Python 3 且可在命令行调用 `python`
