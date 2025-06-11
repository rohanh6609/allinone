import asyncio
import aiohttp
import requests
import json
from pyrogram import Client, filters
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode
import cloudscraper
import os
import base64
import jwt
import datetime
from config import *
import time
from pyrogram.types import InputMediaDocument

time = datetime.datetime.now().strftime("%d-%m-%Y")
channel_id = LOGS_CHANNEL

def decrypt1(enc):
    enc = b64decode(enc.split(':')[0])
    key = '638udh3829162018'.encode('utf-8')
    iv = 'fedcba9876543210'.encode('utf-8')
    if len(enc) == 0:
        return ""
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(enc), AES.block_size)
    return plaintext.decode('utf-8')

def decode_base64(encoded_str):
    try:
        decoded_bytes = base64.b64decode(encoded_str)
        decoded_str = decoded_bytes.decode('utf-8')
        return decoded_str
    except Exception as e:
        return f"Error decoding string: {e}"

def decrypt(text):
    key = '638udh3829162018'
    key = bytearray(key.encode())
    iv_key = 'fedcba9876543210'
    iv_key = bytearray(iv_key.encode())
    bs = 16

    PADDING = lambda s: s + (bs - len(s) % bs) * bytes([bs - len(s) % bs])
    generator = AES.new(key, AES.MODE_CBC, iv_key)
    text += '=' * ((4 - len(text) % 4) % 4)

    try:
        decrpyt_bytes = base64.b64decode(text)
    except base64.binascii.Error:
        return 'Invalid base64-encoded string'

    meg = generator.decrypt(decrpyt_bytes)
    try:
        result = meg[:-meg[-1]].decode('utf-8')
    except Exception:
        result = 'Decoding failed, please try again!'
    return result

bot = Client("bot",
             bot_token=bot_token,
             api_id=api_id,
             api_hash=api_hash)

app = bot

@app.on_message(filters.command("apiv1"))
async def api_v1(bot, m):
    editable = await bot.send_message(m.chat.id, "**🌐 Enter API :**")
    input01: Message = await bot.listen(editable.chat.id)
    raw_text05 = input01.text
    await input01.delete(True)
    await editable.edit("Send **Token** or **ID & Password** 🧲")
    
    login_hdr = {
        'Client-Service': 'Appx',
        'Auth-Key': 'appxapi',
        'User-ID': '-2',
        'language': 'en',
        'device_type': 'ANDROID',
        'Host': f'{raw_text05}',
        'Connection': 'Keep-Alive',
        'User-Agent': 'okhttp/4.9.1',
    }

    data = {
        'email': '',
        'password': '',
        'devicetoken': 'evxVp-BBB3I:APA91bFSglfbsDx7kYeVNnOszxud1cUyXj-p54ejyaSvItm7p5EPH9iyZKKk0N66gROVI3cRWVg1Bvy4tuBsU1VPulrjKqoiF644NI9dqKUswrnOc5TLd0ZHrTZsgy6tSLpcG6OMz7F',
        'mydeviceid': 'e4be9d04e8ca6e44',
    }

    input: Message = await bot.listen(editable.chat.id)
    raw_text = input.text
    await input.delete(True)

    if "*" in raw_text:
        data["email"] = raw_text.split("*")[0]
        data["password"] = raw_text.split("*")[1]
        scraper = cloudscraper.create_scraper()
        url = f"https://{raw_text05}/post/userLogin"
        html = scraper.post(url, data=data, headers=login_hdr).content
        output = json.loads(html)
        token = output.get("data", {}).get("token", None)
        userid = output.get("data", {}).get("userid", None)
    else:
        token = raw_text
        userid = jwt.decode(token, options={"verify_signature": False}).get('id')

    hdr = {
        'Client-Service': 'Appx',
        'Auth-Key': 'appxapi',
        'User-ID': userid,
        'Authorization': token,
        'language': 'en',
        'device_type': 'ANDROID',
        'Host': f'{raw_text05}',
        'Connection': 'Keep-Alive',
        'User-Agent': 'okhttp/4.9.1',
    }

    scraper = cloudscraper.create_scraper()
    html1 = scraper.get("https://"+raw_text05+"/get/mycourse?userid=" + userid, headers=hdr).content
    output1 = json.loads(html1)
    topicid = output1["data"]

    cool = ""
    total_links = 0
    for data in topicid:
        aa = f" `{data['id']}` » {data['course_name']} ✳️ ₹{data['price']}\n\n"
        if len(f'{cool}{aa}') > 4096:
            print(aa)
            cool = ""
        cool += aa

    await bot.send_message(channel_id, f"`{raw_text05}`\n\n<pre>{token}</pre>{cool}")
    await editable.edit(f"**Login successful....✅**\n\n**BATCH ID** ➤ **BATCH NAME**\n\n{cool}\nSEND ID:")
    input1 = await bot.listen(editable.chat.id)
    raw_text1 = input1.text

    course_title = ""
    for data in topicid:
        if data['id'] == raw_text1:
            batch_logo = data['course_thumbnail']
            course_title = data['course_name'].replace('/','')

    scraper = cloudscraper.create_scraper()
    html3 = scraper.get("https://"+raw_text05+"/get/allsubjectfrmlivecourseclass?courseid=" + raw_text1, headers=hdr).content
    output3 = json.loads(html3)
    topicid = output3["data"]

    for topic in topicid:
        tids = topic["subjectid"]
        subject_title = topic["subject_name"].replace(':', '')
        scraper = cloudscraper.create_scraper()
        html4 = scraper.get("https://"+raw_text05+"/get/alltopicfrmlivecourseclass?courseid=" + raw_text1 + "&subjectid=" + tids, headers=hdr).content
        output4 = json.loads(html4)
        vv = output4["data"]
        tsids_list = []
        
        for data in vv:
            tsids = data['topicid']
            tsids_list.append(tsids)
            
        for tsids in tsids_list:
            scraper = cloudscraper.create_scraper()
            html5 = scraper.get("https://"+raw_text05+"/get/livecourseclassbycoursesubtopconceptapiv3?topicid=" + tsids + "&start=-1&courseid=" + raw_text1 + "&subjectid=" + tids, headers=hdr).content
            output5 = json.loads(html5)
            gg = output5["data"]

            for video in gg:
                if video.get("download_link"):
                    video_title = video["Title"].replace('||', '').replace('#', '').replace(':', '').replace(',', '').replace('@', '').replace('|', '')
                    fuck = video["download_link"]
                    video_link = decrypt((fuck).split(":")[0])
                    with open(f"{course_title}.txt", 'a') as f:
                        f.write(f"({subject_title}) {video_title}:{video_link}\n")
                        total_links += 1

                    p1 = video.get("pdf_link", "")
                    p2 = video.get("pdf_link2", "")
                    if p1 and p1 != fuck:
                        dp1 = decrypt1(p1)
                        pp1 = video.get("pdf_encryption_key", "")
                        pkey = pp1.split(":")[0]
                        mkey = '638udh3829162018'.encode()
                        miv = 'fedcba9876543210'.encode()
                        unpad = lambda s: s[:-ord(s[len(s) - 1:])]
                        decipher = AES.new(mkey, AES.MODE_CBC, miv)
                        p1key = (unpad(decipher.decrypt(b64decode(pkey))).decode('utf-8'))
                        print(f"({subject_title}) {vt} PDF:{dp1}*{p1key}")
                        with open(f"{course_title}.txt", 'a') as f:
                            f.write(f"({subject_title}) {vt} PDF:{dp1}*{p1key}\n")
                            total_links += 1
                    if p2:
                        dp2 = decrypt1(p2)
                        pp2 = video.get("pdf_encryption_key", "")
                        pkey = pp2.split(":")[0]
                        mkey = '638udh3829162018'.encode()
                        miv = 'fedcba9876543210'.encode()
                        unpad = lambda s: s[:-ord(s[len(s) - 1:])]
                        decipher = AES.new(mkey, AES.MODE_CBC, miv)
                        p2key = (unpad(decipher.decrypt(b64decode(pkey))).decode('utf-8'))
                        print(f"({subject_title}) {vt} PDF-2:{dp2}*{p2key}")
                        with open(f"{course_title}.txt", 'a') as f:
                            f.write(f"({subject_title}) {vt} PDF-2:{dp2}*{p2key}\n")
                            total_links += 1
                else:
                    video_id = video["id"]
                    video_title = video["Title"].replace('||', '').replace('#', '').replace(':', '').replace(',', '').replace('@', '').replace('|', '')
                    scraper = cloudscraper.create_scraper()
                    html6 = scraper.get("https://"+raw_text05+"/get/fetchVideoDetailsById?course_id=" + raw_text1 + "&video_id=" + video_id + "&ytflag=0&folder_wise_course=0", headers=hdr).content
                    print(html6)
                    r4 = html6.json()
                    vt = r4["data"].get("Title", "")
                    vl = r4["data"].get("download_link", "")
                    if vl:
                        dvl = decrypt1(vl)
                        print(f"({subject_title}) {vt}:{dvl}")
                        with open(f"{course_title}.txt", 'a') as f:
                            f.write(f"({subject_title}) {vt}:{dvl}\n")
                            total_links += 1
                    else:
                        encrypted_links = r4["data"].get("encrypted_links", [])
                        for link in encrypted_links:
                            a = link.get("path")
                            k = link.get("key")
                            if a and k:
                                k1 = decrypt1(k)
                                k2 = decode_base64(k1)
                                da = decrypt1(a)
                                da = decrypt1(a)
                                print(f"({subject_title}) {vt}:{da}*{k2}")
                                with open(f"{course_title}.txt", 'a') as f:
                                    f.write(f"({subject_title}) {vt}:{da}*{k2}\n")
                                    total_links += 1

                    if "material_type" in r4["data"]:
                        mt = r4["data"]["material_type"]
                        if mt == "VIDEO":
                            p1 = r4["data"].get("pdf_link", "")
                            p2 = r4["data"].get("pdf_link2", "")
                            if p1:
                                dp1 = decrypt1(p1)
                                pp1 = r4["data"].get("pdf_encryption_key", "")
                                pkey = pp1.split(":")[0]
                                mkey = '638udh3829162018'.encode()
                                miv = 'fedcba9876543210'.encode()
                                unpad = lambda s: s[:-ord(s[len(s) - 1:])]
                                decipher = AES.new(mkey, AES.MODE_CBC, miv)
                                p1key = (unpad(decipher.decrypt(b64decode(pkey))).decode('utf-8'))
                                print(f"({subject_title}) {vt} PDF:{dp1}*{p1key}")
                                with open(f"{course_title}.txt", 'a') as f:
                                    f.write(f"({subject_title}) {vt} PDF:{dp1}*{p1key}\n")
                                    total_links += 1
                            if p2:
                                dp2 = decrypt1(p2)
                                pp2 = r4["data"].get("pdf_encryption_key", "")
                                pkey = pp2.split(":")[0]
                                mkey = '638udh3829162018'.encode()
                                miv = 'fedcba9876543210'.encode()
                                unpad = lambda s: s[:-ord(s[len(s) - 1:])]
                                decipher = AES.new(mkey, AES.MODE_CBC, miv)
                                p2key = (unpad(decipher.decrypt(b64decode(pkey))).decode('utf-8'))
                                print(f"({subject_title}) {vt} PDF-2:{dp2}*{p2key}")
                                with open(f"{course_title}.txt", 'a') as f:
                                    f.write(f"({subject_title}) {vt} PDF-2:{dp2}*{p2key}\n")
                                    total_links += 1

    caption_details = raw_text05.replace("api.cloudflare.net.in", "").replace("api.classx.co.in", "").replace("api.teachx.co.in", "").replace("api.appx.co.in", "").replace("apinew.teachx.in", "").replace("api.akamai.net.in", "").replace("api.teachx.in", "").replace("cloudflare.net.in", "").upper()
    file1 = InputMediaDocument(f"{course_title}.txt", caption=f"\n\n**🌀 Batch Id :** {raw_text1}\n\n**✳️ App :** {caption_details} (AppX V1)\n\n**📚 Batch :** `{course_title}`\n\n**🔰 Total Links :** {total_links}\n\n**🌪️ Thumb :** `{batch_logo}`\n\n**❄️ Date :** {time}")
    await bot.send_media_group(m.chat.id, [file1])
    await bot.send_media_group(channel_id, [file1])
    os.remove(f"{course_title}.txt")
    await bot.send_message(m.chat.id, f"`{raw_text05}`\n<pre>{token}</pre>", thumb=image)
