import pymongo
from config import *
from datetime import datetime, timedelta
from datetime import datetime
from pyrogram import Client, filters 
# current_time = datetime.utcnow()
# import datetime
# current_time = datetime.datetime.utcnow()


client = pymongo.MongoClient(MONGO_URI)
db = client["telegram_bot"]
admins_col = db["admins"]
users_col = db["users"]

async def save_user(user_id):
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id, "joined_at": datetime.utcnow()})


# 🔥 Function to add an admin
def add_admin(user_id, days):
    expiry_date = datetime.utcnow() + timedelta(days=days)
    admins_col.insert_one({"user_id": user_id, "expiry": expiry_date})
    return f"✅ Admin Added!\n👤 User ID: `{user_id}`\n🗓 Valid for: `{days} days`"

# 🏆 Function to get all active admins
def get_admins():
    current_time = datetime.utcnow()
    admins_data = admins_col.find({"expiry": {"$gte": current_time}}, {"user_id": 1, "expiry": 1, "_id": 0})

    admins_list = []
    admin_ids = []

    for admin in admins_data:
        user_id = admin["user_id"]
        expiry = admin["expiry"]

        remaining_time = expiry - current_time
        days = remaining_time.days
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        admins_list.append(f"👤 **User ID:** `{user_id}`\n⏳ **Expires in:** `{days}d {hours}h {minutes}m`\n")
        admin_ids.append(user_id)

    return admin_ids  # Returns only valid admin IDs

# 📅 Function to check user's admin plan
async def my_plan(user_id):
    current_time = datetime.utcnow()
    admin_data = admins_col.find_one({"user_id": user_id})

    if not admin_data:
        return "❌ You are not an admin."

    expiry = admin_data["expiry"]
    remaining_time = expiry - current_time
    days = remaining_time.days
    hours, remainder = divmod(remaining_time.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    expiry_date = expiry.strftime("%d %B %Y, %I:%M %p")

    return (
        f"🎟 **Admin Plan Details**\n"
        f"👤 **Username:** `{user_id}`\n"
        f"📆 **Expiry Date:** `{expiry_date}`\n"
        f"⏳ **Time Left:** `{days}d {hours}h {minutes}m`\n"
        f"💡 **Enjoy your admin privileges!** 🚀"
    )

async def fetch_admins(requester_id, client: Client):
    if requester_id != OWNER:
        return "🚫 **Access Denied!**\n🔒 Only the **Owner** can use this command."

    current_time = datetime.utcnow()
    active_admins_count = admins_col.count_documents({"expiry": {"$gte": current_time}})

    if active_admins_count == 0:
        return "❌ **No active admins found.**"

    admins_data = admins_col.find({"expiry": {"$gte": current_time}}, {"user_id": 1, "expiry": 1, "_id": 0})
    admins_info = "📜 **Active Admins List:**\n\n"

    for admin in admins_data:
        user_id = admin["user_id"]
        expiry = admin["expiry"]
        remaining_time = expiry - current_time
        days = remaining_time.days
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        expiry_date = expiry.strftime("%d %B %Y, %I:%M %p")

        # ✅ Fetch username from Telegram API
        try:
            user = await client.get_users(user_id)
            username = f"@{user.username}" if user.username else user.first_name
        except Exception:
            username = "Unknown"

        admins_info += (
            f"👤 **Username:** `{username}`\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"📅 **Expiry Date:** `{expiry_date}`\n"
            f"⏳ **Remaining:** `{days}d {hours}h {minutes}m`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

    return admins_info

# 📜 Function to get all user IDs

