import re
import os
import asyncio
import aiohttp
from config import *
from pyrogram import filters, Client as app
from pyrogram.types import Message
from bs4 import BeautifulSoup
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode
import aiofiles

# AES Key और IV (16 Bytes की होनी चाहिए)

# AES Key aur IV (16 Bytes hone chahiye)
  


def modify_urls_in_txt(input_file, output_file):
    """
    Reads a text file, replaces DRM video URLs with the playlist format, removes '/wv', and writes the modified content to a new file.
    
    Args:
        input_file (str): Path to the input text file.
        output_file (str): Path to save the modified output file.
    """
    with open(input_file, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Regular expression to modify URLs:
    # 1. Removes "/wv" after "/drm"
    # 2. Replaces "master.m3u8" with "playlist.m3u8"
    modified_content = re.sub(
        r"(https://media-cdn\.classplusapp\.com/drm)/wv(/[\w\d]+/)[\w\d]+/master\.m3u8",
        r"\1\2playlist.m3u8",
        content
    )

    # Save the modified content
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(modified_content)


def count_batches_and_format_ids(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    
    # Extract batch IDs (before ' - ' separator)
    batch_ids = [line.split(" - ")[0].strip() for line in lines if " - " in line]
    
    # Get total batch count
    total_batches = len(batch_ids)
    
    # Format batch IDs with '&' separator
    formatted_batch_ids = "&".join(batch_ids)
    
    return total_batches, formatted_batch_ids






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

KEY = b'^#^#&@*HDU@&@*()'   
IV = b'^@%#&*NSHUE&$*#)' 
# Encryption function
def enc_url(url):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    ciphertext = cipher.encrypt(pad(url.encode(), AES.block_size))
    return "helper://" + b64encode(ciphertext).decode('utf-8')  # helper:// prefix add karna

# Function to split name & URL properly
def split_name_url(line):
    match = re.search(r"(https?://\S+)", line)  # Find `https://` ya `http://` ke baad ka URL
    if match:
        name = line[:match.start()].strip().rstrip(":")  # URL se pehle ka text (extra `:` hatao)
        url = match.group(1).strip()  # Sirf URL
        return name, url
    return line.strip(), None  # Agar URL nahi mila, to pura line name maan lo

# Function to encrypt file URLs
"""def encrypt_file(input_file):
    output_file = "encrypted_" + input_file  # Output file ka naam
    with open(input_file, "r", encoding="utf-8") as f, open(output_file, "w", encoding="utf-8") as out:
        for line in f:
            name, url = split_name_url(line)  # Sahi tarike se name aur URL split karo
            #if url:
                #enc = enc_url(url)  # Encrypt URL
            out.write(f"{name}: {enc}\n")  # Ek hi `:` likho
            else:
                out.write(line.strip() + "\n")  # Agar URL nahi mila to line jaisa hai waisa likho
    return output_file"""
def encrypt_file(input_file):
    output_file = "encrypted_" + input_file  # Output file ka naam
    with open(input_file, "r", encoding="utf-8") as f, open(output_file, "w", encoding="utf-8") as out:
        for line in f:
            name, url = split_name_url(line)  # Sahi tarike se name aur URL split karo
            if url:  # Check if a URL exists
                out.write(f"{name}: {url}\n")  # Write the original URL, not encrypted
            else:  # If no URL, write the line as is
                out.write(line.strip() + "\n")  # Agar URL nahi mila to line jaisa hai waisa likho
    return output_file




api = "https://api.classplusapp.com"
batch_dict = {}



async def get_app_name(org_id, default_image):
    url = f"https://{org_id}.courses.store/"  # Construct the URL based on org ID
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                
                # Extract app name
                meta_title = soup.find("meta", {"property": "og:title"})
                app_name = meta_title["content"] if meta_title else "❌ App name not found!"
                
                # Extract image URL, fallback to default image if not found
                meta_image = soup.find("meta", {"property": "og:image"})
                image_url = meta_image["content"] if meta_image else default_image
                
                return app_name, image_url
            else:
                return f"❌ Error: {response.status}", default_image

async def get_list_token(orgid: str) -> str:
    """Fetches list_token from the organization API."""
    
    url = f"{api}/v2/course/preview/org/info"
    headers = {'tutorwebsitedomain': f'https://{orgid}.courses.store'}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
    
    return data["data"]["hash"]

async def fetch_batches_new(orgid: str, list_token: str) -> list:
    """Fetches batch details using the new method."""
    HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "EN",
    "api-version": "22",
    "origin": f"https://{orgid}.courses.store",
    "referer": f"https://{orgid}.courses.store/",
    "region": "IN",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}
    category_url = f"{api}/v2/course/preview/category/list/{list_token}?"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(category_url, headers=HEADERS) as response:
            response.raise_for_status()
            data = await response.json()
    
    categories = data.get("data", {}).get("categoryList", [])
    if not categories:
        return []

    batch_details = []
    async with aiohttp.ClientSession() as session:
        for category in categories:
            category_id = category["id"]
            list_api = f"{api}/v2/course/preview/similar/{list_token}?filterId=[1]&sortId=[7]&subCatList=&mainCategory={category_id}&limit=200&offset=0"
            
            async with session.get(list_api, headers=HEADERS) as response:
                response.raise_for_status()
                data = await response.json()
            
            batches = data.get("data", {}).get("coursesData", [])
            for batch in batches:
                batch_id = str(batch["id"])  # Ensure batch_id is a string
                batch_name = batch["name"]
                price = batch["price"]

                # Append to batch details list
                batch_details.append(f"{batch_id} - {batch_name} (₹{price})")

                # Store details in dictionary
                batch_dict[batch_id] = {
                    "name": batch_name,
                    "imageUrl": batch.get("imageUrl"),  # Using .get() for safety
                    "price": price
                }
    
    return batch_details



async def download_image(image_url, save_path="thumb.jpg", default_thumb=image):
    """Download image from URL and save it, fallback to default thumbnail if download fails."""
    if not image_url or image_url == "❌ Image not found!":
        return default_thumb  # Return default thumbnail if image URL is missing

    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status == 200:
                async with aiofiles.open(save_path, 'wb') as file:
                    await file.write(await response.read())
                return save_path  # Return the saved image path
    return default_thumb  # Return default image if download fails


async def fetch_batches_old(orgid: str, list_token: str) -> list:
    """Fetches batch details using the old method."""
    HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "EN",
    "api-version": "22",
    "origin": f"https://{orgid}.courses.store",
    "referer": f"https://{orgid}.courses.store/",
    "region": "IN",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}
    batch_url_template = f"{api}/v2/course/preview/similar/{list_token}?filterId=[1]&sortId=[7]&subCatList=&mainCategory={{}}&limit=200&offset=0"
    batch_details = []

    async with aiohttp.ClientSession() as session:
        list_api = batch_url_template.format("")
        async with session.get(list_api, headers=HEADERS) as response:
            response.raise_for_status()
            data = await response.json()
        
        batches = data.get("data", {}).get("coursesData", [])
        for batch in batches:
                batch_id = str(batch["id"])  # Ensure batch_id is a string
                batch_name = batch["name"]
                price = batch["price"]

                # Append to batch details list
                batch_details.append(f"{batch_id} - {batch_name} (₹{price})")

                # Store details in dictionary
                batch_dict[batch_id] = {
                    "name": batch_name,
                    "imageUrl": batch.get("imageUrl"),  # Using .get() for safety
                    "price": price
                }
    
    return batch_details

async def get_list_batches(orgid: str) -> str:
    """
    Fetch and return a formatted string list of all batch courses.

    Args:
        orgid (str): Organization ID (subdomain of courses.store).

    Returns:
        str: Formatted list of batch details.
    """
    list_token = await get_list_token(orgid)
    batch_details = await fetch_batches_new(orgid, list_token)

    # Agar new method fail ho jaaye toh old method use karein
    if not batch_details:
        batch_details = await fetch_batches_old(orgid, list_token)

    return "\n".join(batch_details) if batch_details else "No batches found."

# Run script
# orgid = "xvvel"  # Replace this with the actual org ID


async def get_token(orgid: str, bid: str) -> str:
    """
    Retrieve the token (hash) for a specific course using organization ID and batch ID.

    Args:
        orgid (str): The organization ID.
        bid (str): The batch/course ID.

    Returns:
        str: The token (hash) for the course.
    """
    url = f'{api}/v2/course/preview/org/info?courseId={bid}'
    headers = {'tutorwebsitedomain': f'https://{orgid}.courses.store'}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
    return data["data"]["hash"]

async def get_bname(token: str) -> str:
    """
    Fetch the batch name using the course token.

    Args:
        token (str): The course token.

    Returns:
        str: The formatted batch name (course name + organization name).
    """
    url = f'{api}/v2/course/preview/{token}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
    cname = re.sub(r'[^\w\s-]', ' ', data["data"]["details"]["name"])
    iname = data["data"]["orgDetails"]["name"]
    return f"{cname} ({iname})"


  # Encrypted file ka naam return karega


async def get_content(api_url: str) -> dict:
    """
    Fetch content from the Classplus API.

    Args:
        api_url (str): The API endpoint URL.

    Returns:
        dict: The JSON response content.
    """
    headers = {
        'authority': 'api.classplusapp.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'EN',
        'api-version': '22'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

def transform_url(thumbnail_url: str, name: str, fname: str) -> str:
    """
    Transform thumbnail URLs into playable media URLs based on patterns.

    Args:
        thumbnail_url (str): The original thumbnail URL.
        name (str): The content name.
        fname (str): The folder prefix.

    Returns:
        str: The transformed URL string or empty string if no match.
    """
    url_transforms = {
        # r"(.*?/[a-zA-Z0-9]+-[a-zA-Z0-9]+-[a-zA-Z0-9]+-[a-zA-Z0-9]+-[a-zA-Z0-9]+).jpg": 
        #     lambda match: f"{match.group(1)}.m3u8",

        r"https://media-cdn.classplusapp.com/videos.classplusapp.com/vod-[a-zA-Z0-9]+/(.*?)/snapshots/[a-zA-Z0-9-]+-\d+\.jpg": 
            lambda match: f"https://media-cdn.classplusapp.com/alisg-cdn-a.classplusapp.com/{match.group(1)}/master.m3u8",

        r"https://media-cdn.classplusapp.com/videos.classplusapp.com/[a-zA-Z0-9]+/[a-zA-Z0-9]+/thumbnail.png": 
            lambda match: None,

        r"https://media-cdn.classplusapp.com/videos.classplusapp.com/[a-zA-Z0-9]+/(.*?)\.jpeg": 
            lambda match: f"https://media-cdn.classplusapp.com/alisg-cdn-a.classplusapp.com/b08bad9ff8d969639b2e43d5769342cc62b510c4345d2f7f153bec53be84fe35/{match.group(1)}/master.m3u8",

        r"https://media-cdn.classplusapp.com(/.*?/.*?/.*?/)thumbnail.png": 
            lambda match: f"https://media-cdn.classplusapp.com{match.group(1)}master.m3u8",

        r"https://cpvideocdn.testbook.com/streams/(.*?)/thumbnail.png": 
            lambda match: f"https://cpvideocdn.testbook.com/{match.group(1)}/playlist.m3u8"
    }


    for pattern, transform in url_transforms.items():
        match = re.search(pattern, thumbnail_url)
        if match:
            transformed_url = transform(match)
            return f"{fname} {name}:{transformed_url}\n"
    return ""

async def process_folder_content(folder_content: dict, fname: str = '', token: str = '', bname: str = '', editable: Message = None) -> str:
    """
    Recursively process folder content to extract media URLs and show live updates.

    Args:
        folder_content (dict): The folder content JSON.
        fname (str): The folder name prefix.
        token (str): The course token.
        bname (str): The batch name.
        editable (Message): The Telegram message object to update live.

    Returns:
        str: The formatted content string with media URLs.
    """
    fetched_contents = ""
    for item in folder_content['data']:
        if item['contentType'] in (2, 3):  # Video or similar content
            name = item['name']
            if 'thumbnailUrl' in item:
                fetched_contents += transform_url(item['thumbnailUrl'], name, fname)
        elif item['contentType'] == 1:  # Folder
            folder_id = item['id']
            new_fname = f"{fname} {item['name']}"
            # Update the Telegram message with the current folder nam
            sub_content = await get_content(f"{api}/v2/course/preview/content/list/{token}?folderId={folder_id}&limit=1000")
            fetched_contents += await process_folder_content(sub_content, fname=new_fname, token=token, bname=bname, editable=editable)
    return fetched_contents

def write_to_file(content: str, bname: str) -> str:
    """
    Write content to a file, removing lines containing 'None'.

    Args:
        content (str): The content to write.
        bname (str): The batch name for the filename.

    Returns:
        str: The path to the written file.
    """
    output_file = f"{bname}.txt"
    
    # Filter out lines containing 'None'
    filtered_content = "\n".join([line for line in content.split("\n") if "None" not in line])
    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(filtered_content)
    
    return output_file


# @app.on_message(filters.command("classplus2"))
async def classplus_download(app: app, message: Message):
    """
    Telegram bot command to download Classplus course content with live folder updates.

    Args:
        app (Client): The Pyrogram client.
        message (Message): The incoming message object.
    """
    user_id = message.chat.id
    mention = message.from_user.mention

    try:
        # Ask for organization ID
        editable = await app.send_message(message.chat.id, "🚀**अपना Organization ID दर्ज करें**\n📌 Please enter your **Org ID** to proceed: ")
        org_msg = await app.listen(editable.chat.id)
        orgid = org_msg.text.strip()
        await org_msg.delete(True)

        # Get and display course list
        # cm_list = await get_list_course(orgid)
        app_name, image_url = await get_app_name(orgid, image)
        extracting_prompt = (
            f"🔎 **बैच डिटेल्स एक्सट्रैक्ट की जा रही हैं... कृपया प्रतीक्षा करें!**\n\n"
            f"📲 **Application:** `{app_name}`\n"
            f"🆔 **Org CODE:** `{orgid}`\n"
        )
        text = await app.send_message(message.chat.id, extracting_prompt)
        final_batches_list = await get_list_batches(orgid)

        # Remove duplicates by converting to a set and then back to a string
        unique_batches = "\n".join(set(final_batches_list.split("\n")))
        batches_file = f"{app_name}.txt"
        with open(batches_file, 'w', encoding='utf-8') as f:
            f.write(unique_batches)
        total_batches, batch_id_string = count_batches_and_format_ids(batches_file)
        app_name, image_url = await get_app_name(orgid, image)
        thumb_path = await download_image(image_url)
        batch_string = batch_id_string if len(batch_id_string) <= 500 else "None"
        caption = (
                f"🚀 **Application: {app_name}**\n"
                f"🏢 **Organization:** `{orgid}`\n"
                f"📦 **Total Batches:** `{total_batches}`\n\n"
                
                f"🔗 **To Download All Batches (सभी बैच डाउनलोड करने के लिए):**\n"
                f"   ┌───📥 **Batch String:** `{batch_string}`\n"
                f"   └──────────────────────────\n"
            )
        await app.send_document(user_id, batches_file, caption=caption, thumb=thumb_path)
        await text.delete(True)
        os.remove(batches_file)
        if thumb_path:
            os.remove(thumb_path)

        # course_list_text = "Available Courses:\n\n" + "\n".join(cm_list)
        
        await editable.edit("**Please enter the batch ID or for multiple batches send like this - 132437&24536&5361&6351**")
        bid_msg = await app.listen(editable.chat.id)
        bid_input = bid_msg.text.strip()
        await bid_msg.delete(True)
        await editable.edit(f"extracting...")

        try:
            # Extract batch IDs from input
            batch_ids = bid_input.split('&')
            batch_ids = [bid.strip() for bid in batch_ids]

            # Extract available batch IDs from the list
            course_ids = [line.split(" - ")[0].strip() for line in final_batches_list.split("\n") if " - " in line]

            # Validate batch IDs
            invalid_batches = [bid for bid in batch_ids if bid not in course_ids]
            if invalid_batches:
                await editable.edit(f"Invalid batch IDs: {', '.join(invalid_batches)}. Please choose from the list.")
                return

            # Process each batch separately and send immediately after extraction
            for bid in batch_ids:
                try:
                    
                    token = await get_token(orgid, bid)
                    bname = await get_bname(token)
                    app_name, image_url = await get_app_name(orgid, image)
                    details = batch_dict.get(bid, {})
                    thu = details.get('imageUrl', '#')
                    if thu and thu != "#":  # Ensure the image URL is valid
                        try:
                            thumb_p = await download_image(thu)  # Download image and get local file path
                            if not thumb_p:  # If download fails, use default image
                                thumb_p = image
                        except Exception as e:
                            print(f"Error downloading image: {e}")
                            thumb_p = image
                    else:
                        thumb_p = image
                    # thumb_p = await download_image(thu) 
                    try:
                        thum = await app.send_photo(
                            chat_id=editable.chat.id, 
                            photo=thumb_p, 
                            caption=f"Processing batch: `{bname}`"
                        )
                    except Exception as e:
                        print(f"Error sending image: {e}")
                        thum = await editable.edit(f"Processing batch: `{bname}` (Image error)")

                    api_url = f'{api}/v2/course/preview/content/list/{token}?folderId=0&limit=1000'
                    content = await get_content(api_url)
                    
                    fetched_contents = await asyncio.gather(process_folder_content(content, token=token, bname=bname, editable=editable))
                    # await thum.delete()

                    if fetched_contents:
                        output_file1 = write_to_file("\n".join(fetched_contents), bname)
                        output_file2 = f"{bname}_helper.txt"
                        modify_urls_in_txt(output_file1, output_file2)
                        output_file = encrypt_file(output_file2)
                    else:
                        await app.send_message(user_id, f"❌ No content found for batch `{bid}`.")
                        continue

                    # Send file immediately after extraction
                    total, pdfs, videos = count_urls(output_file2)
                    details = batch_dict.get(bid, {})
                    caption = (
                        f"📌 **Batch Details:**\n"
                        f"   ┌───📚 **Batch: {bname}**\n"
                        f"   └──────────────────────────\n\n"

                        f"📂 **Batch Info:**\n"
                        f"   ┌───📲 **Application: {app_name}**\n"
                        f"   │    🆔 **Org CODE:** `{orgid}`\n"
                        f"   │    🌀 **Batch ID:** `{bid}`\n"
                        f"   │    💰 **Price: सिर्फ ₹ {details.get('price', 'N/A')}**\n"
                        f"   │    🖼 **Thumbnail:** 🔗 [Click Here]({details.get('imageUrl', '#')})\n"
                        f"   └──────────────────────────\n\n"

                        f"📂 **Content Overview:**\n"
                        f"   ┌───🔗 **Total Links:** `{total}`\n"
                        f"   │    ├ 🎥 **Videos:** `{videos}` 📹\n"
                        f"   │    └ 📄 **PDFs:** `{pdfs}` ❌\n"
                        f"   └──────────────────────────\n\n"

                        f"🔒 **Security Notice:**\n"
                        f"   ┌───🔹 **All URLs are encrypted.** 🔑\n"
                        f"   │    🔹 **Use our bot to upload.** 🤖\n"
                        f"   └──────────────────────────\n\n"

                        f"🏆 **Extracted By:** `{mention}`\n"
                    )



                    try:
                        await app.send_document(user_id, document=output_file, caption=caption, thumb=image)
                        #await app.send_document(LOGS_CHANNEL, document=output_file2, caption=caption, thumb=image)
                    finally:
                        os.remove(output_file)
                        os.remove(output_file1)
                        os.remove(output_file2)

                except aiohttp.ClientError as e:
                    error_msg = f"🌐 **Network Error in Batch {bid}**\n\n🚨 `{str(e)}`"
                    await app.send_message(user_id, error_msg)

                except KeyError as e:
                    error_msg = f"📌 **API Response Error in Batch {bid}**\n\n❗ Missing key: `{str(e)}`"
                    await app.send_message(user_id, error_msg)

                except Exception as e:
                    error_msg = f"⚠️ **Unexpected Error in Batch {bid}**\n\n💢 `{str(e)}`"
                    await app.send_message(user_id, error_msg)

            # Final message after all batches are processed
            await editable.delete(True)
            await app.send_message(user_id, "🎉 **Extraction Successful!**")


        except aiohttp.ClientError as e:
            await editable.edit(f"Network error: {str(e)}")
        except KeyError as e:
            await editable.edit(f"API response error: Missing key {str(e)}")
    except Exception as e:
            await editable.edit(f"Error: {str(e)}")
