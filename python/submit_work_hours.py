#!/usr/bin/env python3
"""
工时自动填报脚本 - 从周报Excel读取工作内容自动提交
Cookie存放在同目录 cookie.txt 中
"""

import time
import json
import os
import sys
import argparse
from datetime import datetime

# PyInstaller 打包后 __file__ 指向临时目录，cookie 会丢失
# 需要用 exe 所在目录（或 .py 脚本所在目录）
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(APP_DIR, 'cookie.txt')
BASE_URL = "http://10.10.5.25:8004"
DEFAULT_PROJECT_CODE = "RD240009"

WORK_STATUS = {'办公', '外勤', '出差'}
REST_STATUS = {'法定假', '周六', '周日', '年假', '病假', '调休', '事假', '婚假', '丧假', '其他'}


def extract_uid_from_cookie(cookie_str):
    """从 cookie 字符串中提取 token=xxx 作为 userId"""
    for part in cookie_str.split(';'):
        part = part.strip()
        if part.startswith('token='):
            val = part[6:].strip()
            if val.isdigit():
                return int(val)
    return 0


def read_clipboard():
    """从 Windows 剪贴板读取文本（PowerShell 方式，兼容 exe）"""
    try:
        import subprocess
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', 'Get-Clipboard'],
            capture_output=True, text=True, timeout=5
        )
        text = result.stdout.strip()
        if text:
            return text
    except:
        pass
    # 备用：ctypes
    try:
        import ctypes
        CF_UNICODETEXT = 13
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        if user32.OpenClipboard(0):
            try:
                if user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
                    handle = user32.GetClipboardData(CF_UNICODETEXT)
                    if handle:
                        ptr = kernel32.GlobalLock(handle)
                        if ptr:
                            text = ctypes.wstring_at(ptr)
                            kernel32.GlobalUnlock(handle)
                            return text.strip()
            finally:
                user32.CloseClipboard()
    except:
        pass
    return ''


def input_cookie(prompt='Cookie: '):
    """输入Cookie，支持回车从剪贴板读取（避免控制台粘贴截断）"""
    print('（浏览器复制Cookie后直接回车粘贴，或手动输入）')
    raw = input(prompt).strip()
    if raw:
        return raw
    # 回车 → 读剪贴板
    clip = read_clipboard()
    if clip:
        # 显示首尾，让用户确认
        if len(clip) > 80:
            print(f'  已读取 ({len(clip)} 字符): {clip[:50]}...{clip[-20:]}')
        else:
            print(f'  已读取: {clip}')
        return clip
    print('  剪贴板为空，请先在浏览器中复制Cookie')
    return ''


def load_cookie():
    """读取保存的凭据，返回 cookie 字符串或 None"""
    if os.path.exists(COOKIE_FILE):
        raw = open(COOKIE_FILE, 'r').read().strip()
        # 兼容旧 JSON 格式
        if raw.startswith('{'):
            try:
                d = json.loads(raw)
                return d.get('cookie', '')
            except json.JSONDecodeError:
                pass
        return raw
    return None


def save_cookie(cookie):
    with open(COOKIE_FILE, 'w') as f:
        f.write(cookie)


def api_post(cookie, url, payload):
    import requests
    headers = {'Content-Type': 'application/json', 'Cookie': cookie}
    try:
        resp = requests.post(f'{BASE_URL}{url}', json=payload, headers=headers, timeout=10)
        return resp.json()
    except Exception as e:
        return {'code': '500', 'msg': str(e)}


def detect_user(cookie, user_id):
    """从已有日报反查用户姓名"""
    result = api_post(cookie, '/api/dailyReport/list',
                      {'pageNum': 1, 'pageSize': 1, 'userId': user_id})
    if result.get('code') == '200':
        items = result['info'].get('list', [])
        if items:
            return items[0]['userCompellation']
    return ''


def select_excel():
    """tk文件对话框选择Excel文件"""
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title='选择周报Excel',
        filetypes=[('Excel', '*.xlsx *.xls')],
        initialdir=APP_DIR,
    )
    root.destroy()
    return path


def read_excel(path):
    import pandas as pd
    df = pd.read_excel(path, header=0)
    records = []
    last_date = None  # 上一行有效日期，用于"事假+半天办公"同日拆分的日期继承
    for _, row in df.iterrows():
        date_val = row.iloc[1]
        status = row.iloc[2]
        project_code = row.iloc[3]
        work_content = row.iloc[4]
        note = row.iloc[5]
        # 约最大天数（G列）：1=全天 0.5=半天，缺省按全天
        day_frac = row.iloc[6] if len(row) > 6 else None

        # 跳过非数据行："本周工作重点"/"下周工作计划" 分隔行可能出现在列0/列1/列2
        sep_phrases = {'下周工作计划', '本周工作重点', '本周工作计划'}
        row_head = [str(row.iloc[i]).strip() for i in range(min(3, len(row)))]
        if any(c in sep_phrases for c in row_head):
            continue

        # 日期解析：本行缺失或无有效值时沿用上一行（半天/分隔行往往不填日期）
        date_str = None
        if pd.notna(date_val):
            if isinstance(date_val, datetime):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                raw = str(date_val).strip()
                # 统一将 "." 和 "/" 替换为 "-" 再解析（兼容 2026.1.1 / 2026/1/1）
                normalized = raw.replace('.', '-').replace('/', '-')
                try:
                    date_str = datetime.strptime(normalized[:10], '%Y-%m-%d').strftime('%Y-%m-%d')
                except ValueError:
                    date_str = None
            if date_str:
                last_date = date_str
        if not date_str:
            if last_date:
                date_str = last_date
            else:
                continue  # 既无本行有效日期也无前序日期，跳过

        if pd.isna(status):
            continue

        status = str(status).strip()

        code = str(project_code).strip() if pd.notna(project_code) else ''
        if not code:
            code = DEFAULT_PROJECT_CODE

        content = str(work_content).strip() if pd.notna(work_content) else ''
        note_str = str(note).strip() if pd.notna(note) else ''

        # 约最大天数 → 工时(小时)：全天=8h，半天=4h，缺省按全天 8h
        frac = 1.0
        if pd.notna(day_frac):
            fs = str(day_frac).strip()
            if fs:
                try:
                    frac = float(fs)
                except ValueError:
                    frac = 1.0
        duration = int(round(frac * 8))

        if status in WORK_STATUS:
            matters = content
            if note_str and note_str not in ('休息', ''):
                matters = (matters + '\n' + note_str) if matters else note_str
            if not matters:
                matters = '工作'
        elif status in REST_STATUS:
            continue  # skip rest days
        else:
            matters = content if content else status

        records.append({
            'date': date_str,
            'status': status,
            'duration': duration,
            'matters': matters,
            'project_code': code,
        })
    return records


def fetch_projects(cookie):
    result = api_post(cookie, '/api/project/list',
                      {'pageNum': 1, 'pageSize': 9999, 'projectType': 1})
    if result.get('code') == '200':
        return result['info']['list']
    return []


def fetch_existing(cookie, date_str, user_id):
    result = api_post(cookie, '/api/dailyReport/list',
                      {'pageNum': 1, 'pageSize': 10, 'workDate': date_str, 'userId': user_id})
    if result.get('code') == '200':
        for item in result['info'].get('list', []):
            if item['userId'] == user_id and item['workDate'] == date_str:
                return item
    return None


def submit_add(cookie, date, duration, matters, project, task, user_id, user_name):
    task_list = project.get('projectTaskList', [])
    item = {
        'key': '000',
        'workDuration': str(duration),
        'workMatters': f'"{matters}"\n',
        'workDate': date,
        'projectId': project['id'],
        'workOvertime': '',
        'userCompellation': user_name,
        'isOverTime': False,
        'taskId': task['id'],
        'taskList': task_list,
        'projectName': project['projectName'],
        'taskName': task['taskName'],
        'projectType': 1,
        'projectCode': project['projectCode'],
        'projectUsername': '',
        'projectUserName': project.get('userName', ''),
        'userId': user_id,
        'auditing': 0,
    }
    return api_post(cookie, '/api/dailyReport/add', [item])


def submit_update(cookie, existing, date, duration, matters, project, task, user_id, user_name):
    task_list = project.get('projectTaskList', [])
    payload = {
        'id': existing['id'],
        'workDate': date,
        'workDuration': duration,
        'workMatters': matters,
        'workOvertime': existing.get('workOvertime', 0),
        'projectId': project['id'],
        'projectName': project['projectName'],
        'projectCode': project['projectCode'],
        'projectLeader': existing.get('projectLeader'),
        'taskId': task['id'],
        'taskName': task['taskName'],
        'userId': user_id,
        'userCompellation': user_name,
        'createTime': existing.get('createTime'),
        'updateTime': existing.get('updateTime'),
        'auditing': existing.get('auditing', 0),
        'createBy': existing.get('createBy', user_id),
        'deleted': existing.get('deleted'),
        'project': {
            'id': project['id'],
            'projectName': project['projectName'],
            'projectCode': project['projectCode'],
            'projectType': project.get('projectType', 1),
            'projectStatus': project.get('projectStatus'),
            'startTime': project.get('startTime'),
            'endTime': project.get('endTime'),
            'createTime': project.get('createTime'),
            'updateTime': project.get('updateTime'),
            'remark': project.get('remark'),
            'placeOnFile': project.get('placeOnFile', 0),
            'placeOnFileTime': None,
            'salesName': None,
            'createBy': project.get('createBy'),
            'createByName': project.get('createByName'),
            'deleted': 0,
            'userId': project.get('userId'),
            'fileName': project.get('fileName', ''),
            'userName': project.get('userName'),
            'projectTaskList': None,
            'dailyReportList': None,
            'projectUser': None,
            'projectPeopleNum': None,
            'projectWorkDurationNum': None,
        },
        'projectType': 1,
        'taskList': task_list,
        'projectUserName': project.get('userName'),
    }
    return api_post(cookie, '/api/dailyReport/update', payload)


def parse_args():
    parser = argparse.ArgumentParser(description='工时自动填报')
    parser.add_argument('-f', '--file', help='周报Excel路径（省略则弹出文件对话框）')
    parser.add_argument('-s', '--start', help='起始日期 MMDD，如 0212')
    parser.add_argument('-e', '--end', help='结束日期 MMDD，如 0212')
    parser.add_argument('--uid', type=int, default=0, help='用户ID（默认从cookie的token字段提取）')
    parser.add_argument('--name', default='', help='用户姓名（默认自动反查）')
    return parser.parse_args()


def main():
    args = parse_args()

    print('=' * 50)
    print('  工时自动填报工具')
    print('=' * 50)

    # ===== 阶段1：纯文本交互，零延迟 =====

    # Cookie
    cookie = load_cookie()
    if not cookie:
        print(f'\n首次使用，请输入Cookie')
        cookie = input_cookie()
        if not cookie:
            print('Cookie不能为空')
            return

    # 从 cookie 的 token= 字段提取 userId
    user_id = args.uid or extract_uid_from_cookie(cookie)

    # Excel路径：命令行指定 或 弹出文件选择
    excel_path = args.file

    # 日期范围（在 tkinter 之前问完）
    start = args.start
    end = args.end
    if not start and not end:
        year = datetime.now().strftime('%Y')
        print(f'\n年份: {year}，输入日期范围（回车=全部）：')
        start = input('  起始 (MMDD): ').strip()
        end = input('  结束 (MMDD): ').strip()

    # ===== 阶段2：需要 tkinter 的操作（仅路径未确定时）=====
    if not excel_path:
        print('请选择文件...')
        excel_path = select_excel()
        if not excel_path:
            print('未选择文件')
            return

    # ===== 阶段3：加载重模块 + 网络请求 =====
    print('加载中...')

    # Cookie 验证
    result = api_post(cookie, '/api/project/list',
                      {'pageNum': 1, 'pageSize': 1, 'projectType': 1})
    if result.get('code') != '200':
        print('Cookie无效或已过期，请重新输入')
        cookie = input_cookie()
        result = api_post(cookie, '/api/project/list',
                          {'pageNum': 1, 'pageSize': 1, 'projectType': 1})
        if result.get('code') != '200':
            print('Cookie仍然无效')
            return
        # cookie 变了，重新提取 uid
        user_id = args.uid or extract_uid_from_cookie(cookie)

    save_cookie(cookie)
    print('Cookie OK')

    # 确定用户身份
    if not user_id:
        user_id = extract_uid_from_cookie(cookie)
    if args.name:
        user_name = args.name
    else:
        user_name = detect_user(cookie, user_id) if user_id else ''
    if not user_name:
        user_name = input('请输入姓名: ').strip()
    print(f'用户: {user_name} (ID={user_id})')

    # 读取Excel
    print(f'读取: {excel_path}')
    records = read_excel(excel_path)
    if not records:
        print('无有效记录')
        return
    print(f'共 {len(records)} 个工作日 ({records[0]["date"]} ~ {records[-1]["date"]})')

    # 日期过滤（year 从 Excel 数据覆盖）
    year = records[0]['date'][:4]
    if start:
        start = f'{year}-{start[:2]}-{start[2:]}' if len(start) == 4 else start
        records = [r for r in records if r['date'] >= start]
    if end:
        end = f'{year}-{end[:2]}-{end[2:]}' if len(end) == 4 else end
        records = [r for r in records if r['date'] <= end]
    if not records:
        print('范围内无记录')
        return

    # 获取项目列表，构建 code -> project 映射
    print('获取项目列表...')
    projects = fetch_projects(cookie)
    if not projects:
        print('获取项目失败')
        return
    proj_map = {}
    for p in projects:
        proj_map[p['projectCode']] = p

    # 检查缺失的项目编码
    all_codes = set(r['project_code'] for r in records)
    missing = all_codes - set(proj_map.keys())
    if missing:
        print(f'\n警告: 以下项目编码在系统中不存在: {", ".join(missing)}')
        print(f'将使用默认项目 {DEFAULT_PROJECT_CODE}')
        for r in records:
            if r['project_code'] not in proj_map:
                r['project_code'] = DEFAULT_PROJECT_CODE

    # 统计
    total = len(records)
    print(f'\n待提交: {total} 条')
    print('=' * 50)

    # 直接开始提交
    success = 0
    fail_list = []
    for i, r in enumerate(records):
        code = r['project_code']
        project = proj_map.get(code)
        if not project:
            fail_list.append(r['date'])
            print(f'  [{i+1:>3}/{total}] SKIP {r["date"]} (项目 {code} 不存在)')
            continue

        tasks = project.get('projectTaskList', [])
        task = tasks[0] if tasks else {'id': None, 'taskName': ''}

        existing = fetch_existing(cookie, r['date'], user_id)
        if existing:
            # 已审核的记录不可修改，跳过
            if existing.get('auditing') == 1:
                print(f'  [{i+1:>3}/{total}] SKIP {r["date"]} (已审核，不可修改)')
                time.sleep(0.3)
                continue
            result = submit_update(cookie, existing, r['date'], r['duration'], r['matters'], project, task, user_id, user_name)
        else:
            result = submit_add(cookie, r['date'], r['duration'], r['matters'], project, task, user_id, user_name)

        if result.get('code') == '200':
            success += 1
            print(f'  [{i+1:>3}/{total}] OK {r["date"]} [{code}]')
        else:
            fail_list.append(r['date'])
            # 优先显示 info（服务端真实原因），其次 msg
            msg = result.get('info') or result.get('msg') or str(result)
            print(f'  [{i+1:>3}/{total}] FAIL {r["date"]}: {msg}')
        time.sleep(0.3)

    print(f'\n完成: 成功 {success}, 失败 {len(fail_list)}')
    if fail_list:
        print(f'失败日期: {", ".join(fail_list[:20])}')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n已中断')
    except Exception as e:
        print(f'\n出错: {e}')
        import traceback
        traceback.print_exc()
