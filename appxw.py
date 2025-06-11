import requests
import asyncio
import aiohttp
import json
import zipfile
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os
import base64
from pyrogram import Client, filters
import sys
import re
import requests
import uuid
import random
import string
import hashlib
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait
from pyromod import listen
from pyromod.exceptions.listener_timeout import ListenerTimeout
from pyrogram.types import Message
import pyrogram
from pyrogram import Client, filters
from pyrogram.types import User, Message
from pyrogram.enums import ChatMemberStatus
from pyrogram.raw.functions.channels import GetParticipants
#from config import api_id, api_hash, bot_token, auth_users
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor
THREADPOOL = ThreadPoolExecutor(max_workers=1000)
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def appx_decrypt(enc):
    enc = b64decode(enc.split(':')[0])
    key = '638udh3829162018'.encode('utf-8')
    iv = 'fedcba9876543210'.encode('utf-8')

    if len(enc) == 0:
        return ""

    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(enc), AES.block_size)
    b = plaintext.decode('utf-8')
    url = b
    return url


async def fetch_appx_html_to_json(session, url, headers=None, data=None):
    try:
        if data:
            async with session.post(url, headers=headers, data=data) as response:
                text = await response.text()
        else:
            async with session.get(url, headers=headers) as response:
                text = await response.text()

        try:
            return json.loads(text)

        except json.JSONDecodeError:
            match = re.search(r'\{"status":', text, re.DOTALL)
            if match:
                json_str = text[match.start():]
                try:
                    open_brace_count = 0
                    close_brace_count = 0
                    json_end = -1

                    for i, char in enumerate(json_str):
                        if char == '{':
                            open_brace_count += 1
                        elif char == '}':
                            close_brace_count += 1

                        if open_brace_count > 0 and open_brace_count == close_brace_count:
                            json_end = i + 1
                            break

                    if json_end != -1:
                        return json.loads(json_str[:json_end])
                    else:
                        logging.error("Could not find matching closing brace } . json string: ", json_str)
                        return None
                except json.JSONDecodeError:
                    logging.error("Could not parse JSON from the end. ", json_str)
                    return None
            else:
                logging.error("Could not find JSON at the end. Response content: ", text)
                return None
    except Exception as e:
        logging.exception(f"An error occurred during the request: {e}")
        return None


async def fetch_appx_video_id_details_v2(session, api, selected_batch_id, video_id, ytFlag, headers, folder_wise_course, user_id):
    logging.info(f"User ID: {user_id} - Fetching video details for video ID: {video_id}")
    try:
        res = await fetch_appx_html_to_json(session, f"{api}/get/fetchVideoDetailsById?course_id={selected_batch_id}&folder_wise_course={folder_wise_course}&ytflag={ytFlag}&video_id={video_id}", headers)

        output = []
        if res:
            data = res.get('data', [])

            if data:
                Title = data["Title"]
                uhs_version = data["uhs_version"]
                
                res = await fetch_appx_html_to_json(session, f"{api}/get/get_mpd_drm_links?videoid={video_id}&folder_wise_course={folder_wise_course}", headers)
                if res:
                    drm_data = res.get('data', [])
                    if drm_data and isinstance(drm_data, list) and len(drm_data) > 0:
                        path = appx_decrypt(drm_data[0].get("path", "")) if drm_data and isinstance(drm_data, list) and drm_data and drm_data[0].get("path") else None
                            
                        if path:
                            output.append(f"{Title}:{path}\n")
                                
                pdf_link = appx_decrypt(data.get("pdf_link", "")) if data.get("pdf_link", "") and appx_decrypt(data.get("pdf_link", "")).endswith(".pdf") else None

                is_pdf_encrypted = data.get("is_pdf_encrypted", 0)
                if pdf_link:
                    if is_pdf_encrypted == 1 or is_pdf_encrypted == "1":
                        key = appx_decrypt(data.get("pdf_encryption_key", "")) if data.get("pdf_encryption_key") else None
                        if key:
                            output.append(f"{Title}:{pdf_link}*{key}\n")
                        else:
                            output.append(f"{Title}:{pdf_link}\n")
                    else:
                        output.append(f"{Title}:{pdf_link}\n")
                        
                pdf_link2 = appx_decrypt(data.get("pdf_link2", "")) if data.get("pdf_link2", "") and appx_decrypt(data.get("pdf_link2", "")).endswith(".pdf") else None
                    
                is_pdf2_encrypted = data.get("is_pdf2_encrypted", 0)
                if pdf_link2:
                    if is_pdf2_encrypted == 1 or is_pdf2_encrypted == "1":
                        key = appx_decrypt(data.get("pdf2_encryption_key", "")) if data.get("pdf2_encryption_key") else None
                        if key:
                            output.append(f"{Title}:{pdf_link2}*{key}\n")
                        else:
                            output.append(f"{Title}:{pdf_link2}\n")
                    else:
                        output.append(f"{Title}:{pdf_link2}\n")

            else:
                output.append(f"Did Not Found Course_id : {selected_batch_id} Video_id : {video_id}\n")
        else:
            output.append(f"Did Not Found Course_id : {selected_batch_id} Video_id : {video_id}\n")

        return output

    except Exception as e:
        return [
            f"User ID: {user_id} - An error occurred while fetching details for Course_id : {selected_batch_id}, video ID {video_id}: {str(e)}\n"]


async def fetch_appx_folder_contents_v2(session, api, selected_batch_id, folder_id, headers, folder_wise_course, user_id):
    logging.info(f"User ID: {user_id} - Fetching folder contents for folder ID: {folder_id}")
    try:
        res = await fetch_appx_html_to_json(session, f"{api}/get/folder_contentsv2?course_id={selected_batch_id}&parent_id={folder_id}", headers)
        tasks = []
        output = []
        if "data" in res:
            data = res["data"]
            for item in data:
                Title = item.get("Title")
                video_id = item.get("id")
                ytFlag = item.get("ytFlag")

                if item.get("material_type") == "VIDEO":
                    tasks.append(
                        fetch_appx_video_id_details_v2(session, api, selected_batch_id, video_id, ytFlag, headers, folder_wise_course, user_id))

                elif item.get("material_type") == "FOLDER":
                    tasks.append(
                        fetch_appx_folder_contents_v2(session, api, selected_batch_id, item.get("id"), headers, folder_wise_course, user_id))

        if tasks:
            results = await asyncio.gather(*tasks)
            for res in results:
                if isinstance(res, list):
                    output.extend(res)
                else:
                    output.append(res)
        return output
    except Exception as e:
        return [
            f"User ID: {user_id} - Error fetching folder contents for folder - Course_id : {selected_batch_id}, Folder_id : {folder_id}. Error: {e}\n"]


async def fetch_appx_video_id_details_v3(session, api, selected_batch_id, video_id, ytFlag, headers, user_id):
    logging.info(f"User ID: {user_id} - Fetching video details V3 for video ID: {video_id}")
    try:
        res = await fetch_appx_html_to_json(session, f"{api}/get/fetchVideoDetailsById?course_id={selected_batch_id}&folder_wise_course=0&ytflag={ytFlag}&video_id={video_id}", headers)
        with open("logs.txt", "a") as log_file:
            log_file.write(f"{res}\n")

        output = []
        if res:
            data = res.get('data', [])

            if data:
                Title = data["Title"]
                uhs_version = data["uhs_version"]
                
                res = await fetch_appx_html_to_json(session, f"{api}/get/get_mpd_drm_links?folder_wise_course=0&videoid={video_id}", headers)
                if res:
                    drm_data = res.get('data', [])
                    if drm_data and isinstance(drm_data, list) and len(drm_data) > 0:
                        path = appx_decrypt(drm_data[0].get("path", "")) if drm_data and isinstance(drm_data, list) and drm_data and drm_data[0].get("path") else None
                            
                        if path:
                            output.append(f"{Title}:{path}\n")
                                
                pdf_link = appx_decrypt(data.get("pdf_link", "")) if data.get("pdf_link", "") and appx_decrypt(data.get("pdf_link", "")).endswith(".pdf") else None

                is_pdf_encrypted = data.get("is_pdf_encrypted", 0)
                if pdf_link:
                    if is_pdf_encrypted == 1 or is_pdf_encrypted == "1":
                        key = appx_decrypt(data.get("pdf_encryption_key", "")) if data.get("pdf_encryption_key") else None
                        if key:
                            output.append(f"{Title}:{pdf_link}*{key}\n")
                        else:
                            output.append(f"{Title}:{pdf_link}\n")
                    else:
                        output.append(f"{Title}:{pdf_link}\n")
                        
                pdf_link2 = appx_decrypt(data.get("pdf_link2", "")) if data.get("pdf_link2", "") and appx_decrypt(data.get("pdf_link2", "")).endswith(".pdf") else None

                is_pdf2_encrypted = data.get("is_pdf2_encrypted", 0)
                if pdf_link2:
                    if is_pdf2_encrypted == 1 or is_pdf2_encrypted == "1":
                        key = appx_decrypt(data.get("pdf2_encryption_key", "")) if data.get("pdf2_encryption_key") else None
                        if key:
                            output.append(f"{Title}:{pdf_link2}*{key}\n")
                        else:
                            output.append(f"{Title}:{pdf_link2}\n")
                    else:
                        output.append(f"{Title}:{pdf_link2}\n")
            else:
                output.append(f"Did Not Found Course_id : {selected_batch_id} Video_id : {video_id}\n")
        else:
            output.append(f"Did Not Found Course_id : {selected_batch_id} Video_id : {video_id}\n")

        return output

    except Exception as e:
        return [
            f"User ID: {user_id} - An error occurred while fetching details for Course_id : {selected_batch_id}, video ID {video_id}: {str(e)}\n"]


def find_appx_matching_apis(search_api, appxapis_file="appxapis.json"):
    matched_apis = []

    try:
        with open(appxapis_file, 'r') as f:
            api_data = json.load(f)
    except FileNotFoundError:
        logging.error(f"Error: Could not find the file: {appxapis_file}")
        return matched_apis
    except json.JSONDecodeError:
        logging.error(f"Error: Invalid JSON format in the file: {appxapis_file}")
        return matched_apis

    for item in api_data:
        for term in search_api:
            term = term.strip().lower()
            if term in item["name"].lower() or term in item["api"].lower():
                matched_apis.append(item)

    unique_apis = []
    seen_apis = set()
    for item in matched_apis:
        if item["api"] not in seen_apis:
            unique_apis.append(item)
            seen_apis.add(item["api"])

    return unique_apis


async def process_folder_wise_course_0(session, api, selected_batch_id, headers, user_id):
    logging.info(f"User ID: {user_id} - Processing folder-wise course 0")
    res = await fetch_appx_html_to_json(session, f"{api}/get/allsubjectfrmlivecourseclass?courseid={selected_batch_id}&start=-1", headers)
    all_outputs = []
    tasks = []
    if res and "data" in res:
        subjects = res["data"]
        for subject in subjects:
            subjectid = subject.get("subjectid")

            res2 = await fetch_appx_html_to_json(session, f"{api}/get/alltopicfrmlivecourseclass?courseid={selected_batch_id}&subjectid={subjectid}&start=-1", headers)
            if res2 and "data" in res2:
                topics = res2["data"]
                for topic in topics:
                    topicid = topic.get("topicid")

                    res3 = await fetch_appx_html_to_json(session, f"{api}/get/livecourseclassbycoursesubtopconceptapiv3?topicid={topicid}&start=-1&courseid={selected_batch_id}&subjectid={subjectid}", headers)
                    if res3 and "data" in res3:
                        data = res3["data"]
                        for item in data:
                            Title = item.get("Title")
                            video_id = item.get("id")
                            ytFlag = item.get("ytFlag")

                            if item.get("material_type") == "PDF" or item.get("material_type") == "TEST":
                                Title = item.get("Title")
                                
                                pdf_link = appx_decrypt(item.get("pdf_link", "")) if item.get("pdf_link", "") and appx_decrypt(item.get("pdf_link", "")).endswith(".pdf") else None
                                                              
                                is_pdf_encrypted = item.get("is_pdf_encrypted")

                                if pdf_link:
                                    if is_pdf_encrypted == 1 or is_pdf_encrypted == "1":
                                        key = appx_decrypt(item.get("pdf_encryption_key"))
                                        if key:
                                            all_outputs.append(f"{Title}:{pdf_link}*{key}\n")
                                        else:
                                            all_outputs.append(f"{Title}:{pdf_link}\n")
                                    else:
                                        all_outputs.append(f"{Title}:{pdf_link}\n")
                                        
                                pdf_link2 = appx_decrypt(item.get("pdf_link2", "")) if item.get("pdf_link2", "") and appx_decrypt(item.get("pdf_link2", "")).endswith(".pdf") else None
                                    
                                is_pdf2_encrypted = item.get("is_pdf2_encrypted")

                                if pdf_link2:
                                    if is_pdf2_encrypted == 1 or is_pdf2_encrypted == "1":
                                        key = appx_decrypt(item.get("pdf2_encryption_key"))
                                        if key:
                                            all_outputs.append(f"{Title}:{pdf_link2}*{key}\n")
                                        else:
                                            all_outputs.append(f"{Title}:{pdf_link2}\n")
                                    else:
                                        all_outputs.append(f"{Title}:{pdf_link2}\n")

                            elif item.get("material_type") == "IMAGE":
                                thumbnail = item.get("thumbnail")
                                if thumbnail:
                                    all_outputs.append(f"{Title}:{thumbnail}\n")
                                    
                            elif item.get("material_type") == "VIDEO":
                                if selected_batch_id is not None and video_id is not None and ytFlag is not None:
                                    tasks.append(
                                        fetch_appx_video_id_details_v3(session, api, selected_batch_id, video_id, ytFlag, headers, user_id))
                                else:
                                    logging.warning(
                                        f"User ID: {user_id} - Skipping video due to None value: course_id={selected_batch_id}, video_id={video_id}, ytflag={ytFlag}")
                    else:
                        logging.warning(f"User ID: {user_id} - No data found in livecourseclassbycoursesubtopconceptapiv3 API response")
            else:
                logging.warning(f"User ID: {user_id} - No data found in alltopicfrmlivecourseclass API response")
    else:
        logging.warning(f"User ID: {user_id} - No data found in allsubjectfrmlivecourseclass API response")

    if tasks:
        results = await asyncio.gather(*tasks)
        for res in results:
            all_outputs.extend(res)

    return all_outputs

async def process_folder_wise_course_1(session, api, selected_batch_id, headers, user_id):
    logging.info(f"User ID: {user_id} - Processing folder-wise course 1")
    res = await fetch_appx_html_to_json(session, f"{api}/get/folder_contentsv2?course_id={selected_batch_id}&parent_id=-1", headers)
    all_outputs = []
    tasks = []
    if res and "data" in res:
        data = res["data"]
        for item in data:
            Title = item.get("Title")
            video_id = item.get("id")
            ytFlag = item.get("ytFlag")
            
            if item.get("material_type") == "PDF" or item.get("material_type") == "TEST":
                Title = item.get("Title")
                
                pdf_link = appx_decrypt(item.get("pdf_link", "")) if item.get("pdf_link", "") and appx_decrypt(item.get("pdf_link", "")).endswith(".pdf") else None
                    
                is_pdf_encrypted = item.get("is_pdf_encrypted")

                if pdf_link:
                    if is_pdf_encrypted == 1 or is_pdf_encrypted == "1":
                        key = appx_decrypt(item.get("pdf_encryption_key"))
                        if key:
                            all_outputs.append(f"{Title}:{pdf_link}*{key}\n")
                        else:
                            all_outputs.append(f"{Title}:{pdf_link}\n")
                    else:
                        all_outputs.append(f"{Title}:{pdf_link}\n")
                        
                pdf_link2 = appx_decrypt(item.get("pdf_link2", "")) if item.get("pdf_link2", "") and appx_decrypt(item.get("pdf_link2", "")).endswith(".pdf") else None
                    
                is_pdf2_encrypted = item.get("is_pdf2_encrypted")

                if pdf_link2:
                    if is_pdf2_encrypted == 1 or is_pdf2_encrypted == "1":
                        key = appx_decrypt(item.get("pdf2_encryption_key"))
                        if key:
                            all_outputs.append(f"{Title}:{pdf_link2}*{key}\n")
                        else:
                            all_outputs.append(f"{Title}:{pdf_link2}\n")
                    else:
                        all_outputs.append(f"{Title}:{pdf_link2}\n")

            elif item.get("material_type") == "IMAGE":
                thumbnail = item.get("thumbnail")
                if thumbnail:
                   all_outputs.append(f"{Title}:{thumbnail}\n")
                   
            elif item.get("material_type") == "VIDEO":
                tasks.append(
                    fetch_appx_video_id_details_v2(session, api, selected_batch_id, video_id, ytFlag, headers, 1, user_id))

            elif item.get("material_type") == "FOLDER":
                tasks.append(fetch_appx_folder_contents_v2(session, api, selected_batch_id, item.get("id"), headers, 1, user_id))

    if tasks:
        results = await asyncio.gather(*tasks)
        for res in results:
            all_outputs.extend(res)

    return all_outputs


async def process_appxwp(bot: Client, m: Message, user_id: int):

    loop = asyncio.get_event_loop()
    CONNECTOR = aiohttp.TCPConnector(limit=10000, loop=loop)

    async with aiohttp.ClientSession(connector=CONNECTOR, loop=loop) as session:
        try:
            editable = await m.reply_text("**Enter App Name Or Api**")

            try:
                input1 = await bot.listen(chat_id=m.chat.id, filters=filters.user(user_id), timeout=120)
                api = input1.text
                await input1.delete(True)
            except:
                await editable.edit("**Timeout! You took too long to respond**")
                return

            if not (api.startswith("http://") or api.startswith("https://")):

                api = api
                search_api = [term.strip() for term in api.split()]

                matches = find_appx_matching_apis(search_api)

                if matches:
                    text = ''
                    for cnt, item in enumerate(matches):
                        name = item['name']
                        api = item["api"]
                        text += f'{cnt + 1}. ```\n{name}:{api}```\n'
                        
                    await editable.edit(f"**Send index number of the Batch to download.\n\n{text}**")

                    try:
                        input2 = await bot.listen(chat_id=m.chat.id, filters=filters.user(user_id), timeout=120)
                        raw_text2 = input2.text
                        await input2.delete(True)
                    except:
                        await editable.edit("**Timeout! You took too long to respond**")
                        return
                
                    if input2.text.isdigit() and 1 <= int(input2.text) <= len(matches):
                        selected_api_index = int(input2.text.strip())
                        item = matches[selected_api_index - 1]
                        api = item['api']
                        selected_app_name = item['name']

                    else:
                        await editable.edit("**Error : Wrong Index Number**")
                        return
                else:
                    await editable.edit("**No matches found. Enter Correct App Starting Word**")
                    return
            else:
                api = api = "https://" + api.replace("https://", "").replace("http://", "").rstrip("/")
                selected_app_name = api

            token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6IjEwMTU1NTYyIiwiZW1haWwiOiJhbm9ueW1vdXNAZ21haWwuY29tIiwidGltZXN0YW1wIjoxNzQ1MDc5MzgyLCJ0ZW5hbnRUeXBlIjoidXNlciIsInRlbmFudE5hbWUiOiIiLCJ0ZW5hbnRJZCI6IiIsImRpc3Bvc2FibGUiOmZhbHNlfQ.EfwLhNtbzUVs1qRkMqc3P6ObkKSO0VYWKdAe6GmhdAg"
            userid = "10155562"
                
            headers = {
                'User-Agent': "okhttp/4.9.1",
                'Accept-Encoding': "gzip",
                'client-service': "Appx",
                'auth-key': "appxapi",
         #       'user-id': userid,
         #       'authorization': token,
                'user_app_category': "",
                'language': "en",
                'device_type': "ANDROID"
            }
            
            res1 = await fetch_appx_html_to_json(session, f"{api}/get/courselist", headers)
            res2 = await fetch_appx_html_to_json(session, f"{api}/get/courselistnewv2", headers)

            courses1 = res1.get("data", []) if res1 and res1.get('status') == 200 else []
            total1 = res1.get("total", 0) if res1 and res1.get('status') == 200 else 0

            courses2 = res2.get("data", []) if res2 and res2.get('status') == 200 else []
            total2 = res2.get("total", 0) if res2 and res2.get('status') == 200 else 0
            
            courses = courses1 + courses2
            total = total1 + total2

            if courses:
                if total > 50:
                    text = ''
                    for cnt, course in enumerate(courses):
                        name = course["course_name"]
                        price = course["price"]
                        text += f'{cnt + 1}. {name} 💵₹{price}\n'
                    
                    course_details = f"{user_id}_paid_course_details"
                
                    with open(f"{course_details}.txt", 'w') as f:
                        f.write(text)
                        
                    caption = f"**App Name : ```\n{selected_app_name}```\nBatch Name : ```\nPaid Course Details```**"
                                
                    files = [f"{course_details}.{ext}" for ext in ["txt"]]
                                
                    for file in files:
                        file_ext = os.path.splitext(file)[1][1:]
                        try:
                            with open(file, 'rb') as f:
                                await editable.delete(True)
                                doc = await m.reply_document(document=f, caption=caption, file_name=f"paid course details.{file_ext}")
                                editable = await m.reply_text("**Send index number From the course details txt File to download.**")
                        except FileNotFoundError:
                            logging.error(f"File not found: {file}")
                        except Exception as e:
                            logging.exception(f"Error sending document {file}:")
                        finally:
                            try:
                                os.remove(file)
                                logging.info(f"Removed File After Sending : {file}")
                            except OSError as e:
                                logging.error(f"Error deleting {file}: {e}")
                else:
                    text = ''
                    for cnt, course in enumerate(courses):
                        name = course["course_name"]
                        price = course["price"]
                        text += f'{cnt + 1}. ```\n{name} 💵₹{price}```\n'
                    await editable.edit(f"**Send index number of the course to download.\n\n{text}**")
            else:
                raise Exception("Did not found any course")
                
            try:
                input5 = await bot.listen(chat_id=m.chat.id, filters=filters.user(user_id), timeout=120)
                raw_text5 = input5.text
                await input5.delete(True)
            except:
                await editable.edit("**Timeout! You took too long to respond**")
                return
                
            if input5.text.isdigit() and 1 <= int(input5.text) <= len(courses):
                selected_course_index = int(input5.text.strip())
                course = courses[selected_course_index - 1]
                selected_batch_id = course['id']
                selected_batch_name = course['course_name']
                folder_wise_course = course.get("folder_wise_course", "")
                clean_batch_name = f"{selected_batch_name.replace('/', '-').replace('|', '-')[:min(244, len(selected_batch_name))]}"
                clean_file_name = f"{user_id}_{clean_batch_name}"
                
            else:
                raise Exception("Wrong Index Number")
        
            await editable.edit(f"**Extracting course : {selected_batch_name} ...**")
            
            start_time = time.time()
            
            headers = {
                "Client-Service": "Appx",
                "Auth-Key": "appxapi",
                "source": "website",
                "Authorization": token,
                "User-ID": userid
            }

            all_outputs = []

            if folder_wise_course == 0:
                logging.info(f"User ID: {user_id} - Processing as non-folder-wise (folder_wise_course = 0)")
                all_outputs = await process_folder_wise_course_0(session, api, selected_batch_id, headers, user_id)

            elif folder_wise_course == 1:
                logging.info(f"User ID: {user_id} - Processing as folder-wise (folder_wise_course = 1)")
                all_outputs = await process_folder_wise_course_1(session, api, selected_batch_id, headers, user_id)

            else:
                logging.info(f"User ID: {user_id} - folder_wise_course is neither 0 nor 1.  Processing with both methods sequentially.")
                # Process as if folder_wise_course is 0
                logging.info(f"User ID: {user_id} - Processing as non-folder-wise (folder_wise_course = 0)")
                outputs_0 = await process_folder_wise_course_0(session, api, selected_batch_id, headers, user_id)
                all_outputs.extend(outputs_0)

                # Process as if folder_wise_course is 1
                logging.info(f"User ID: {user_id} - Processing as folder-wise (folder_wise_course = 1)")
                outputs_1 = await process_folder_wise_course_1(session, api, selected_batch_id, headers, user_id)
                all_outputs.extend(outputs_1)
            
            if all_outputs:
            
                with open(f"{clean_file_name}.txt", 'w') as f:
                    for output_line in all_outputs:
                        f.write(output_line)
                        
                end_time = time.time()
                response_time = end_time - start_time
                minutes = int(response_time // 60)
                seconds = int(response_time % 60)

                if minutes == 0:
                    if seconds < 1:
                        formatted_time = f"{response_time:.2f} seconds"
                    else:
                        formatted_time = f"{seconds} seconds"
                else:
                    formatted_time = f"{minutes} minutes {seconds} seconds"
                                    
                caption = f"**App Name : ```\n{selected_app_name}```\nBatch Name : ```\n{selected_batch_name}``````\nTime Taken : {formatted_time}```**"
                                
                files = [f"{clean_file_name}.{ext}" for ext in ["txt"]]
                for file in files:
                    file_ext = os.path.splitext(file)[1][1:]
                    try:
                        with open(file, 'rb') as f:
                            await editable.delete(True)
                            doc = await m.reply_document(document=f, caption=caption, file_name=f"{clean_batch_name}.{file_ext}")
                    except FileNotFoundError:
                        logging.error(f"File not found: {file}")
                    except Exception as e:
                        logging.exception(f"Error sending document {file}:")
                    finally:
                        try:
                            os.remove(file)
                            logging.info(f"Removed File After Sending : {file}")
                        except OSError as e:
                            logging.error(f"Error deleting {file}: {e}")
            else:
                raise Exception("Didn't Found Any Content In The Course")
                
            
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            try:
                await editable.edit(f"**Error : {e}**")
            except Exception as ee:
                logging.error(f"Failed to send error message to user in callback: {ee}")
        finally:
            if session:
                await session.close()
            await CONNECTOR.close()
