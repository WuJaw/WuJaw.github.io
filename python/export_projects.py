#!/usr/bin/env python3
"""
项目列表导出工具
从工时系统导出所有项目信息到 Excel

使用方式:
  1. pip install pandas openpyxl requests
  2. python export_projects.py
  3. 弹窗选择保存位置（或默认保存到脚本同目录）
"""

import pandas as pd
import requests
import os
import json
import sys
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    tk = None

# ============ 配置区 ============
BASE_URL = "http://10.10.5.25:8004"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.json')


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_cookie():
    cfg = load_config()
    cookie = cfg.get('cookie', '')
    if cookie:
        return cookie

    print('  Cookie 不存在，请先运行 submit_work_hours.py 或手动输入')
    print('  (浏览器 F12 > Console > copy(document.cookie))')
    cookie = input('\n  Cookie: ').strip()
    if cookie:
        cfg['cookie'] = cookie
        cfg['cookie_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_config(cfg)
    return cookie


def select_save_path(default_name):
    """弹窗选择保存位置"""
    if tk:
        root = tk.Tk()
        root.withdraw()
        path = filedialog.asksaveasfilename(
            title='保存项目列表',
            defaultextension='.xlsx',
            initialfile=default_name,
            filetypes=[('Excel 文件', '*.xlsx'), ('所有文件', '*.*')],
            initialdir=SCRIPT_DIR
        )
        root.destroy()
        return path if path else os.path.join(SCRIPT_DIR, default_name)
    return os.path.join(SCRIPT_DIR, default_name)


def fetch_projects(cookie):
    headers = {'Content-Type': 'application/json', 'Cookie': cookie}
    payload = {"projectName": "", "pageNum": 1, "pageSize": 9999, "projectType": 1}
    try:
        resp = requests.post(f'{BASE_URL}/api/project/list', json=payload, headers=headers, timeout=10)
        result = resp.json()
        if result.get('code') == '200':
            return result.get('info', {}).get('list', [])
        else:
            print(f'  请求失败: {result.get("msg", result)}')
    except Exception as e:
        print(f'  网络错误: {e}')
    return []


def main():
    print('=' * 50)
    print('  工时系统 - 项目列表导出')
    print('=' * 50)

    print('\n[1/2] 获取 Cookie...')
    cookie = get_cookie()
    if not cookie:
        print('  Cookie 为空，退出')
        return

    print('\n[2/2] 获取项目列表...')
    projects = fetch_projects(cookie)
    if not projects:
        print('  未获取到项目，Cookie 可能已过期')
        return

    rows = []
    for p in projects:
        task_names = '; '.join(t['taskName'] for t in (p.get('projectTaskList') or []))
        rows.append({
            '项目ID': p['id'],
            '项目名称': p['projectName'],
            '项目编码': p['projectCode'],
            '项目类型': p.get('projectType', ''),
            '项目状态': '进行中' if p.get('projectStatus') == 1 else '已结束',
            '开始日期': p.get('startTime', '')[:10] if p.get('startTime') else '',
            '结束日期': p.get('endTime', '')[:10] if p.get('endTime') else '',
            '备注': p.get('remark', ''),
            '任务列表': task_names,
            '创建人': p.get('createByName', ''),
            '负责人': p.get('userName', ''),
            '创建时间': p.get('createTime', ''),
        })

    df = pd.DataFrame(rows)
    df = df.sort_values('项目编码').reset_index(drop=True)

    default_name = f'项目列表_{datetime.now().strftime("%Y%m%d")}.xlsx'
    out_file = select_save_path(default_name)

    df.to_excel(out_file, index=False, engine='openpyxl')

    print(f'\n  共 {len(rows)} 个项目')
    print(f'  已保存: {out_file}')

    # 预览
    print('\n  项目列表预览:')
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)
    pd.set_option('display.max_colwidth', 30)
    preview = df[['项目编码', '项目名称', '项目状态', '任务列表']].head(20)
    print(preview.to_string(index=False))
    if len(rows) > 20:
        print(f'  ... 共 {len(rows)} 个，完整列表见 Excel')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n已中断')
    except Exception as e:
        print(f'\n出错: {e}')
        import traceback
        traceback.print_exc()
