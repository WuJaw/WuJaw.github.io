---
layout: post
title: "Microstation测试工具开发记录"
date: 2026-07-01
category: python
---

## 1 概述

Microstation 测试工具是一个基于 Python tkinter 的桌面 GUI 程序，用于微站设备的半成品和成品测试。通过串口连接微站设备，采集信号强度、版本信息等数据，自动写入 Excel 报告（仅成品测试）。

## 2 功能概览

### 2.1 测试模式

| 模式       | 说明                                                         |
|------------|-------------------------------------------------------------|
| 半成品测试 | 同时采集信号强度 + 设备版本（主机版本00、从机版本01/02），4分钟倒计时，支持20s无数据超时 |
| 成品测试   | 仅采集信号强度（与基站 + 与蓝牙标签），按配置包数结束，支持20s无数据超时   |

> **注意**：半成品测试结果仅显示在 UI 上，不写入 Excel；只有成品测试才会写入 Excel 文件。

### 2.2 信号采集逻辑

- 串口数据按行过滤，信号行需要**同时匹配蓝牙测试标签和数分微站号**才参与计算
- 版本行通过原始字符串前缀 `S R RF : 23 {station}` 匹配，不做格式转换
- 进度条按每包数据递增，达到配置包数后自动完成

### 2.3 超时保护

两种测试模式均支持配置超时时间（默认 20 秒）：

- 开始测试后启动超时定时器
- 首次收到有效信号数据时自动取消定时器
- 超时触发后：停止采集 → 显示"超时" → 成品测试写入 Excel（仅编号+备注"蓝牙标签或微站没有数据上报"） → 解锁配置

### 2.4 Excel 写入（仅成品测试）

- 自动去重：同一编号重复时覆盖写入而非追加
- 空行清理：自动删除夹在数据中间的完全空行（5列全部为 None）
- 全部右对齐（表头 + 数据行）
- 列：编号 / 与基站信号强度 / 与蓝牙标签信号强度 / 蓝牙信号强度 / 备注

## 3 关键实现细节

### 3.1 串口数据过滤

```python
def _should_display(self, text: str) -> bool:
    """版本行 或 信号行（双匹配）才显示"""
    if self._is_version_line(text):
        return True
    return self._is_signal_line(text)
```

信号行双匹配：文本同时包含蓝牙标签 hex 和数分微站号 hex 才算有效数据。

### 3.2 输入框 hex 格式化

所有 hex 输入框（蓝牙测试标签、数分微站号、版本）绑定 `FocusOut` 事件，自动：
- 去除非 hex 字符
- 转大写
- 每 2 字符加空格分隔

### 3.3 PyInstaller 打包关键点

- 使用 `-F -w` 打包为单文件无控制台窗口
- 路径处理：通过 `sys.frozen` 判断是否为打包环境，用 `sys.executable` 定位 exe 所在目录而非临时解压目录
- 必须 `--collect-all serial --collect-all openpyxl` 确保隐藏导入

### 3.4 超时定时器实现

```python
# 启动超时
timeout_sec = int(self.var_ble_timeout.get())
self._test_timeout_id = self.after(timeout_sec * 1000, self._on_test_timeout)

# 首次收到数据取消超时
if self._test_mode in ("full", "semi"):
    tid = getattr(self, "_test_timeout_id", None)
    if tid:
        self.after_cancel(tid)
        self._test_timeout_id = None
```

## 4 布局设计

左侧面板（260px）从上到下：

```
配置区域（串口号、写入文件、蓝牙测试标签等）
阈值配置（基站信号阈值、标签信号强度阈值）
采集参数（信号采集包数、超时时间(秒)）
[成品测试] [半成品测试] [停止测试]
进度条
─────────────
与基站信号 — dBm                     N
与蓝牙标签信号 — dBm                  N
主机版本00 —
从机版本01 —
从机版本02 —
测试成功，版本正常
基站信号弱              与蓝牙标签信号弱
```

- 信号标签、版本标签统一**右对齐**
- 信号数值紧跟标签，**计数器靠右**显示
- 警告行放在版本状态下方，与提示信息集中显示
- 版本面板在信号显示之后、警告行之前，无多余分隔线

## 5 配置文件

程序通过 `launcher_config.json` 自动保存/恢复配置：

```json
{
  "port": "COM3",
  "excel_path": "",
  "ble_tag": "",
  "station_id": "",
  "rssi_threshold": "-70",
  "ble_rssi_threshold": "-70",
  "ble_packet_count": "10",
  "ble_timeout": "20",
  "host_version": "",
  "slave_version_01": "",
  "slave_version_02": ""
}
```

重启程序自动恢复上次配置。

## 6 源码

最新代码见 [assets/launcher.py](../assets/launcher.py)。
