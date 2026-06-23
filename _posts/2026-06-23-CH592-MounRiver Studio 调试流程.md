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

---

## 5 进入调试

点击 **Debug** 按钮，MRS 自动：

1. 切换到 Debug 透视图（首次弹出提示）
2. 下载固件到 Flash
3. 停在 `main()` 函数入口

---

## 6 常用调试操作

| 操作 | 快捷键 | 说明 |
|------|--------|------|
| 单步进入 | `F5` | 进入函数内部 |
| 单步跳过 | `F6` | 不进入函数 |
| 全速运行 | `F8` | 运行到下一个断点 |
| 切换断点 | `Ctrl + Shift + B` | 或双击行号左侧 |
| 终止调试 | `Ctrl + F2` | 退出调试会话 |
| 重启 | 工具栏按钮 | 复位 MCU 重新运行 |

---

## 7 常用调试图口

- **Variables**：查看当前作用域变量值
- **Expressions**：添加自定义表达式监视
- **Registers**：查看 RISC-V 寄存器状态
- **Memory**：Memory Browser 查看指定地址的内存数据
- **Disassembly**：反汇编视图
- **Breakpoints**：管理所有断点

缺失的面板通过 **Window → Show View** 手动打开。

---

## 8 烧录

- Debug 会话会自动烧录固件
- 单独烧录用 **Flash → Download**
- 批量生产推荐 **WCHISPStudio** 工具

---

## 9 CH592F 特殊注意事项

1. **BLE 协议栈固件固化在 ROM 中**（地址 `0x0000`–`0x3FFF`），用户代码需要从 `0x4000` 开始，这部分区域不可擦写，调试时不用担心覆盖。

2. **带 Bootloader 时**，链接脚本中 `FLASH ORIGIN` 已经偏移到 `0xC000`（48KB），Debug Configuration 的 `.elf` 文件路径指向编译输出即可，仿真器会根据 `.elf` 中的地址信息自动烧写到正确位置。

3. **WCH-LinkE 固件版本**需要更新到最新，旧版本可能不支持 CH592F。使用 **WCH-LinkUtility** 工具升级。

4. **地址偏移**的三处同步修改：
   - `Ld/Link.ld`：`FLASH (rx) : ORIGIN = 0x0000C000`
   - `APP/include/ota.h`：`#define BOOTLOADER_SIZE (0xC000)`
   - `APP/include/ota.h`：`FLASH_APP0_ADDR = FLASH_START_ADDR + BOOTLOADER_SIZE`
