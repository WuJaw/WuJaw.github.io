#!/usr/bin/env python3
"""
工时自动填报脚本
从周报 Excel 读取工作内容，自动提交到工时系统

使用方式:
  1. pip install pandas openpyxl requests
  2. python submit_work_hours.py
  3. 弹窗选择周报 Excel 文件
  4. 首次运行输入 Cookie（后续自动保存）

Cookie 获取: 浏览器 F12 > Console > copy(document.cookie)
"""

import pandas as pd
import requests
import time
import os
import json
import sys
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    tk = None

# ============ 配置区（按需修改） ============
BASE_URL = "http://10.10.5.25:8004"
DEFAULT_PROJECT_CODE = "RD240009"  # 项目编码为空时的默认值
DEFAULT_TASK_INDEX = 0              # 默认选择第几个任务（0=第一个）
REQUEST_INTERVAL = 0.3              # 提交间隔（秒）

# ============ 脚本所在目录 ============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.json')

WORK_STATUS = {'办公', '外勤', '出差'}
REST_STATUS = {'法定假', '周六', '周日', '年假', '病假', '调休', '事假', '婚假', '丧假', '其他'}


# ============ 配置管理 ============
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


def load_cookie(cfg):
    return cfg.get('cookie', '')


def save_cookie_to_config(cookie):
    cfg = load_config()
    cfg['cookie'] = cookie
    cfg['cookie_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_config(cfg)


# ============ 文件选择 ============
def select_excel():
    """弹窗选择 Excel 文件，如果 tkinter 不可用则命令行输入"""
    if tk:
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title='选择周报 Excel 文件',
            filetypes=[('Excel 文件', '*.xlsx *.xls'), ('所有文件', '*.*')],
            initialdir=r'D:\SVN2\docx\周报'
        )
        root.destroy()
        return path if path else None
    else:
        print('请输入周报 Excel 文件路径:')
        path = input('> ').strip().strip('"')
        return path if path and os.path.exists(path) else None


# ============ API 请求 ============
def api_post(cookie, url, payload):
    headers = {'Content-Type': 'application/json', 'Cookie': cookie}
    try:
        resp = requests.post(f'{BASE_URL}{url}', json=payload, headers=headers, timeout=10)
        return resp.json()
    except Exception as e:
        return {'code': '500', 'msg': str(e)}


def fetch_projects(cookie):
    result = api_post(cookie, '/api/project/list',
                      {'pageNum': 1, 'pageSize': 9999, 'projectType': 1})
    if result.get('code') == '200':
        return result['info']['list']
    return []


def fetch_user_info(cookie):
    """从项目列表响应推断 userId（通过 Cookie 中的 token 字段）"""
    cfg = load_config()
    return cfg.get('user_id', int(cookie.split('token=')[-1].split(';')[0]) if 'token=' in cookie else 0)


def fetch_existing(cookie, user_id, date_str):
    result = api_post(cookie, '/api/dailyReport/list',
                      {'pageNum': 1, 'pageSize': 10, 'workDate': date_str, 'userId': user_id})
    if result.get('code') == '200':
        for item in result['info'].get('list', []):
            if item['userId'] == user_id and item['workDate'] == date_str:
                return item
    return None


# ============ 提交接口 ============
def submit_add(cookie, user_id, user_name, date, duration, matters, project, task):
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


def submit_update(cookie, user_id, user_name, existing, date, duration, matters, project, task):
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
        'taskList': project.get('projectTaskList', []),
        'projectUserName': project.get('userName'),
    }
    return api_post(cookie, '/api/dailyReport/update', payload)


# ============ Excel 解析 ============
def read_excel(path):
    # 尝试查找"周报"sheet，找不到就用第一个sheet
    xls = pd.ExcelFile(path)
    sheet_name = None
    for name in xls.sheet_names:
        if '周报' in name:
            sheet_name = name
            break
    if not sheet_name:
        sheet_name = xls.sheet_names[0]

    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
    records = []

    for _, row in df.iterrows():
        date_val = row.iloc[1]
        status = row.iloc[2]
        project_code = row.iloc[3]
        work_content = row.iloc[4]
        note = row.iloc[5]

        if pd.isna(date_val):
            continue
        weekday = str(row.iloc[0]).strip()
        if weekday in ('下周工作计划', '本周工作重点'):
            continue
        if pd.isna(status):
            continue

        date_str = date_val.strftime('%Y-%m-%d') if isinstance(date_val, datetime) else str(date_val)[:10]
        status = str(status).strip()

        code = str(project_code).strip() if pd.notna(project_code) else ''
        if not code:
            code = DEFAULT_PROJECT_CODE

        content = str(work_content).strip() if pd.notna(work_content) else ''
        note_str = str(note).strip() if pd.notna(note) else ''

        if status in REST_STATUS:
            continue

        duration = 8
        matters = content
        if note_str and note_str not in ('休息', ''):
            matters = (matters + '\n' + note_str) if matters else note_str
        if not matters:
            matters = '工作'

        records.append({
            'date': date_str,
            'status': status,
            'duration': duration,
            'matters': matters,
            'project_code': code,
        })
    return records


# ============ Cookie 管理 ============
def check_cookie(cookie):
    """验证 Cookie 是否有效"""
    result = api_post(cookie, '/api/project/list',
                      {'pageNum': 1, 'pageSize': 1, 'projectType': 1})
    return result.get('code') == '200'


def get_cookie():
    cfg = load_config()
    cookie = load_cookie(cfg)
    if cookie and check_cookie(cookie):
        t = cfg.get('cookie_time', '未知')
        print(f'  Cookie 有效 (保存于 {t})')
        return cookie

    print('\n  Cookie 无效或不存在，请输入')
    print('  (浏览器 F12 > Console > 输入 copy(document.cookie) > 回车)')
    cookie = input('\n  Cookie: ').strip()
    if not cookie:
        print('  Cookie 不能为空')
        sys.exit(1)

    if not check_cookie(cookie):
        print('  Cookie 无效，请检查后重试')
        sys.exit(1)

    save_cookie_to_config(cookie)
    print('  Cookie 已保存到 config.json')
    return cookie


# ============ 主流程 ============
def main():
    print('=' * 50)
    print('  工时自动填报工具')
    print('=' * 50)

    # 1. Cookie
    print('\n[1/4] 检查 Cookie...')
    cookie = get_cookie()

    # 获取用户信息
    user_id = fetch_user_info(cookie)
    if not user_id:
        print('  警告: 无法获取用户ID，请确认 Cookie 中包含 token 字段')
        user_id = int(input('  手动输入用户ID: ').strip() or '0')

    # 获取用户名（从已有记录或 Cookie）
    cfg = load_config()
    user_name = cfg.get('user_name', '')
    if not user_name:
        print(f'  请输入你的姓名:')
        user_name = input('  姓名: ').strip()
        if user_name:
            cfg['user_name'] = user_name
            cfg['user_id'] = user_id
            save_config(cfg)

    print(f'  用户: {user_name} (ID: {user_id})')

    # 2. 选择 Excel
    print('\n[2/4] 选择周报 Excel...')
    excel_path = select_excel()
    if not excel_path:
        print('  未选择文件，退出')
        return

    print(f'  文件: {os.path.basename(excel_path)}')
    records = read_excel(excel_path)
    if not records:
        print('  无有效记录（Excel 中无工作日数据）')
        return
    print(f'  共 {len(records)} 个工作日 ({records[0]["date"]} ~ {records[-1]["date"]})')

    # 3. 日期范围
    print('\n[3/4] 输入日期范围（回车=全部）:')
    start = input('  起始 (YYYY-MM-DD): ').strip()
    end = input('  结束 (YYYY-MM-DD): ').strip()
    if start:
        records = [r for r in records if r['date'] >= start]
    if end:
        records = [r for r in records if r['date'] <= end]
    if not records:
        print('  范围内无记录')
        return

    # 获取项目列表
    print('  获取项目列表...')
    projects = fetch_projects(cookie)
    if not projects:
        print('  获取项目失败，Cookie 可能已过期')
        return
    proj_map = {p['projectCode']: p for p in projects}

    # 检查缺失的项目编码
    all_codes = set(r['project_code'] for r in records)
    missing = all_codes - set(proj_map.keys())
    if missing:
        print(f'\n  警告: 以下项目编码不存在: {", ".join(missing)}')
        print(f'  将使用默认项目 {DEFAULT_PROJECT_CODE}')
        for r in records:
            if r['project_code'] not in proj_map:
                r['project_code'] = DEFAULT_PROJECT_CODE

    # 4. 提交
    total = len(records)
    print(f'\n[4/4] 开始提交 ({total} 条)...')
    print('=' * 50)

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
        task = tasks[DEFAULT_TASK_INDEX] if len(tasks) > DEFAULT_TASK_INDEX else tasks[0]

        existing = fetch_existing(cookie, user_id, r['date'])
        if existing:
            result = submit_update(cookie, user_id, user_name, existing,
                                    r['date'], r['duration'], r['matters'], project, task)
        else:
            result = submit_add(cookie, user_id, user_name,
                                 r['date'], r['duration'], r['matters'], project, task)

        if result.get('code') == '200':
            success += 1
            print(f'  [{i+1:>3}/{total}] OK {r["date"]} [{code}]')
        else:
            fail_list.append(r['date'])
            msg = result.get('msg', str(result))
            print(f'  [{i+1:>3}/{total}] FAIL {r["date"]}: {msg}')
        time.sleep(REQUEST_INTERVAL)

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
