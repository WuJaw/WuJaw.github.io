---
layout: post
title: "Hello Jekyll"
date: 2026-05-27
---

这是第一篇用 Markdown 写的文章。

## 写作很简单

只需要在 `_posts/` 目录下新建 `YYYY-MM-DD-标题.md` 文件，开头加上 Front Matter：

```markdown
---
layout: post
title: "文章标题"
date: 2026-05-27
---

正文内容...
```

推送到 GitHub 后，GitHub Pages 会自动编译生成页面。

## 支持的语法

### 代码块

```c
// STM32 UART 中断接收
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART2) {
        // 处理数据
    }
}
```

### 列表

- STM32 / CH592 嵌入式开发
- BLE / WiFi 模块调试
- RISC-V 架构

### 表格

| 芯片 | 架构 | 用途 |
|------|------|------|
| STM32F405 | ARM Cortex-M4 | 主控 |
| CH592F | RISC-V | BLE |
| BW16 | ARMv8-M | WiFi/BLE |

就这样，开始写吧 ✍️
