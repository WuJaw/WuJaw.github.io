---
layout: post
title: "python：周报Excel项目编码自动填写"
date: 2026-06-09
category: 编程
---

## 1 背景

周报 Excel 的"项目编码"列（D 列）经常留空，手动逐行填写费时。实际工作内容里包含项目关键词（如"输液"、"床垫"、"蜂巢"等），可以根据关键词自动匹配项目编码，批量补全。

## 2 项目编码映射规则

根据公司项目列表，建立关键词到项目编码的映射：

| 关键词 | 项目编码 | 项目名称 |
|--------|----------|----------|
| 婴儿标签、bg13 | RD240008 | 婴儿防盗系统 |
| 输液、夹断、bg22 | RD240003 | 输液监测系统 |
| 蜂巢、星链、PCIE、at32、华为、海康 | RD250002 | 全网通数分平台 |
| 床垫、BWS | RD240005 | 生命体征监测床垫系统 |
| 送检、软著、CE认证、ch592、其他 | RD240009 | 物联网定位平台 |

匹配顺序：**先命中先生效**，未命中任何关键词则使用默认编码 `RD240009`。

## 3 实现代码

```python
import openpyxl
import shutil

src = r'D:\SVN2\docx\周报\办公室周报2026-吴潇.xlsx'
shutil.copy2(src, src + '.bak')  # 备份原文件

wb = openpyxl.load_workbook(src)
ws = wb.worksheets[0]

# 关键词 → 项目编码（顺序即优先级，先匹配先生效）
rules = [
    (['婴儿标签', 'bg13', 'BG13'], 'RD240008'),
    (['输液', '夹断', 'bg22', 'BG22'], 'RD240003'),
    (['蜂巢', '星链', 'PCIE', 'pcie', 'at32', 'AT32', '华为', '海康'], 'RD250002'),
    (['床垫', 'BWS'], 'RD240005'),
]
default_code = 'RD240009'

for r in range(4, ws.max_row + 1):
    status = ws.cell(r, 3).value
    code = ws.cell(r, 4).value
    # 只处理办公/外勤/出差，且项目编码为空的行
    if not status or str(status).strip() not in ('办公', '外勤', '出差'):
        continue
    if code and str(code).strip():
        continue

    # 合并工作内容 + 备注进行匹配
    content = str(ws.cell(r, 5).value or '')
    note = str(ws.cell(r, 6).value or '')
    text = content + ' ' + note

    matched_code = default_code
    for keywords, project_code in rules:
        if any(kw in text for kw in keywords):
            matched_code = project_code
            break

    ws.cell(r, 4).value = matched_code

wb.save(src)
```

## 4 关键设计

### 4.1 匹配优先级

规则列表的顺序决定优先级。例如某天工作内容同时包含"输液"和"婴儿标签"，`婴儿标签` 规则排在前面会先命中。

### 4.2 跳过已有编码

如果某行已手动填了项目编码，脚本不会覆盖，只补空缺行。

### 4.3 备份机制

修改前自动创建 `.bak` 备份，万一匹配错误可以回退。

## 5 踩坑：D 列数据验证

原始 Excel 的 D 列（项目编码）被误加了与 C 列相同的下拉验证规则：

```
C4:D7  →  list: "办公,外勤,出差,周六,周日,调休,法定假,年假,病假,婚假,事假,丧假,其他"
```

导致 D 列单元格显示工作状态下拉，而非自由输入项目编码。需要用 openpyxl 将数据验证范围从 `C:D` 改为仅 `C`：

```python
import re

wb = openpyxl.load_workbook(src)
ws = wb.worksheets[0]
dv = ws.data_validations.dataValidation[0]

# 将 C4:D7 拆为 C4:C7，删除纯 D 列范围
new_parts = []
for part in str(dv.sqref).split():
    if ':' in part:
        start, end = part.split(':')
        c1 = re.match(r'[A-Z]+', start).group()
        c2 = re.match(r'[A-Z]+', end).group()
        if c1 == 'C' and c2 == 'D':
            r1 = re.search(r'\d+', start).group()
            r2 = re.search(r'\d+', end).group()
            new_parts.append(f'C{r1}:C{r2}')
        elif c1 == 'C':
            new_parts.append(part)
        # D 列范围直接丢弃
    else:
        col = re.match(r'[A-Z]+', part).group()
        if col == 'C':
            new_parts.append(part)

dv.sqref = ' '.join(new_parts)
wb.save(src)
```

## 6 总结

| 项目 | 说明 |
|------|------|
| 依赖 | `openpyxl` |
| 输入 | 周报 Excel（含工作内容关键词） |
| 输出 | 同文件，D 列自动补全项目编码 |
| 备份 | 原文件 → `.bak` |
| 匹配逻辑 | 关键词优先级匹配 + 默认编码兜底 |
| 注意 | 先清除 D 列误加的下拉验证再填写 |
