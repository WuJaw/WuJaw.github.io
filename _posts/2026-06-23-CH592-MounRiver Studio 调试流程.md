---
layout: post
title: "MounRiver Studio 调试流程"
date: 2026-06-23
category: CH592
---

基于 CH592F 项目的 MounRiver Studio 调试完整流程记录。

## 1 整体流程

```
硬件连接 ──▶ 工程配置 ──▶ 编译 ──▶ 调试配置 ──▶ 进入调试 ──▶ 调试操作 ──▶ 烧录
```

---

## 2 硬件连接

WCH-LinkE 仿真器通过 SWD 接口连接 CH592F，共 4 根线：

| VCC (3.3V) | VCC |
|--------|--------|
| 仿真器 | CH592F |
| GND | GND |
| SWDIO | SWDIO |
| SWCLK | SWCLK |



- 目标板需独立供电或由仿真器供电（电流不超过 200mA）

---

## 3 编译

**Project → Build All**（快捷键 `Ctrl + B`），确保 Console 输出 **0 errors**。

---

## 4 调试配置

**Run → Debug Configurations** → 双击 "GDB OpenOCD MRS Debugging" 新建一个配置：

- **Main** 选项卡：`C/C++ Application` 指向编译输出的 `.elf` 文件（在 `obj/` 目录下）
- **Debugger** 选项卡：`OpenOCD` 配置路径通常自动填入，无需手动修改
- 首次使用需新建配置，后续直接复用

<img src="/assets/image-20260623110447127.png" alt="image-20260623110447127">

如果不能调试就连接下 usb 接口 打开两线仿真

<img src="/assets/image-20260623112214582.png" alt="image-20260623112214582">
