---
layout: post
title: "CH592 Part No 烧录工具"
date: 2026-06-12
category: python
---

## 1 背景

批量烧录 CH592 芯片时，每个芯片的 Part No（序列号）必须唯一。WCH 官方的 ISP 工具 `WCHISPTool_CH57x-59x.exe` 支持读取外部 `part no.bin` 文件作为序列号来源，但本身不具备自动递增功能。

手动改号效率极低，于是决定用 Python + tkinter 写一个辅助工具：
- 自动生成 4 字节 `part no.bin`
- 实时监控 ISP 工具的烧录结果
- 烧录成功一次，序列号自动 +1

这个工具从最初的 WCH ISP GUI 一路精简，最终只保留最核心的功能。

---

## 2 功能

### 2.1 Part No 生成规则

| 组成 | 长度 | 说明 |
|------|------|------|
| 前缀 | 3 位 HEX | 如 `87F` |
| 后缀 | 5 位十进制 | 如 `00001` |
| 组合值 | 8 位 HEX | `0x87F00001` |

前缀 + 后缀拼成一个 8 位十六进制值，写入 4 字节二进制文件 `part no.bin`。前缀代表产品批次，后缀是流水号。

### 2.2 字节序切换

WCH ISP 工具读取 `part no.bin` 时是大端序，但某些场景下可能需要小端。工具提供勾选框实时切换：

- **不勾选**：大端（Big Endian），如 `0x87F00001` → `87 F0 00 01`
- **勾选**：小端（Little Endian），如 `0x87F00001` → `01 00 F0 87`

### 2.3 窗体监控自动累加

核心自动化逻辑：

1. 每 **500ms** 读取一次 `WCHISPTool_CH57x-59x` 窗口及其子控件的文字
2. 用正则提取 `成功：X` 中的数字
3. **仅当数字增加时才累加**（变 0 或减少不触发）

这避免了以下误触发场景：
- ISP 工具启动时统计清零（`成功：0`）
- 窗口刷新导致同一数字重复出现
- 失败重试时数字回退

---

## 3 核心实现

### 3.1 序列号管理器

```python
class SerialNumberManager:
    SN_FILE = "part no.bin"

    def get_combined_value(self) -> int:
        """前缀3位HEX + 后缀5位十进制 → 32位整数值"""
        prefix = self._clean_prefix(self.config.prefix)       # 如 "87F"
        suffix_str = str(self.config.current_number % 100000).zfill(5)  # 如 "00001"
        combined = prefix + suffix_str                        # "87F00001"
        return int(combined, 16)                              # 0x87F00001

    def get_bytes(self) -> bytes:
        """按配置的字节序输出4字节"""
        val = self.get_combined_value()
        order = 'big' if self.config.byte_order == 'big' else 'little'
        return val.to_bytes(4, byteorder=order)
```

### 3.2 Windows 窗体文字读取

ISP 工具的下发记录区域是子控件，需要同时用两种 API 读取：

```python
def _get_target_window_text(self) -> str:
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    WM_GETTEXT = 0x000D

    # 1. 找到目标窗口（标题匹配关键词）
    def enum_proc(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if "WCHISPTool" in buf.value:
                results.append((hwnd, buf.value))
        return True

    # 2. 枚举子控件，双方式读取文字
    def child_enum_proc(child_hwnd, _):
        txt = ""
        # 方式1：GetWindowTextW（对普通控件有效）
        length = user32.GetWindowTextLengthW(child_hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(child_hwnd, buf, length + 1)
            txt = buf.value.strip()

        # 方式2：WM_GETTEXT（对 Edit、ListBox 更有效）
        if not txt:
            buf2 = ctypes.create_unicode_buffer(4096)
            sent_len = user32.SendMessageW(child_hwnd, WM_GETTEXT, 4096, buf2)
            if sent_len > 0:
                txt = buf2.value.strip()

        if txt:
            child_texts.append(txt)
        return True
```

### 3.3 严谨的自动累加判断

```python
def _check_window_success(self, text: str):
    # 提取所有 "成功：数字"
    matches = re.findall(r'成功[：:]\s*(\d+)', text)
    if not matches:
        return

    current_count = int(matches[-1])

    # 变0不累加（统计清零）
    if current_count == 0:
        return

    # 未增加不累加（防止重复触发）
    if current_count <= self.last_success_count:
        return

    # 数字确实增加了，Part No +1
    current = int(self.var_sn_start.get())
    new_val = (current + 1) % 100000
    self.var_sn_start.set(str(new_val))
    self._update_sn_preview()

    self.last_success_count = current_count
```

---

## 4 从 1245 行到 543 行

这个工具最初是从 WCH ISP 烧录工具的 GUI 代码改过来的，经历了大幅度的精简：

| 阶段 | 代码行数 | 主要变化 |
|------|---------|---------|
| 初始版本 | 1245 | 完整的 ISP 烧录工具，含固件选择、进度条、日志系统 |
| 删除烧录功能 | ~800 | 移除 FlashEngine、FirmwareProcessor、FlashLogger |
| 删除 Notebook | ~700 | 去掉多标签页，改为单页面 |
| 删除按钮/进度条 | ~600 | 去掉开始/停止按钮、进度条、固件选择框 |
| 添加窗体监控 | ~580 | 新增 Windows API 读取 + 自动累加 |
| 添加字节序切换 | ~560 | 新增小端勾选框 |
| 清理残余代码 | **543** | 删除 SUPPORTED_CHIPS、flash 配置等常量 |

精简后的代码结构非常清晰：

```
SerialNumberConfig      # 配置数据类
SerialNumberManager     # 序列号读写管理
WCHISPGUIEnhanced       # GUI 主类
  ├── create_layout()       # 界面布局
  ├── _start_window_monitor()   # 启动监控
  ├── _poll_window_text()       # 定时轮询
  ├── _get_target_window_text() # API 读取
  ├── _check_window_success()   # 累加判断
  └── _update_sn_preview()      # 更新预览+写文件
```

---

## 5 技术难点

### 5.1 自绘控件读不到文字

WCHISPTool 的"下载记录"区域可能是自绘控件，标准的 `GetWindowTextW` 和 `WM_GETTEXT` 都无法读取其内容。解决方法：

1. 扩大标题关键词匹配范围（`CH57x-59x`、`WCHISPTool`）
2. 同时枚举窗口的所有子控件
3. 两种方式互补读取

如果仍然读不到，目前只能通过 OCR 截图识别，或者让 ISP 工具输出日志文件后监控文件。

### 5.2 字节序与 WCH ISP 工具的对应

实测发现 WCHISP 工具读取 `part no.bin` 是**大端序**（不勾选小端时），与芯片手册一致。但工具提供勾选框以防万一：

```
大端: 0x87F00001 → 文件内容: 87 F0 00 01
小端: 0x87F00001 → 文件内容: 01 00 F0 87
```

### 5.3 重复触发防护

早期版本只要匹配到"成功"就累加，导致同一批次重复 +1。改进方案：

- 从**整行文本对比** → 改为**提取数字对比**
- 增加"变 0 不累加"规则
- 增加"数字未增加不累加"规则

---

## 6 使用方式

### 6.1 目录结构

```
工作目录/
├── wch_isp_gui_enhanced.py    # 本工具
├── part no.bin                # 生成的序列号文件（自动创建）
└── config.json                # 配置保存（自动创建）
```

### 6.2 启动前准备

1. 打开 `WCHISPTool_CH57x-59x.exe`
2. 在 ISP 工具的设置中选择"Part No 文件"，指向本工具生成的 `part no.bin`
3. 运行 `python wch_isp_gui_enhanced.py`

### 6.3 操作流程

1. 设置前缀（如 `87F`）和起始号码（如 `1`）
2. 当前值预览实时显示组合后的 HEX 值
3. 勾选/不勾选"小端"以匹配 ISP 工具的读取方式
4. 窗体监控区实时显示读取到的 ISP 工具文字
5. 在 ISP 工具中点击下载，成功一次 → 本工具的序列号自动 +1
6. 下次下载将使用新的 Part No

---

## 7 源码

完整源码放在 [python/wch_isp_gui_enhanced.py](https://github.com/WuJaw/WuJaw.github.io/blob/master/python/wch_isp_gui_enhanced.py)。

关键特点：
- 纯标准库（tkinter + ctypes），无需 pip 安装任何包
- 窗口固定尺寸 `440×430`，禁止拉伸
- 输入实时响应，修改后立即写入 `part no.bin`
- 配置文件自动清理旧字段，向后兼容

---

## 8 总结

这个工具的核心价值在于**消除重复劳动**：烧录人员只需要在 ISP 工具中反复点击下载，Part No 的递增完全自动化。

从 1245 行到 543 行的精简过程也说明：**功能的减法往往比加法更难，也更有价值**。一个只做一件事、但做得可靠的专用工具，远比一个大而全的万能工具更实用。
