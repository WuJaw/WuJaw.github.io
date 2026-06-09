#!/usr/bin/env python3
"""
工时自动填报脚本 - 从周报Excel读取工作内容自动提交
Cookie存放在同目录 cookie.txt 中
"""

import pandas as pd
import requests
import time
import json
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(SCRIPT_DIR, 'cookie.txt')
BASE_URL = "http://10.10.5.25:8004"
USER_ID = 111
USER_NAME = "吴潇"
DEFAULT_PROJECT_CODE = "RD240009"

WORK_STATUS = {'办公', '外勤', '出差'}
REST_STATUS = {'法定假', '周六', '周日', '年假', '病假', '调休', '事假', '婚假', '丧假', '其他'}


def load_cookie():
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'r') as f:
            return f.read().strip()
    return None


def save_cookie(cookie):
    with open(COOKIE_FILE, 'w') as f:
        f.write(cookie)


def api_post(cookie, url, payload):
    headers = {'Content-Type': 'application/json', 'Cookie': cookie}
    try:
        resp = requests.post(f'{BASE_URL}{url}', json=payload, headers=headers, timeout=10)
        return resp.json()
    except Exception as e:
        return {'code': '500', 'msg': str(e)}


def select_excel():
    """tk文件对话框选择Excel文件"""
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title='选择周报Excel',
        filetypes=[('Excel', '*.xlsx *.xls')],
        initialdir=SCRIPT_DIR,
    )
    root.destroy()
    return path


def read_excel(path):
    df = pd.read_excel(path, header=0)
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

        if status in WORK_STATUS:
            duration = 8
            matters = content
            if note_str and note_str not in ('休息', ''):
                matters = (matters + '\n' + note_str) if matters else note_str
            if not matters:
                matters = '工作'
        elif status in REST_STATUS:
            continue  # skip rest days
        else:
            duration = 8
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


def fetch_existing(cookie, date_str):
    result = api_post(cookie, '/api/dailyReport/list',
                      {'pageNum': 1, 'pageSize': 10, 'workDate': date_str, 'userId': USER_ID})
    if result.get('code') == '200':
        for item in result['info'].get('list', []):
            if item['userId'] == USER_ID and item['workDate'] == date_str:
                return item
    return None


def submit_add(cookie, date, duration, matters, project, task):
    task_list = project.get('projectTaskList', [])
    item = {
        'key': '000',
        'workDuration': str(duration),
        'workMatters': f'"{matters}"\n',
        'workDate': date,
        'projectId': project['id'],
        'workOvertime': '',
        'userCompellation': USER_NAME,
        'isOverTime': False,
        'taskId': task['id'],
        'taskList': task_list,
        'projectName': project['projectName'],
        'taskName': task['taskName'],
        'projectType': 1,
        'projectCode': project['projectCode'],
        'projectUsername': '',
        'projectUserName': project.get('userName', ''),
        'userId': USER_ID,
        'auditing': 0,
    }
    return api_post(cookie, '/api/dailyReport/add', [item])


def submit_update(cookie, existing, date, duration, matters, project, task):
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
        'userId': USER_ID,
        'userCompellation': USER_NAME,
        'createTime': existing.get('createTime'),
        'updateTime': existing.get('updateTime'),
        'auditing': existing.get('auditing', 0),
        'createBy': existing.get('createBy', USER_ID),
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


def main():
    print('=' * 50)
    print('  工时自动填报工具')
    print('=' * 50)

    # Cookie
    cookie = load_cookie()
    if not cookie:
        print(f'\n首次使用，请输入Cookie')
        print('（浏览器Console执行 copy(document.cookie) 获取）')
        cookie = input('Cookie: ').strip()
        if not cookie:
            print('Cookie不能为空')
            return
        # 验证
        result = api_post(cookie, '/api/project/list',
                          {'pageNum': 1, 'pageSize': 1, 'projectType': 1})
        if result.get('code') != '200':
            print('Cookie无效')
            return
        save_cookie(cookie)
        print('Cookie已保存')
    else:
        print(f'\n从 {COOKIE_FILE} 读取Cookie')
        # 验证
        result = api_post(cookie, '/api/project/list',
                          {'pageNum': 1, 'pageSize': 1, 'projectType': 1})
        if result.get('code') != '200':
            print('Cookie已过期，请重新输入')
            cookie = input('Cookie: ').strip()
            result = api_post(cookie, '/api/project/list',
                              {'pageNum': 1, 'pageSize': 1, 'projectType': 1})
            if result.get('code') != '200':
                print('Cookie仍然无效')
                return
            save_cookie(cookie)
            print('Cookie已更新')
    print('Cookie OK')

    # 选择Excel文件
    excel_path = select_excel()
    if not excel_path:
        print('未选择文件')
        return
    print(f'\n读取: {excel_path}')
    records = read_excel(excel_path)
    if not records:
        print('无有效记录')
        return
    print(f'共 {len(records)} 个工作日 ({records[0]["date"]} ~ {records[-1]["date"]})')

    # 日期范围
    year = records[0]['date'][:4]
    print(f'\n年份: {year}，输入日期范围（回车=全部）：')
    start = input('  起始 (MMDD): ').strip()
    end = input('  结束 (MMDD): ').strip()
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

        existing = fetch_existing(cookie, r['date'])
        if existing:
            result = submit_update(cookie, existing, r['date'], r['duration'], r['matters'], project, task)
        else:
            result = submit_add(cookie, r['date'], r['duration'], r['matters'], project, task)

        if result.get('code') == '200':
            success += 1
            print(f'  [{i+1:>3}/{total}] OK {r["date"]} [{code}]')
        else:
            fail_list.append(r['date'])
            msg = result.get('msg', str(result))
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
