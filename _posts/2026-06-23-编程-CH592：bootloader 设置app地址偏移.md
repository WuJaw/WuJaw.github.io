---
layout: post
title: "CH592：bootloader 设置app地址偏移"
date: 2026-06-23
category: 编程
---

## 1 APP 程序设置地址偏移
### 1.1 链接脚本 `Ld/Link.ld` — FLASH 起始地址

对比你的备份文件，已经改过了：

| 项目           | 原始（.bak） | 当前（Link.ld）  |
| :------------- | :----------- | :--------------- |
| `FLASH ORIGIN` | `0x00000000` | **`0x0000c000`** |
| `FLASH LENGTH` | `448K`       | **`400K`**       |

这就是把 Firmware 镜像的起始地址往后偏移了 **48KB（0xC000）**，前面留给 Bootloader。也是地址偏移最核心的一步。

### 1.2 `APP/include/ota.h` — Bootloader 大小宏

**c**

```c
#define BOOTLOADER_SIZE     (0xC000)    // bootloader最大空间
#define FLASH_APP0_ADDR     (FLASH_START_ADDR+BOOTLOADER_SIZE)  // = 0x0000C000
```

这两个值必须和 `Link.ld` 里的 `FLASH ORIGIN` **保持一致**。如果链接脚本改了偏移，这里也要同步改。

------

### 1.3 设置原则

调整时以你的 Bootloader 实际大小为准：

- **确认 Bootloader 编译后的大小**，然后取整到 4KB 对齐（CH592F 一个 Flash page = 0x1000）
- 比如 Bootloader 实际占 20KB → 取 `0x5000`（向上对齐到 4KB 整数倍）
- 同时改三个地方：

```
Link.ld:        FLASH ORIGIN = 0x00005000, LENGTH = 448K - 20K
ota.h:          #define BOOTLOADER_SIZE  (0x5000)
ota.h:          FLASH_APP0_ADDR 自动计算 = 0x00005000
```

------

### 1.4 补充说明

CH592F 是 RISC-V + BLE ROM 架构，中断向量表放在 RAM 中的 `.highcode` 段（由 ROM boot 代码加载），跟普通 ARM 的 VTOR 不同，所以 **不需要** 手动设置中断向量偏移寄存器。链接脚本的 `FLASH ORIGIN` 改好就行，ROM 启动代码会自动从对应位置搬运向量表。

你目前配置的 `0xC000`（48KB）作为 Bootloader 空间是合理的。需要调大调小的话，前面说的三个位置一起改就行。
