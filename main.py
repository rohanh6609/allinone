from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging
from mmoonngg import *
from thefinalcode import *
from pw import *
from pw_ll import *
from appx_v1 import api_v1
from appx_v3 import *
from appxw import *
from config import *
from pyrogram.errors import FloodWait
import time 
from datetime import datetime
from khan import *
from classplus import *
from pyrogram.errors import UserNotParticipant

FORCE_SUB_CHANNEL = FORCE_CHANNEL

ALL_USERS = set()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

THREADPOOL = ThreadPoolExecutor(max_workers=1000)

bot = Client("bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

OWNER_ID = 1671836568

image_list = [
    "logo.jpg",
    "logo1.jpg",
    "logo2.jpg"
]

@bot.on_message(filters.command("broadcast") & filters.user(OWNER))
async def broadcast(_, message: Message):
    text_to_send = (
        message.reply_to_message.text if message.reply_to_message 
        else message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 
        else None
    )

    if not text_to_send:
        return await message.reply_text("❌ **Reply to a message OR provide text after command to broadcast!**")

    exmsg = await message.reply_text("🚀 **Broadcasting started...**")
    
    all_users = db["users"].distinct("user_id")  

    sent_count = 0
    for user_id in all_users:
        try:
            await bot.send_message(user_id, text_to_send)
            sent_count += 1
            await asyncio.sleep(0.2)  
        except:
            pass  

    await exmsg.edit_text(f"✅ **Broadcast Completed!**\n📩 **Message Sent To:** `{sent_count}` Users")

@bot.on_message(filters.command("add") & filters.user(OWNER))
async def add_admin_command(_, message):
    try:
        args = message.text.split()[1:]  

        if len(args) < 2:
            return await message.reply_text("❌ **Usage:** `/add <user_id> <time>`\n\n**Example:** `/add 123456789 1 day`")

        user_id = int(args[0])
        time_str = " ".join(args[1:])

        time_units = {
            "day": "days",
            "days": "days",
            "hour": "hours",
            "hours": "hours",
            "minute": "minutes",
            "min": "minutes",
            "minutes": "minutes",
            "month": "months",
            "months": "months",
            "year": "years",
            "years": "years"
        }

        time_parts = time_str.split()
        if len(time_parts) != 2 or time_parts[1].lower() not in time_units:
            return await message.reply_text("❌ **Invalid format!**\nUse: `/add <user_id> <time>`\n\n✅ **Example:** `/add 123456789 1 day`")

        time_value = int(time_parts[0])
        time_unit = time_units[time_parts[1].lower()]

        current_time = datetime.datetime.utcnow()
        if time_unit == "days":
            expiry_time = current_time + timedelta(days=time_value)
        elif time_unit == "hours":
            expiry_time = current_time + timedelta(hours=time_value)
        elif time_unit == "minutes":
            expiry_time = current_time + timedelta(minutes=time_value)
        elif time_unit == "months":
            expiry_time = current_time + timedelta(days=30 * time_value)
        elif time_unit == "years":
            expiry_time = current_time + timedelta(days=365 * time_value)

        expiry_str = expiry_time.strftime("%Y-%m-%d %H:%M:%S UTC")

        existing_admin = admins_col.find_one({"user_id": user_id})

        if existing_admin:
            admins_col.update_one({"user_id": user_id}, {"$set": {"expiry": expiry_time}})
            action = "Updated"
        else:
            admins_col.insert_one({"user_id": user_id, "expiry": expiry_time})
            action = "Added"

        user = await bot.get_users(user_id)

        success_msg = f"""✅ **ᴘʀᴇᴍɪᴜᴍ {action} ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**  

👤 **ᴜꜱᴇʀ:** {user.mention}  
⚡ **ᴜꜱᴇʀ ɪᴅ:** `{user_id}`  
⏰ **ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ:** `{time_value} {time_unit}`  

⏳ **ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ:** `{current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}`  
⌛ **ᴇxᴘɪʀʏ ᴅᴀᴛᴇ:** `{expiry_str}`  

__**Powered by ★·.·★ Ⓢⓐⓚⓢⓗⓐⓜ Ⓑⓗⓐⓘⓨⓐ ★·.·★**__"""

        await message.reply_text(success_msg, disable_web_page_preview=True)

        await bot.send_message(
            chat_id=user_id,
            text=f"👋 **ʜᴇʏ {user.mention},**\nᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴘᴜʀᴄʜᴀꜱɪɴɢ ᴘʀᴇᴍɪᴜᴍ.\n\n⏰ **ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ:** `{time_value} {time_unit}`\n⏳ **ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ:** `{current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}`\n⌛ **ᴇxᴘɪʀʏ ᴅᴀᴛᴇ:** `{expiry_str}`",
            disable_web_page_preview=True
        )

    except ValueError:
        await message.reply_text("❌ Invalid format! Please use: `/add <user_id> <time>`\n\n**Example:** `/add 123456789 1 day`")
    except Exception as e:
        await message.reply_text(f"⚠️ **Error:** `{str(e)}`")

@bot.on_message(filters.command("remove") & filters.user(OWNER))
async def remove_admin_command(_, message):
    try:
        args = message.text.split()[1:]  

        if not args:
            return await message.reply_text("❌ **Usage:** `/remove <user_id>`\n\n**Example:** `/remove 123456789`")

        user_id = int(args[0])

        existing_admin = admins_col.find_one({"user_id": user_id})

        if not existing_admin:
            return await message.reply_text("⚠️ **User is not an admin!**")

        admins_col.delete_one({"user_id": user_id})

        user = await bot.get_users(user_id)

        success_msg = f"""✅ **Admin Removed Successfully!**  

👤 **User:** {user.mention}  
⚡ **User ID:** `{user_id}`  

__**Powered by ★·.·★ Ⓢⓐⓚⓢⓗⓐⓜ Ⓑⓗⓐⓘⓨⓐ ★·.·★**__"""

        await message.reply_text(success_msg, disable_web_page_preview=True)

        await bot.send_message(
            chat_id=user_id,
            text=f"❌ **Hey {user.mention},**\nYour **premium access** has been **revoked**.\nIf you believe this is a mistake, contact support.",
            disable_web_page_preview=True
        )

    except ValueError:
        await message.reply_text("❌ **Invalid format!** Please use: `/remove <user_id>`\n\n**Example:** `/remove 123456789`")
    except Exception as e:
        await message.reply_text(f"⚠️ **Error:** `{str(e)}`")

"""@bot.on_message(filters.command("getfree") & filters.private)
async def getfree_command(_, message):
    user_id = message.from_user.id
    current_time = datetime.datetime.utcnow()
    existing_admin = admins_col.find_one({"user_id": user_id, "expiry": {"$gt": current_time}})
    
    if existing_admin:
        await message.reply_text("You already have premium access.")
    else:
        await message.reply_text(
            "Click the button below to get 30 days of free premium access!",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Get Free Premium", callback_data="get_free_premium")]]
            )
        )

@bot.on_callback_query()
async def handle_callback_query(_, query):
    if query.data == "get_free_premium":
        user_id = query.from_user.id
        current_time = datetime.datetime.utcnow()
        expiry_time = current_time + datetime.timedelta(days=30)
        
        admins_col.update_one(
            {"user_id": user_id},
            {"$set": {"expiry": expiry_time}},
            upsert=True
        )
        
        await query.answer("Premium access granted!")
        await query.edit_message_text("You have claimed your free premium access!")
        
        user = await bot.get_users(user_id)
        await bot.send_message(
            chat_id=user_id,
            text=(
                f"👋 **Hey {user.mention},**\n"
                "You have been granted 30 days of free premium access.\n\n"
                f"⏳ **Joining date:** `{current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}`\n"
                f"⌛ **Expiry date:** `{expiry_time.strftime('%Y-%m-%d %H:%M:%S UTC')}`"
            ),
            disable_web_page_preview=True
        )"""

@bot.on_message(filters.command("admins") & filters.user(OWNER))
async def admins_command(_, message):
    requester = message.from_user.id  
    admins_text = await fetch_admins(requester, bot)  
    await message.reply(admins_text)

@bot.on_message(filters.command("myplan"))
async def my_plan_command(_, message):
    user_id = message.from_user.id  
    plan_details = await my_plan(user_id)  
    await message.reply(plan_details)  

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚡ 𝐏𝐡𝐲𝐬𝐢𝐜𝐬 𝐖𝐚𝐥𝐥𝐚𝐡 - 𝐋𝐨𝐠𝐢𝐧 𝐍𝐨𝐰 🔓", callback_data="pw")],
        [InlineKeyboardButton("📚 𝐂𝐥𝐚𝐬𝐬𝐏𝐥𝐮𝐬 - 𝐄𝐱𝐭𝐫𝐚𝐜𝐭 𝐋𝐢𝐧𝐤𝐬 🔗", callback_data="CLP")],
        
        [
            InlineKeyboardButton("📜 𝐀𝐩𝐩𝐱 𝐕𝟏 - 𝐄𝐧𝐚𝐛𝐥𝐞𝐝 ✅", callback_data="appx_v1"),
            InlineKeyboardButton("📜 𝐀𝐩𝐩𝐱 𝐕𝟑 - 𝐔𝐩𝐝𝐚𝐭𝐞𝐝 🔥", callback_data="appx_v3"),
        ],
        
        [InlineKeyboardButton("📖 𝐊𝐡𝐚𝐧 𝐒𝐢𝐫 - 𝐅𝐮𝐥𝐥 𝐀𝐜𝐜𝐞𝐬𝐬 🎓", callback_data="khan")],
        
        [
            InlineKeyboardButton("🔙 𝐆𝐨 𝐁𝐚𝐜𝐤", callback_data="back"),
            InlineKeyboardButton("🏠 𝐌𝐚𝐢𝐧 𝐌𝐞𝐧𝐮", callback_data="home"),
            InlineKeyboardButton("💠 𝐏𝐫𝐞𝐦𝐢𝐮�{m 𝐙𝐨𝐧𝐞 ✨", callback_data="premium_menu"),
        ],
        
        [InlineKeyboardButton("📩 𝐍𝐞𝐞𝐝 𝐇𝐞𝐥𝐩? 𝐂𝐨𝐧𝐭𝐚𝐜𝐭 𝐒𝐮𝐩𝐩𝐨𝐫𝐭 💬", url="https://t.me/scammerbotaccess")],
    ]
    
    return InlineKeyboardMarkup(keyboard)

CLPTEXT_BUTTON = [ 
    [
        InlineKeyboardButton('🚀 Generate Token 🔑', callback_data="GTOK"),
    ],
    [
        InlineKeyboardButton('📜 Retrieve Text (Using Your Token) 🔍', callback_data="GTEXT"),
    ],
    [
        InlineKeyboardButton('❌ Close Window 🙅🏻‍♂️', callback_data="CLOSE"),
    ],   
]
CLPTOK_BUTTON = [
    [
        InlineKeyboardButton('📩 Send OTP to Email ✉️', callback_data="email_otp"),
    ],   
    [
        InlineKeyboardButton('📱 Send OTP to Mobile 📲', callback_data="mob_otp"),
    ],
    [
        InlineKeyboardButton('🔙 Back to Menu ⏪', callback_data="BACK2"),
    ], 
    [
        InlineKeyboardButton('😣 Exit & Close 😞', callback_data="CLOSE"),
    ],   
]

def premium_keyboard():
    keyboard = [
        [InlineKeyboardButton("🚀 𝗣𝗵𝘆𝘀𝗶𝗰𝘀 𝗪𝗮𝗹𝗹𝗮𝗵 - 𝗨𝗻𝗹𝗼𝗰𝗸 𝗔𝗹𝗹 🔓", callback_data="PWWP")],
        [InlineKeyboardButton("📚 𝗖𝗹𝗮𝘀𝘀𝗣𝗹𝘂𝘀 - 𝗡𝗼 𝗟𝗼𝗴𝗶𝗻 𝗡𝗲𝗲𝗱𝗲𝗱 🆓", callback_data="cpwl")],
        [InlineKeyboardButton("📒 Appx Without Purchase 📒", callback_data="appxwp")],
        [InlineKeyboardButton("📜 𝗣𝗪 𝗝𝗦𝗢𝗡 ➝ 𝗧𝗲𝘅𝘁 𝗖𝗼𝗻𝘃𝗲𝗿𝘁𝗲𝗿 📝", callback_data="pwjsontotxt")],

        [
            InlineKeyboardButton("🔙 𝗕𝗮𝗰𝗸 𝘁𝗼 𝗠𝗮𝗶𝗻 ⏪", callback_data="back_to_main"),
            InlineKeyboardButton("🏠 𝗛𝗼𝗺𝗲 🏡", callback_data="home"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)

@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await save_user(m.from_user.id)
    random_image_url = random.choice(image_list)
    user_id = m.from_user.id
    chat_id = m.chat.id  

    if await check_subscription(bot, user_id, chat_id):
        await m.reply_photo(
            photo=random_image_url,
            caption=(
                "╭━━━━━━━━━━━━━━━━━✦\n"
                "┃ ✨ **BATCH EXTRACTOR BOT** ✨\n"
                "┃ 🚀 *Unlock the Power of Instant Extraction!*\n"
                "┃ 🔓 *No IDs, No Passwords – Just Pure Magic!*\n"
                "╰━━━━━━━━━━━━━━━━━✦\n\n"
                "📂 **Extract Original Links:**\n"
                "╭➤ 🎬 **Videos**\n"
                "├➤ 📚 **Notes**\n"
                "╰➤ 📑 **PDFs & More!**\n\n"
                "<blockquote><b>🔥 **Exclusive Features:** 🔥\n</blockquote></b>"
                "╭➤ 🟢 **Physics Wallah** – Full Access, No Purchase!\n"
                "├➤ 🔵 **Classplus** – Direct Video Links!\n"
                "├➤ 🔴 **APPX V2 & V3** – Always Updated!\n"
                "╰➤ 🟤 **KHAN SIR** – Unlocked Content!\n\n"
                "⚡ **No Encryption – Just Click & Access!**\n\n"
                "💬 **Need Help? Have Questions?**\n"
                "📩 **DM for Instant Support:** [Click Here](https://t.me/botsupdatesbynaruto)\n\n"
                "📌 **Press /extract to See Available Apps & Start Extracting!** 👇"
            ),
            quote=True,
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Join Our Channel 🔥", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
        ])
        await m.reply_text(
            "╭🚫 **ACCESS DENIED!** 🚫\n"
            "┃ 👉 *You need to join our channel to unlock this bot!*\n"
            "┃ 🔹 **Exclusive Features Await You!**\n"
            "╰📢 **Click Below & Become Part of the Community!** 🔥\n\n"
            "📌 **Press /helper after joining to explore all features!** 👇",
            reply_markup=keyboard
        )

@bot.on_message(filters.command(["extract"]))
async def helper(bot: Client, m: Message):
    random_image_url = random.choice(image_list)
    user_id = m.from_user.id
    chat_id = m.chat.id  

    if await check_subscription(bot, user_id, chat_id):
        await m.reply_photo(
            photo=random_image_url,
            caption=(
                "📌 **Select a Service to Begin:**\n\n"
                "╭─── 📂 **Available Services:**\n"
                "├➤ 📚 **Physics Wallah** – Access notes, videos, PDFs\n"
                "├➤ 🎬 **Classplus** – Unlock premium videos\n"
                "├➤ 📲 **AppX V2, V3** – Latest updates & resources\n"
                "├➤ 🎓 **Khan Sir** – Study materials & more\n"
                "╰➤ 🔗 **Other Resources** – Extra content\n\n"
                "🎯 **How to Use?**\n"
                "🔹 *Simply tap on a button below to get started!*\n\n"
                "📢 **Need Assistance?**\n"
                "💬 **DM Support:** [Click Here](https://t.me/botsupdatesbynaruto)\n\n"
                "👇 **Choose an option below & start extracting!**"
            ),
            quote=True,
            reply_markup=main_keyboard()
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Join Our Channel 🔥", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
        ])
        await m.reply_text(
            "🚨 **Access Restricted!** 🚨\n\n"
            "🔒 *This bot is available only for our channel members!*\n"
            "📢 **Join now and unlock premium features instantly!**\n\n"
            "🎁 **Click the button below to subscribe!** ⬇️",
            reply_markup=keyboard
        )

@bot.on_callback_query()
async def callback_handler(bot: Client, query: CallbackQuery):
    if query.data=="CLOSE":
        await query.message.delete(True)
    elif query.data.endswith("CLP"):
        reply_markup = InlineKeyboardMarkup(CLPTEXT_BUTTON)
        text = START_TEXTCP
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup
            )
        except MessageNotModified:
            pass

    elif query.data.endswith("BACK2"):
        reply_markup = InlineKeyboardMarkup(CLPTEXT_BUTTON)
        text = START_TEXTCP
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup
            )
        except MessageNotModified:
            pass

    elif query.data.endswith("GTOK"):
        reply_markup = InlineKeyboardMarkup(CLPTOK_BUTTON)
        text = START_TEXTCP1
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup
            )
        except MessageNotModified:
            pass

    elif query.data.endswith("otp"):
        otp1 = query.data
        otm = otp1.split("_")[0]  
        ct1 = query.message.chat.id

        try:
            await query.edit_message_text(
                text=f"**You selected `{otm}` method to generate your Token:**"
            )
            await query.answer(f"Send in this format: {otm}*OrgCode", show_alert=True)
        except MessageNotModified:
            pass

        await get_cp_token(bot, query, otm, ct1)
        await query.message.delete()

    elif query.data.endswith("GTEXT"):
        ct2 = query.message.chat.id

        try:
            await query.edit_message_text(
                text="**You selected to get text file using your Token:**"
            )
            await query.answer("Send your Auth Token", show_alert=True)
        except MessageNotModified:
            pass

        await get_textcp(bot, query, ct2)

    elif query.data.endswith("khan"):
        user_id = query.from_user.id
        chat_id = query.message.chat.id

        if await check_subscription(bot, user_id, chat_id):
            await khan(bot, query.message)  
        else:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
            ])
            await query.message.reply_text(
                "🚫 **Oops! It seems you're not subscribed to our channel.** 😢\n"
                "✅ **Join us to unlock amazing features and updates!** 🌟\n"
                "👉 **Click the button below to subscribe and continue!** ⬇️",
                reply_markup=keyboard
            )
    elif query.data.endswith("PWWP"):
        await pwwp_callback(bot, query)

    elif query.data.endswith("premium_menu"):
        await premium_menu_callback(client, query)
    
    elif query.data.endswith("appxwp"):
        await appxwp_callback(bot, query)

    elif query.data.endswith("back_to_main"):
        await back_to_main_callback(client, query)

    elif query.data.endswith("home"):
        await home_callback(client, query)

    elif query.data.endswith("back"):
        await back_callback(client, query)

    elif query.data.endswith("pw"):
        await pw_options(bot, query)
    
    elif query.data.endswith("mobile"):
        await pw_mobile_login(bot, query)

    
    elif query.data.endswith("token"):
        await pw_token_login(bot, query)


    elif query.data.endswith("appx_v1"):
        await appx_v1_button_pressed(bot, query)


    elif query.data.endswith("appx_v3"):
        await appx_v3_button_pressed(bot, query)


    elif query.data.endswith("cpwl"):
        await classplus_download_callback(bot, query)


    elif query.data.endswith("pwjsontotxt"):
        await pwjsontotxt_callback(bot, query)

async def premium_menu_callback(client, callback_query):
    await callback_query.edit_message_reply_markup(reply_markup=premium_keyboard())

async def back_to_main_callback(client, callback_query):
    await callback_query.edit_message_reply_markup(reply_markup=main_keyboard())

async def home_callback(client, callback_query):
    await callback_query.edit_message_reply_markup(reply_markup=main_keyboard())

async def back_callback(client, callback_query):
    await callback_query.answer("You are already on the main menu.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_subscription(bot, user_id, chat_id):
    try:
        user_status = await bot.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        status_str = str(user_status.status)  
        logger.info(f"User {user_id} Status: {status_str}")

        if status_str in ["ChatMemberStatus.MEMBER", "ChatMemberStatus.ADMINISTRATOR", "ChatMemberStatus.OWNER"]:
            return True  

    except Exception as e:
        logger.error(f"Error checking subscription: {e}")

    return False  

pw_login_keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("📱 Mobile No.", callback_data="mobile"),
        InlineKeyboardButton("🔑 Token", callback_data="token"),
    ]
])

async def pw_options(bot, query):
    await query.message.reply_text(
        "**CHOOSE FROM BELOW **",
        reply_markup=pw_login_keyboard
    )

async def pw_mobile_login(bot, query):
    await pw_mobile(bot, query.message)  

async def pw_token_login(bot, query):
    await pw_token(bot, query.message)  

async def appx_v1_button_pressed(bot: Client, m: CallbackQuery):
    user_id = m.from_user.id
    chat_id = m.message.chat.id

    if await check_subscription(bot, user_id, chat_id):
        await m.answer()
        await api_v1(bot, m.message)
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
        ])
        await m.reply_text(
                "🚫 **Oops! It seems you're not subscribed to our channel.** 😢\n"
                "✅ **Join us to unlock amazing features and updates!** 🌟\n"
                "👉 **Click the button below to subscribe and continue!** ⬇️",
                reply_markup=keyboard
            )

async def appx_v3_button_pressed(bot: Client, m: CallbackQuery):
    user_id = m.from_user.id
    chat_id = m.message.chat.id

    if await check_subscription(bot, user_id, chat_id):
        await m.answer()
        await appex_v3_txt(bot, m.message)
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
        ])
        await m.reply_text(
                "🚫 **Oops! It seems you're not subscribed to our channel.** 😢\n"
                "✅ **Join us to unlock amazing features and updates!** 🌟\n"
                "👉 **Click the button below to subscribe and continue!** ⬇️",
                reply_markup=keyboard
            )

@bot.on_message(filters.command("stop"))
async def stop_all_processes(client, message):
    global user_states
    user_states.clear()  
    await message.reply_text("❌ **All processes have been stopped!**")  

async def classplus_download_callback(client, callback_query):
    user_id = callback_query.from_user.id
    admin_ids = get_admins()
    admin_ids.append(OWNER)
    print("Admins from DB:", admin_ids)  

    if user_id not in admin_ids:
        try:
            user = await client.get_users(OWNER)  
            owner_username = f"@{user.username}" if user.username else "the owner"
        except Exception:
            owner_username = "the owner"

        await client.send_message(
            callback_query.message.chat.id,
            f"🚫 **Access Denied!** ❌\n\n"
            f"**It looks like you are not authorized to use this feature.** 😔\n"
            f"👉 **For assistance, please contact:** {owner_username} 📩\n\n"
            f"**Thank you for your understanding!** 🙏"
        )
        return  

    await classplus_download(client, callback_query.message)

async def appxwp_callback(bot, callback_query):
    user_id = callback_query.from_user.id

    admin_ids = get_admins()
    admin_ids.append(OWNER)
    print("Admins from DB:", admin_ids)  

    if user_id not in admin_ids:
        try:
            user = await bot.get_users(OWNER)  
            owner_username = f"@{user.username}" if user.username else "the owner"
        except Exception:
            owner_username = "the owner"
        
        await bot.send_message(
            callback_query.message.chat.id,
            f"🚫 **Access Denied!** ❌\n\n"
            f"**It looks like you are not authorized to use this feature.** 😔\n"
            f"👉 **For assistance, please contact:** {owner_username} 📩\n\n"
            f"**Thank you for your understanding!** 🙏"
        )
        return

    await callback_query.answer()
    await process_appxwp(bot, callback_query.message, user_id)

async def pwwp_callback(bot, callback_query):
    user_id = callback_query.from_user.id

    admin_ids = get_admins()
    admin_ids.append(OWNER)
    print("Admins from DB:", admin_ids)  

    if user_id not in admin_ids:
        try:
            user = await bot.get_users(OWNER)  
            owner_username = f"@{user.username}" if user.username else "the owner"
        except Exception:
            owner_username = "the owner"
        
        await bot.send_message(
            callback_query.message.chat.id,
            f"🚫 **Access Denied!** ❌\n\n"
            f"**It looks like you are not authorized to use this feature.** 😔\n"
            f"👉 **For assistance, please contact:** {owner_username} 📩\n\n"
            f"**Thank you for your understanding!** 🙏"
        )
        return

    await callback_query.answer()
    await process_pwwp(bot, callback_query.message, user_id)

def convert_pw_json_to_txt(json_data, output_directory):
    created_files = []

    try:
        data = json.loads(json_data)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON format: {e}")
        return f"Error: Invalid JSON format: {e}"
    except Exception as e:
        logging.error(f"An error occurred while reading the JSON data: {e}")
        return f"Error: An error occurred: {e}"

    for batch_name, batch_data in data.items():
        for subject_name, subject_data in batch_data.items():
            subject_name = subject_name.replace("/", "-").replace("|", "-")
            if subject_name == "Telegram Bot":
                continue

            output_file_path = os.path.join(output_directory, f"encrypted_{subject_name}.txt")

            try:
                with open(output_file_path, 'w', encoding='utf-8') as outfile:
                    for chapter_name, chapter_data in subject_data.items():
                        for content_type in ['videos', 'notes', 'DppNotes', 'DppVideos']:
                            if content_type in chapter_data and isinstance(chapter_data[content_type], list):
                                for item in chapter_data[content_type]:
                                    if isinstance(item, str):
                                        outfile.write(f"{item}\n")
                    outfile.write("\n")

                logging.info(f"Successfully created {output_file_path}")
                created_files.append(output_file_path)
            except Exception as e:
                logging.error(f"Error writing to {output_file_path}: {e}")
                return f"Error writing to {output_file_path}: {e}"

    return created_files, batch_name

async def pwjsontotxt_callback(bot, callback_query):
    user_id = callback_query.from_user.id
    await callback_query.answer()
    admin_ids = get_admins()
    admin_ids.append(OWNER)

    if user_id not in admin_ids:
        try:
            user = await bot.get_users(OWNER_ID)
            owner_username = f"@{user.username}" if user.username else "the owner"
        except Exception:
            owner_username = "the owner"
        await bot.send_message(
                callback_query.message.chat.id,
                f"🚫 **Access Denied!** ❌\n\n"
                f"**It looks like you are not authorized to use this feature.** 😔\n"
                f"👉 **For assistance, please contact:** @{owner_username} 📩\n\n"
                f"**Thank you for your understanding!** 🙏"
            )
        return

    THREADPOOL.submit(asyncio.run, process_pwjsontotxt(bot, callback_query.message, user_id))

async def process_pwjsontotxt(bot: Client, m: Message, user_id: int):
    logging.info(f"Processing PW request from user {user_id}")
    chat_id = m.chat.id
    editable = await m.reply_text("**Please send your JSON file as a document**")

    try:
        input_doc = await bot.listen(chat_id=chat_id, filters=filters.user(user_id) & filters.document, timeout=120)
        file_path = await bot.download_media(input_doc.document)
        logging.info(f"Downloaded file to: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = f.read()
        except Exception as e:
            await editable.edit(f"**Error reading the JSON file: {e}**")
            os.remove(file_path)
            return

        await input_doc.delete(True)
        output_directory = os.path.dirname(file_path)
        created_files, batch_name = convert_pw_json_to_txt(json_data, output_directory)

        if isinstance(created_files, str):
             await editable.edit(created_files)
             return

        await editable.edit("**JSON processed successfully! Text files created**")
        logging.info(f"Sent result message to user {user_id}: Successfully processed")
        caption = f"**Batch Name : ```\n{batch_name}```**"
        for file_path in created_files:
                if "Telegram Bot.txt" in file_path:
                   continue
                try:
                    await bot.send_document(chat_id, document=file_path, caption=caption)
                except Exception as e:
                    await editable.edit(f"**Error sending file : {e}**")
                    logging.error(f"Error sending file to user {user_id}: {e}")

        os.remove(file_path)
        logging.info(f"Deleted temporary JSON file: {file_path}")

    except ListenerTimeout:
        await editable.edit("**Timeout! You took too long to respond**")
        logging.warning(f"Timeout waiting for JSON from user {user_id}")
    except Exception as e:
        logging.exception(f"Error processing JSON from user {user_id}:")
        try:
            await editable.edit(f"**Error: {e}**")
        except:
            logging.error(f"Failed to send error message to user: {e}")
    finally:
        await editable.delete(True)
        await m.reply_text(f"**🔰Done🔰**")
        logging.info(f"Finished processing JSON from user {user_id}")

bot.run()
