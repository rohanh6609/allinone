import os
import requests, re, os, sys, time, datetime, asyncio

def get_folder_content(token,courseId,originalCourseId,folderId):
    vv = ""
    headersg = {"X-Access-Token": f"{token}",
            "User-Agent": "Mobile-Android",
            "Api-Version": "40"}
    paramsg = {'courseId': courseId,'folderId': folderId,'originalCourseId': originalCourseId}
    rb = requests.get('https://api.classplusapp.com/v2/course/content/get', params=paramsg, headers=headersg)
    if rb.status_code == 200:
      cid = rb.json()['data']['courseContent']
      for cid in cid:
        try:
          cc = cid['contentType']
          if cc == 1:
              nmm = str(cid['name']).replace("/","-").replace(":","-")
              lnk, ccid = str(cid['id']), str(cid['contentCourseId'])
              sub_content = get_folder_content(token,ccid,originalCourseId,lnk)
              vv += sub_content
          else:
              try:
                nmm1 = str(cid['name']).replace("/","-").replace(":","-")
                lnkb = str(cid['url'])
                ff = f"{nmm1}:{lnkb}\n"
                vv += ff
              except Exception as e:
                continue
        except Exception as e:
            continue
    return vv
def get_batch(token):
    headers = {"X-Access-Token": f"{token}",
            "User-Agent": "Mobile-Android",
            "Api-Version": "40"}
    paramsa = {'limit': '100','offset': '0',}
    res = requests.get('https://api.classplusapp.com/v2/courses', params=paramsa, headers=headers).json()
    #print(res)
    jh = res['message']
    if res['status'] == 'success':
       cr = (res['data']['courses'])
       vv = ""
       for cr in cr:
           bid = str(cr['id'])
           bnm = str(cr['name'])
           bdt = f"`{bid}` ✳️ {bnm}\n"
           vv += bdt
       return vv
    elif res['status'] == 'failure':
       return jh
    else:
       return None
