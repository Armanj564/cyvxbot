import os, random, string, asyncio, aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PROXY_USER = "ainrlxbm"
PROXY_PASS = "xidaz286f66o"
PROXY_LIST = [
    ("31.59.20.176", 6754), ("198.23.239.134", 6540), ("45.38.107.97", 6014),
    ("107.172.163.27", 6543), ("198.105.121.200", 6462), ("216.10.27.159", 6837),
    ("142.111.67.146", 5611), ("191.96.254.138", 6185), ("31.58.9.4", 6077), ("64.137.10.153", 5803),
]
scanning = False
found_list = []
scanned_count = 0
scan_length = 4
scan_delay = 0.5

def random_proxy():
    ip, port = random.choice(PROXY_LIST)
    return "http://" + PROXY_USER + ":" + PROXY_PASS + "@" + ip + ":" + str(port)

def gen_username(length):
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))

async def check_instagram(session, username, proxy):
    try:
        url = "https://www.instagram.com/" + username + "/"
        h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
        async with session.get(url, headers=h, proxy=proxy, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as r:
            if r.status == 404:
                return True
            if r.status == 200:
                text = await r.text()
                return "ProfilePage" not in text
            return None
    except Exception:
        return None

async def check_tiktok(session, username, proxy):
    try:
        url = "https://www.tiktok.com/@" + username
        h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
        async with session.get(url, headers=h, proxy=proxy, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as r:
            text = await r.text()
            if "user-not-found" in text or "10202" in text:
                return True
            if "uniqueId" in text:
                return False
            return None
    except Exception:
        return None

async def scan_loop(context, chat_id):
    global scanning, found_list, scanned_count
    status_msg = await context.bot.send_message(chat_id, "\U0001f50d Scanning...\n\n\U0001f4ca Scanned: 0 | \u2705 Found: 0\n\nSend /stop to stop.")
    async with aiohttp.ClientSession() as session:
        while scanning:
            username = gen_username(scan_length)
            proxy = random_proxy()
            ig = await check_instagram(session, username, proxy)
            tt = await check_tiktok(session, username, proxy)
            scanned_count += 1
            plats = []
            if ig is True:
                plats.append("\U0001f4f8 Instagram")
            if tt is True:
                plats.append("\U0001f3b5 TikTok")
            if plats:
                plats_str = ", ".join(plats)
                found_list.append(username + " - " + plats_str)
                await context.bot.send_message(chat_id, "\u2705 FOUND: " + username + "\n\U0001f310 Free on: " + plats_str + "\n\n\U0001f517 instagram.com/" + username + "\n\U0001f517 tiktok.com/@" + username)
            if scanned_count % 20 == 0:
                try:
                    await status_msg.edit_text("\U0001f50d Scanning...\n\n\U0001f4ca Scanned: " + str(scanned_count) + " | \u2705 Found: " + str(len(found_list)) + "\n\nSend /stop to stop.")
                except Exception:
                    pass
            await asyncio.sleep(scan_delay)
    await context.bot.send_message(chat_id, "\U0001f6d1 Scan stopped!\n\n\U0001f4ca Scanned: " + str(scanned_count) + "\n\u2705 Found: " + str(len(found_list)))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "hunter"
    await update.message.reply_text(
        "\U0001f47e Hey " + name + ", welcome to 4Char Hunter!\n\n"
        "\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\n"
        "\U0001f3af I hunt rare short usernames across Instagram and TikTok using proxies!\n\n"
        "\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\n"
        "\U0001f4e1 Scanning:\n"
        "\u25b8 /scan - Start hunting usernames\n"
        "\u25b8 /stop - Stop the scan\n\n"
        "\U0001f4cb Results:\n"
        "\u25b8 /list - Show all found usernames\n"
        "\u25b8 /export - Download list as txt file\n"
        "\u25b8 /clear - Clear the found list\n"
        "\u25b8 /stats - View scan statistics\n\n"
        "\u2699\ufe0f Settings:\n"
        "\u25b8 /setspeed fast or slow\n"
        "\u25b8 /setlength 3 or 4 or 5\n"
        "\u25b8 /platforms - Show active platforms\n\n"
        "\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\n"
        "\U0001f680 Send /scan to start hunting!"
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global scanning, scanned_count, found_list
    if scanning:
        await update.message.reply_text("\u26a0\ufe0f Already scanning! Send /stop first.")
        return
    scanning = True
    scanned_count = 0
    found_list = []
    asyncio.create_task(scan_loop(context, update.effective_chat.id))
    spd = "fast" if scan_delay == 0.3 else "slow"
    await update.message.reply_text("\U0001f680 Scan started!\n\n\U0001f4cf Length: " + str(scan_length) + "\n\u26a1 Speed: " + spd + "\n\U0001f310 Platforms: Instagram, TikTok\n\n\U0001f514 Will notify you every time I find one!")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global scanning
    if not scanning:
        await update.message.reply_text("\u26a0\ufe0f Not scanning right now.")
        return
    scanning = False
    await update.message.reply_text("\U0001f6d1 Stopping scan...")

async def list_found(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not found_list:
        await update.message.reply_text("\U0001f4ed Nothing found yet. Send /scan to start!")
        return
    await update.message.reply_text("\u2705 Found " + str(len(found_list)) + " username(s):\n\n" + "\n".join("\u25b8 " + u for u in found_list))

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not found_list:
        await update.message.reply_text("\U0001f4ed Nothing to export yet!")
        return
    with open("found.txt", "w") as f:
        f.write("\n".join(found_list))
    await update.message.reply_document(document=open("found.txt", "rb"), filename="found_usernames.txt", caption="\U0001f4c4 " + str(len(found_list)) + " username(s) exported!")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global found_list
    found_list = []
    await update.message.reply_text("\U0001f5d1\ufe0f List cleared!")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    spd = "fast" if scan_delay == 0.3 else "slow"
    status = "\u2705 scanning" if scanning else "\U0001f534 idle"
    await update.message.reply_text("\U0001f4ca Stats:\n\n\U0001f50d Scanned: " + str(scanned_count) + "\n\u2705 Found: " + str(len(found_list)) + "\n\U0001f4cf Length: " + str(scan_length) + "\n\u26a1 Speed: " + spd + "\n\U0001f501 Status: " + status)

async def setspeed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global scan_delay
    if not context.args:
        await update.message.reply_text("\u2699\ufe0f Usage: /setspeed fast or slow")
        return
    speed = context.args[0].lower()
    if speed == "fast":
        scan_delay = 0.3
        await update.message.reply_text("\u26a1 Speed set to fast!")
    elif speed == "slow":
        scan_delay = 2.0
        await update.message.reply_text("\U0001f422 Speed set to slow!")
    else:
        await update.message.reply_text("\u26a0\ufe0f Use: /setspeed fast or slow")

async def setlength(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global scan_length
    if not context.args:
        await update.message.reply_text("\u2699\ufe0f Usage: /setlength 3 or 4 or 5")
        return
    try:
        length = int(context.args[0])
        if length not in [3, 4, 5]:
            raise ValueError
        scan_length = length
        await update.message.reply_text("\U0001f4cf Length set to " + str(length) + "!")
    except Exception:
        await update.message.reply_text("\u26a0\ufe0f Use: /setlength 3 or 4 or 5")

async def platforms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\U0001f310 Active Platforms:\n\n\u25b8 \U0001f4f8 Instagram\n\u25b8 \U0001f3b5 TikTok\n\n\u2705 Reports username if free on any platform.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("list", list_found))
    app.add_handler(CommandHandler("export", export))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("setspeed", setspeed))
    app.add_handler(CommandHandler("setlength", setlength))
    app.add_handler(CommandHandler("platforms", platforms))
    print("Bot running...")
    app.run_polling()
