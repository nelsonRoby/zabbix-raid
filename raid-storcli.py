# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================
@Time : 2025/4/16 10:47
@Author : Nelson
@File : raid_storcli.py
============================
"""
import sys
import json

import subprocess

def run_storcli(args):
    """执行storcli命令并返回输出"""
    try:
        cmd = ['sudo', '/opt/MegaRAID/storcli/storcli64'] + args
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing storcli: {e.stderr}")
        return None

##LSI Controller
def discover_ctrl():
    output = run_storcli(['show', 'all', 'J'])
    if not output:
        return
    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {str(e)}")
        return

    ctrl_list = []
    for ctrl in data.get('Controllers', []):
        response_data = ctrl.get('Response Data', {})
        for ctk in response_data['System Overview']:
            ctrl_sn = json.loads(run_storcli(['/c{}'.format(ctk['Ctl']),'show', 'J']))['Controllers'][0]['Response Data']['Serial Number']
            ctrl_list.append({"{#CTRL.ID}":ctk['Ctl'],"{#CTRL.MODEL}":ctk['Model'],"{#CTRL.SN}":ctrl_sn})
    return ctrl_list

##RAID LOGICAL
def discover_ld():
    output = run_storcli([ '/call/vall','show', 'J'])
    if not output:
        return
    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {str(e)}")
        return

    pd_list = []

    for pd in data.get('Controllers', []):
        cmd_data = pd.get('Command Status', {})
        response_data = pd.get('Response Data', {})
        for pdk in response_data['Virtual Drives']:
            pd_list.append({"{#CTRL.ID}":cmd_data['Controller'],
                            "{#LD.ID}":pdk['DG/VD'].split('/')[1],
                            "{#LD.NAME}":pdk['Name'],
                            "{#LD.RAID}":pdk['TYPE'],
                            "{#LD.STATE}":pdk['State'].replace("Optl","Optimal")})
    return pd_list

#physical drive
def discover_drives(cid):
    output = run_storcli(['/c{}/eall/sall'.format(cid), 'show', 'J'])
    if not output:
        return
    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {str(e)}")
        return

    drive_list = []
    for controller in data.get('Controllers', []):
        response_data = controller.get('Response Data', {})
        # 尝试不同版本的数据路径
        drives = response_data.get('Drive Information') or \
                     response_data.get('PD LIST') or \
                     response_data.get('Physical Drives', [])

        for drive in drives:
            # 处理不同字段命名
            encl = drive.get('EID:Slt') or drive.get('Enclosure')
            eid = encl.split(':')[0]
            sid = encl.split(':')[1]
            pd_info = json.loads(run_storcli(['/c{}/e{}/s{}'.format(cid,eid,sid),'show','all', 'J']))['Controllers'][0]['Response Data']
            pd_sn = pd_info["Drive /c{}/e{}/s{} - Detailed Information".format(cid,eid,sid)]["Drive /c{}/e{}/s{} Device attributes".format(cid,eid,sid)]['SN']

            pd_state = pd_info["Drive /c{}/e{}/s{} - Detailed Information".format(cid,eid,sid)]["Drive /c{}/e{}/s{} State".format(cid,eid,sid)]

            drive_list.append({
                "{#CTRL.ID}": str(cid),
                "{#ED.ID}": str(eid),
                "{#PD.ID}": str(sid),
                "{#PD.SN}": pd_sn,
                "{#PD.STATE}": drive.get('State').replace("Onln","Online"),
                "{STATE.Media}": pd_state['Media Error Count'],
                "{STATE.Other}": pd_state['Other Error Count'],
                "{STATE.Temp}": pd_state['Drive Temperature'].split('C')[0],
            })

    #print(json.dumps({"data": drive_list}, indent=4))
    return drive_list

def get_ctrl_temp(cid):
    output = run_storcli([f'/c{cid}','show', 'temperature', 'J'])
    if not output:
        return
    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {str(e)}")
        return


    response_data = data.get('Controllers', [])[0].get('Response Data', {})
    temp_value = response_data.get('Controller Properties')[0]['Value']

    return temp_value


if __name__ == '__main__':
    #main()
    args = sys.argv

    if args[1] == 'lld':
        if args[2] == 'ad':
            res_ctrl = discover_ctrl()
            print(json.dumps({"data": res_ctrl}))
        elif args[2] == 'ld':
            res_ld = discover_ld()
            print(json.dumps({"data": res_ld}))
        elif args[2] == 'pd':
            res_pd = discover_drives(0)
            print(json.dumps({"data": res_pd}))
        else:
            print(json.dumps({"data": []}))
    elif args[1] == 'health':
        if args[2] == 'ad':
            if args[4] == 'temperature':
                print(get_ctrl_temp(args[3]))

        elif args[2] == 'ld':
            res_ld = discover_ld()
            for llk in res_ld:
                if args[3] == str(llk['{#CTRL.ID}']) and args[4] == str(llk['{#LD.ID}']):
                    print(llk['{#LD.STATE}'])

        elif args[2] == 'pd':
            res_pd = discover_drives(0)
            for pk in res_pd:
                if args[3] == pk['{#CTRL.ID}'] and args[4] == pk['{#PD.ID}'] and args[5] == pk['{#ED.ID}']:
                    print(pk['{#PD.STATE}'])
        else:
            print()
    else:
        print()
