#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CH592 Part no 烧录工具
========================================
基于 tkinter 的极简工具，支持 Part No 生成与窗体监控自动累加

功能：
  ✅ 前缀(3位HEX) + 起始号码(5位数字) 组合
  ✅ 实时生成 4 字节 part no.bin（大端/小端可选）
  ✅ 窗体监控 WCHISPTool，检测到"成功：X"数字增加时自动累加

作者：Auto Generated
日期：2026-06-12
版本：v3.0.0
"""

import re
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict


# ============================================================================
# 配置数据类
# ============================================================================

@dataclass
class SerialNumberConfig:
    """序列号配置
    规则：前缀3位十六进制 + 后缀5位十进制，拼成8位十六进制值
    例如：前缀 87F，后缀 12456 → 0x87F12456
    """
    start_number: int = 0
    current_number: int = 0
    prefix: str = "87F"
    byte_order: str = "big"


@dataclass
class AppConfig:
    """应用总配置"""
    serial: SerialNumberConfig = field(default_factory=SerialNumberConfig)


# ============================================================================
# 序列号管理器
# ============================================================================

class SerialNumberManager:
    """序列号管理器"""

    SN_FILE = "part no.bin"

    def __init__(self, config: SerialNumberConfig, work_dir: str = "."):
        self.config = config
        self.work_dir = Path(work_dir)
        self.sn_file = self.work_dir / self.SN_FILE
        self._load_state()

    def _load_state(self):
        """从 part no.bin 恢复当前序列号（4字节大端/小端整数），没有则新建"""
        if self.sn_file.exists():
            try:
                with open(self.sn_file, 'rb') as f:
                    raw = f.read(4)
                if len(raw) == 4:
                    order = 'big' if self.config.byte_order == 'big' else 'little'
                    val = int.from_bytes(raw, byteorder=order)
                    # 从组合值反推后缀（提取低20位，即 5 位十进制后缀）
                    suffix = val & 0xFFFFF
                    self.config.current_number = suffix % 100000
                    return
            except:
                pass
        else:
            # 文件不存在，创建并写入初始值
            self.config.current_number = self.config.start_number
            self._save_state()

    def _save_state(self):
        """写入 part no.bin（4字节二进制，大端/小端由配置决定）"""
        with open(self.sn_file, 'wb') as f:
            f.write(self.get_bytes())

    @staticmethod
    def _is_hex(s: str) -> bool:
        """判断字符串是否为合法十六进制"""
        try:
            int(s, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def _clean_prefix(raw: str) -> str:
        """只保留合法十六进制字符，转大写，补零到3位"""
        cleaned = ''.join(c for c in raw.upper() if c in '0123456789ABCDEF')
        return cleaned[:3].zfill(3)

    def get_formatted_number(self) -> str:
        """返回序列号字符串
        - 前缀必须是合法HEX，拼成 0xPPSSSSS 格式（如 0x87F00001）
        """
        prefix = self._clean_prefix(self.config.prefix)
        suffix_str = str(self.config.current_number % 100000).zfill(5)
        combined = prefix + suffix_str
        combined_val = int(combined, 16)
        return f"0x{combined_val:08X}"

    def get_combined_value(self) -> int:
        """返回组合后的32位整数值（前缀强制清理为合法HEX）"""
        prefix = self._clean_prefix(self.config.prefix)
        suffix_str = str(self.config.current_number % 100000).zfill(5)
        combined = prefix + suffix_str
        return int(combined, 16)

    def get_bytes(self) -> bytes:
        """将当前组合值转换为4字节小端/大端整数（用于写入固件）"""
        val = self.get_combined_value()
        if self.config.byte_order == "big":
            return val.to_bytes(4, byteorder='big')
        else:
            return val.to_bytes(4, byteorder='little')

    def increment(self) -> str:
        self.config.current_number += 1  # 十进制步长固定为1
        if self.config.current_number > 99999:
            self.config.current_number = 0  # 超限后从0重新开始
        new_num = self.get_formatted_number()
        self._save_state()
        return new_num

    def reset(self, number: Optional[int] = None):
        if number is not None:
            self.config.current_number = number
        else:
            self.config.current_number = self.config.start_number
        self._save_state()



# ============================================================================
# GUI 主界面（增强版）
# ============================================================================

class WCHISPGUIEnhanced:
    """CH592 Part no 烧录工具 GUI 主类"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('CH592 Part no 烧录工具')

        self.bg = '#f0f0f0'

        # 配置
        self.config = AppConfig()
        self.config_file = Path("config.json")
        self.load_config()

        # 窗体监控状态
        self.window_monitor_id = None
        self.last_window_text = ""       # 上次读取到的完整窗体文字
        self.last_success_count = 0      # 上次记录的"成功："后面的数字，防止重复累加

        # GUI 变量
        self.setup_gui_variables()

        # 创建界面
        self.create_layout()

        self._update_sn_preview()

    def setup_gui_variables(self):
        """设置GUI变量"""
        self.var_sn_start = tk.StringVar()
        # 每次启动都使用默认值 0（不再恢复 part no.bin 的旧值）
        start = self.config.serial.start_number
        self.var_sn_start.set(str(start))

        self.var_sn_prefix = tk.StringVar()
        self.var_sn_prefix.set(self.config.serial.prefix)

        self.var_little_endian = tk.IntVar()
        self.var_little_endian.set(0 if self.config.serial.byte_order == 'big' else 1)

        # 创建/覆盖 part no.bin 写入初始值
        sn_file = Path(__file__).parent / "part no.bin"
        try:
            order = 'little' if self.var_little_endian.get() == 1 else 'big'
            prefix_val = int(self.config.serial.prefix, 16) if self.config.serial.prefix else 0
            combined = (prefix_val << 20) | (start % 100000)
            with open(sn_file, 'wb') as f:
                f.write(combined.to_bytes(4, byteorder=order))
        except:
            pass

    def create_layout(self):
        """创建界面布局（固定窗口大小）"""
        W, H = 440, 430
        self.root.geometry(f"{W}x{H}")
        self.root.resizable(False, False)  # 禁止改变大小

        LEFT_W = 420         # 左侧固定宽度

        font_main = ('微软雅黑', 10)
        font_label = ('微软雅黑', 9)

        # ===== 根窗口 Grid 配置 =====
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # ===== 左侧容器 + 可滚动内容 =====
        left_container = tk.Frame(self.root, bg=self.bg)
        left_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left_container.grid_rowconfigure(0, weight=1)
        left_container.grid_columnconfigure(0, weight=1)

        # Canvas + Scrollbar（无 notebook，直接滚动内容）
        canvas = tk.Canvas(left_container, bg=self.bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=self.bg)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=0, pady=2)

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        # 鼠标滚轮支持
        def _on_mousewheel(event):
            widget = self.root.winfo_containing(event.x_root, event.y_root)
            if widget and (str(widget).startswith(str(canvas)) or
                           str(widget).startswith(str(self.scroll_frame))):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)

        y = 10  # 垂直起始坐标

        y += 10

        # --- 序列号配置框架 ---
        self.sn_frame = tk.Frame(self.scroll_frame, bg=self.bg, relief='groove', bd=1)
        self.sn_frame.place(x=10, y=y, width=LEFT_W - 30, height=145)
        sy = 8

        tk.Label(self.sn_frame, text='前缀(3位):', bg=self.bg, font=font_label).place(x=5, y=sy)
        vcmd_hex = (self.root.register(self._validate_hex_prefix), '%P')
        self.entry_prefix = tk.Entry(self.sn_frame, font=font_main, width=8,
                 textvariable=self.var_sn_prefix,
                 validate='key', validatecommand=vcmd_hex)
        self.entry_prefix.place(x=100, y=sy)
        tk.Label(self.sn_frame, text='(如: 87F, 仅限 0-9 A-F)', bg=self.bg,
                 font=('微软雅黑', 8), fg='gray').place(x=175, y=sy+2)
        sy += 30

        tk.Label(self.sn_frame, text='起始号码(5位):', bg=self.bg, font=font_label).place(x=5, y=sy)
        self.entry_start = tk.Entry(self.sn_frame, font=font_main, width=8,
                 textvariable=self.var_sn_start)
        self.entry_start.place(x=100, y=sy)
        tk.Label(self.sn_frame, text='(十进制, 如: 12456)', bg=self.bg,
                 font=('微软雅黑', 8), fg='gray').place(x=175, y=sy+2)
        sy += 30

        # 实时预览标签
        tk.Label(self.sn_frame, text='当前值预览:', bg=self.bg, font=font_label).place(x=5, y=sy)
        self.preview_label = tk.Label(self.sn_frame, text='0x00000000',
                                      bg=self.bg, font=('Consolas', 16, 'bold'), fg='#0056b3')
        self.preview_label.place(x=100, y=sy)
        sy += 32

        # 字节序勾选
        tk.Label(self.sn_frame, text='字节序:', bg=self.bg, font=font_label).place(x=5, y=sy+2)
        self.chk_endian = tk.Checkbutton(self.sn_frame, text='小端 (Little Endian)',
                                         bg=self.bg, font=font_label,
                                         variable=self.var_little_endian,
                                         command=self._update_sn_preview,
                                         cursor='hand2')
        self.chk_endian.place(x=100, y=sy)

        # 绑定输入变化实时更新预览
        self.var_sn_prefix.trace_add('write', lambda *a: self._update_sn_preview())
        self.var_sn_start.trace_add('write', lambda *a: self._update_sn_preview())
        self._update_sn_preview()

        y += 155

        # --- 窗体监控显示区域 ---
        monitor_frame = tk.LabelFrame(self.scroll_frame, text='窗体监控', bg=self.bg,
                                   font=('微软雅黑', 9, 'bold'), fg='#007bff')
        monitor_frame.place(x=10, y=y, width=LEFT_W - 30, height=220)

        # 监控内容显示 Text
        self.monitor_text = tk.Text(monitor_frame, height=12, bg='#11111b', fg='#cdd6f4',
                                 font=('Consolas', 9), wrap='word',
                                 relief='sunken', bd=1)
        self.monitor_text.pack(side='left', fill='both', expand=True, padx=4, pady=4)

        # 滚动条
        monitor_scroll = ttk.Scrollbar(monitor_frame, orient='vertical',
                                   command=self.monitor_text.yview)
        monitor_scroll.pack(side='right', fill='y', pady=4)
        self.monitor_text.config(yscrollcommand=monitor_scroll.set)

        # 启动窗体监控
        self._start_window_monitor()

        y += 230

        # 设置滚动区域尺寸（place 不会自动扩展父容器）
        self.scroll_frame.config(width=LEFT_W - 40, height=y)
        canvas.config(scrollregion=(0, 0, LEFT_W - 40, y))

    # ========== 以下是方法定义 ==========

    def _start_window_monitor(self):
        """启动窗体文字监控"""
        self.window_monitor_id = None
        self.last_window_text = ""       # 上次读取到的完整窗体文字
        self.last_success_text = ""      # 上次触发成功的文字，防止重复累加
        # 立即读取一次
        self._poll_window_text()

    def _poll_window_text(self):
        """定时读取目标窗体文字（每500ms）"""
        try:
            text = self._get_target_window_text()
            if text:
                # 更新显示区（只显示最新内容，最多2000字符）
                display = text[-2000:] if len(text) > 2000 else text
                self.monitor_text.config(state='normal')
                self.monitor_text.delete('1.0', tk.END)
                self.monitor_text.insert(tk.END, display)
                self.monitor_text.see(tk.END)
                self.monitor_text.config(state='disabled')
                # 检查是否有新的"成功"
                self._check_window_success(text)
        except:
            pass
        # 每 500ms 轮询一次
        self.window_monitor_id = self.root.after(500, self._poll_window_text)

    def _get_target_window_text(self) -> str:
        """获取目标窗体及其子控件的所有文字（通过 Windows API + WM_GETTEXT）"""
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32

        # 配置目标窗体标题关键词（可修改）
        TARGET_TITLE_KEYWORDS = ["CH57x-59x", "WCHISPTool"]   # ← 修改为你想监控的窗口标题关键词

        # 获取所有可见窗口
        results = []
        def enum_proc(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value
                    for kw in TARGET_TITLE_KEYWORDS:
                        if kw in title:
                            results.append((hwnd, title))
                            break
            return True

        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(EnumWindowsProc(enum_proc), 0)

        if not results:
            return "[未找到目标窗口]"

        hwnd, title = results[0]
        texts = [f"[找到窗口: {title}]"]

        # 获取窗口类名
        class_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_buf, 256)
        texts.append(f"[窗口类名: {class_buf.value}]")

        # 枚举子控件并读取文字（GetWindowTextW + WM_GETTEXT）
        child_texts = []
        WM_GETTEXT = 0x000D

        def child_enum_proc(child_hwnd, _):
            # 方法1: GetWindowTextW
            length = user32.GetWindowTextLengthW(child_hwnd)
            txt = ""
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(child_hwnd, buf, length + 1)
                txt = buf.value.strip()

            # 方法2: SendMessage WM_GETTEXT（对 Edit/ListBox 更有效）
            if not txt:
                buf2 = ctypes.create_unicode_buffer(4096)
                sent_len = user32.SendMessageW(child_hwnd, WM_GETTEXT, 4096, buf2)
                if sent_len > 0:
                    txt = buf2.value.strip()

            if txt:
                child_texts.append(txt)
            return True

        user32.EnumChildWindows(hwnd, EnumWindowsProc(child_enum_proc), 0)
        texts.extend(child_texts)

        return '\n'.join(texts)

    def _check_window_success(self, text: str):
        """检查窗体文字中'成功：X'的数字，数字增加才累加 Part No，变0不累加"""
        # 用正则提取所有"成功：数字"中的数字
        matches = re.findall(r'成功[：:]\s*(\d+)', text)
        if not matches:
            return
        # 取最后一个匹配的数字
        try:
            current_count = int(matches[-1])
        except:
            return
        # 数字为0时不处理（防止清零时误触发）
        if current_count == 0:
            return
        # 数字没有增加（减少或不变）时不处理
        if current_count <= self.last_success_count:
            return
        # 数字增加了，累加 Part No
        try:
            current = int(self.var_sn_start.get())
            new_val = (current + 1) % 100000
            self.var_sn_start.set(str(new_val))
            self._update_sn_preview()
        except:
            pass
        # 记录这次的成功数字
        self.last_success_count = current_count

    def get_current_serial(self) -> str:
        """获取当前序列号（前缀强制清理为合法HEX）"""
        prefix = SerialNumberManager._clean_prefix(self.var_sn_prefix.get())
        try:
            suffix = int(self.var_sn_start.get()) % 100000
        except:
            suffix = 0
        suffix_str = str(suffix).zfill(5)
        combined = prefix + suffix_str
        combined_val = int(combined, 16)
        return f"0x{combined_val:08X}"

    def _update_sn_preview(self):
        """实时更新预览标签 + 自动保存到 part no.bin"""
        if hasattr(self, 'preview_label'):
            self.preview_label.config(text=self.get_current_serial())

        # 自动保存当前序列号到 part no.bin
        try:
            prefix = SerialNumberManager._clean_prefix(self.var_sn_prefix.get())
            suffix = int(self.var_sn_start.get()) % 100000
            combined_str = prefix + str(suffix).zfill(5)
            val = int(combined_str, 16)
            order = 'little' if self.var_little_endian.get() == 1 else 'big'
            sn_file = Path(__file__).parent / "part no.bin"
            with open(sn_file, 'wb') as f:
                f.write(val.to_bytes(4, byteorder=order))
        except:
            pass

    def _validate_hex_prefix(self, value: str) -> bool:
        """前缀输入框校验：只允许 0-9, A-F, a-f，最多3位"""
        if value == '':
            return True
        if len(value) > 3:
            return False
        return all(c in '0123456789abcdefABCDEF' for c in value)

    def _clean_prefix(self, raw: str) -> str:
        """清理前缀，只保留合法十六进制字符，转大写，补零到3位"""
        cleaned = ''.join(c for c in raw.upper() if c in '0123456789ABCDEF')
        return cleaned[:3].zfill(3)

    def update_config_from_gui(self):
        """从GUI更新配置"""
        try:
            self.config.serial.start_number = int(self.var_sn_start.get() or 0)
            self.config.serial.prefix = self._clean_prefix(self.var_sn_prefix.get())
            self.config.serial.byte_order = 'little' if self.var_little_endian.get() == 1 else 'big'
        except Exception:
            pass

    def save_config(self):
        """保存配置到文件"""
        self.update_config_from_gui()
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功", f"配置已保存!\n{self.config_file}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败:\n{e}")

    def load_config(self):
        """从文件加载配置（兼容旧格式）"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 仅读取 SerialNumberConfig 中已存在的字段，忽略旧版多余字段
                if 'serial' in data and isinstance(data['serial'], dict):
                    sn_data = data['serial']
                    valid_fields = {k: sn_data[k] for k in sn_data
                                    if k in SerialNumberConfig.__dataclass_fields__}
                    data['serial'] = SerialNumberConfig(**valid_fields)
                # AppConfig 同样容错，忽略旧版 flash 等字段
                valid_app = {k: data[k] for k in data
                             if k in AppConfig.__dataclass_fields__}
                self.config = AppConfig(**valid_app)
            except Exception:
                pass

    def run(self):
        """运行主循环"""
        self.root.mainloop()


# ============================================================================
# 主程序入口
# ============================================================================

if __name__ == "__main__":
    app = WCHISPGUIEnhanced()
    app.run()
