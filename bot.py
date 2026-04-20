import os
import socket
import requests
import subprocess
import json
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ─── CONFIG ───────────────────────────────────────────────
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your token from @BotFather

# ─── HELPERS ──────────────────────────────────────────────

def is_valid_ip(ip):
    pattern = r"^\d{1,3}(\.\d{1,3}){3}$"
    return re.match(pattern, ip) is not None

def is_valid_domain(domain):
    pattern = r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    return re.match(pattern, domain) is not None

# ─── /start ───────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 OSINT Tools", callback_data="menu_osint")],
        [InlineKeyboardButton("🌐 Network Tools", callback_data="menu_network")],
        [InlineKeyboardButton("🛡️ Security Info", callback_data="menu_security")],
        [InlineKeyboardButton("📖 Help", callback_data="menu_help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 *CyvxBot — Cybersecurity Toolkit*\n\n"
        "Your all-in-one security assistant.\n"
        "Choose a category below or type a command:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# ─── /help ────────────────────────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Available Commands*\n\n"
        "*OSINT*\n"
        "`/username <name>` — Search username across platforms\n"
        "`/email <email>` — Check if email was breached\n"
        "`/whois <domain>` — WHOIS lookup\n"
        "`/dns <domain>` — DNS records lookup\n"
        "`/ip <ip>` — IP geolocation & info\n"
        "`/subdomains <domain>` — Find subdomains via crt.sh\n"
        "`/dork <query>` — Generate Google dorks\n\n"
        "*Network Tools*\n"
        "`/portscan <host> [ports]` — Scan ports (e.g. /portscan example.com 80,443)\n"
        "`/ping <host>` — Ping a host\n"
        "`/headers <url>` — Get HTTP headers\n"
        "`/robots <domain>` — Get robots.txt\n\n"
        "*Security Info*\n"
        "`/tips` — Random cybersecurity tip\n"
        "`/tools` — Popular security tools list\n"
        "`/cve <keyword>` — Search recent CVEs\n"
        "`/hash <text>` — Hash a string (MD5/SHA)\n"
        "`/encode <text>` — Base64 encode\n"
        "`/decode <text>` — Base64 decode\n"
    )
    msg = update.message or update.callback_query.message
    await msg.reply_text(text, parse_mode="Markdown")

# ─── OSINT: USERNAME ──────────────────────────────────────

async def username_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/username <name>`", parse_mode="Markdown")
        return

    username = context.args[0]
    platforms = {
        "GitHub": f"https://github.com/{username}",
        "Twitter/X": f"https://twitter.com/{username}",
        "Instagram": f"https://instagram.com/{username}",
        "Reddit": f"https://reddit.com/user/{username}",
        "TikTok": f"https://tiktok.com/@{username}",
        "YouTube": f"https://youtube.com/@{username}",
        "Telegram": f"https://t.me/{username}",
        "Pinterest": f"https://pinterest.com/{username}",
        "Twitch": f"https://twitch.tv/{username}",
        "Medium": f"https://medium.com/@{username}",
        "Dev.to": f"https://dev.to/{username}",
        "HackerNews": f"https://news.ycombinator.com/user?id={username}",
    }

    await update.message.reply_text(f"🔍 Checking `{username}` across platforms...", parse_mode="Markdown")

    found = []
    not_found = []

    for platform, url in platforms.items():
        try:
            r = requests.get(url, timeout=5, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                found.append(f"✅ [{platform}]({url})")
            else:
                not_found.append(f"❌ {platform}")
        except:
            not_found.append(f"⚠️ {platform} (timeout)")

    result = f"👤 *Username: `{username}`*\n\n"
    if found:
        result += "*Found on:*\n" + "\n".join(found) + "\n\n"
    if not_found:
        result += "*Not found:*\n" + " | ".join(not_found)

    await update.message.reply_text(result, parse_mode="Markdown", disable_web_page_preview=True)

# ─── OSINT: EMAIL BREACH CHECK ────────────────────────────

async def email_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/email <email>`", parse_mode="Markdown")
        return

    email = context.args[0]
    await update.message.reply_text(f"🔍 Checking `{email}` for breaches...", parse_mode="Markdown")

    try:
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        headers = {
            "hibp-api-key": "YOUR_HIBP_API_KEY",  # Get free key at haveibeenpwned.com
            "user-agent": "CyvxBot"
        }
        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code == 200:
            breaches = r.json()
            names = [b['Name'] for b in breaches]
            result = (
                f"🚨 *Email found in {len(breaches)} breach(es)!*\n\n"
                f"📧 `{email}`\n\n"
                f"*Breaches:* {', '.join(names[:10])}"
            )
        elif r.status_code == 404:
            result = f"✅ Good news! `{email}` was *not found* in any known breaches."
        elif r.status_code == 401:
            result = "⚠️ HIBP API key required. Add your key in bot.py"
        else:
            result = f"⚠️ Could not check. Status: {r.status_code}"
    except Exception as e:
        result = f"❌ Error: {str(e)}"

    await update.message.reply_text(result, parse_mode="Markdown")

# ─── OSINT: WHOIS ─────────────────────────────────────────

async def whois_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/whois <domain>`", parse_mode="Markdown")
        return

    domain = context.args[0]
    await update.message.reply_text(f"🔍 WHOIS lookup for `{domain}`...", parse_mode="Markdown")

    try:
        r = requests.get(f"https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey=at_free&domainName={domain}&outputFormat=JSON", timeout=10)
        data = r.json()
        record = data.get("WhoisRecord", {})

        registrar = record.get("registrarName", "N/A")
        created = record.get("createdDate", "N/A")
        expires = record.get("expiresDate", "N/A")
        registrant = record.get("registrant", {}).get("organization", "N/A")
        country = record.get("registrant", {}).get("country", "N/A")

        result = (
            f"🌐 *WHOIS: {domain}*\n\n"
            f"🏢 Registrar: `{registrar}`\n"
            f"👤 Registrant: `{registrant}`\n"
            f"🌍 Country: `{country}`\n"
            f"📅 Created: `{created[:10] if created != 'N/A' else 'N/A'}`\n"
            f"⏰ Expires: `{expires[:10] if expires != 'N/A' else 'N/A'}`\n"
        )
    except Exception as e:
        result = f"❌ Error: {str(e)}"

    await update.message.reply_text(result, parse_mode="Markdown")

# ─── OSINT: DNS ───────────────────────────────────────────

async def dns_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/dns <domain>`", parse_mode="Markdown")
        return

    domain = context.args[0]
    await update.message.reply_text(f"🔍 DNS records for `{domain}`...", parse_mode="Markdown")

    try:
        r = requests.get(f"https://dns.google/resolve?name={domain}&type=ANY", timeout=10)
        data = r.json()
        answers = data.get("Answer", [])

        if not answers:
            await update.message.reply_text(f"No DNS records found for `{domain}`", parse_mode="Markdown")
            return

        type_map = {1: "A", 2: "NS", 5: "CNAME", 15: "MX", 16: "TXT", 28: "AAAA"}
        result = f"🌐 *DNS Records: {domain}*\n\n"

        for ans in answers[:15]:
            rtype = type_map.get(ans.get("type", 0), str(ans.get("type", "?")))
            data_val = ans.get("data", "")
            result += f"`{rtype}` → `{data_val}`\n"

    except Exception as e:
        result = f"❌ Error: {str(e)}"

    await update.message.reply_text(result, parse_mode="Markdown")

# ─── OSINT: IP INFO ───────────────────────────────────────

async def ip_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/ip <ip_address>`", parse_mode="Markdown")
        return

    ip = context.args[0]
    await update.message.reply_text(f"🔍 Looking up `{ip}`...", parse_mode="Markdown")

    try:
        r = requests.get(f"https://ipapi.co/{ip}/json/", timeout=10)
        data = r.json()

        result = (
            f"🌍 *IP Info: `{ip}`*\n\n"
            f"📍 Location: `{data.get('city', 'N/A')}, {data.get('region', 'N/A')}, {data.get('country_name', 'N/A')}`\n"
            f"🏢 ISP/Org: `{data.get('org', 'N/A')}`\n"
            f"🌐 ASN: `{data.get('asn', 'N/A')}`\n"
            f"🕐 Timezone: `{data.get('timezone', 'N/A')}`\n"
            f"📮 Postal: `{data.get('postal', 'N/A')}`\n"
            f"🗺️ Lat/Lon: `{data.get('latitude', 'N/A')}, {data.get('longitude', 'N/A')}`\n"
        )
    except Exception as e:
        result = f"❌ Error: {str(e)}"

    await update.message.reply_text(result, parse_mode="Markdown")

# ─── OSINT: SUBDOMAINS ────────────────────────────────────

async def subdomains(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/subdomains <domain>`", parse_mode="Markdown")
        return

    domain = context.args[0]
    await update.message.reply_text(f"🔍 Finding subdomains for `{domain}` via crt.sh...", parse_mode="Markdown")

    try:
        r = requests.get(f"https://crt.sh/?q=%.{domain}&output=json", timeout=15)
        data = r.json()

        subs = set()
        for entry in data:
            name = entry.get("name_value", "")
            for sub in name.split("\n"):
                sub = sub.strip().lstrip("*.")
                if sub.endswith(domain):
                    subs.add(sub)

        if not subs:
            result = f"No subdomains found for `{domain}`"
        else:
            subs = sorted(list(subs))[:30]
            result = f"🔎 *Subdomains for {domain}* ({len(subs)} found):\n\n"
            result += "\n".join([f"`{s}`" for s in subs])

    except Exception as e:
        result = f"❌ Error: {str(e)}"

    await update.message.reply_text(result, parse_mode="Markdown")

# ─── OSINT: GOOGLE DORKS ─────────────────────────────────

async def dork(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/dork <domain or keyword>`", parse_mode="Markdown")
        return

    target = " ".join(context.args)
    dorks = [
        f"`site:{target} filetype:pdf`",
        f"`site:{target} filetype:xls OR filetype:xlsx`",
        f"`site:{target} inurl:admin`",
        f"`site:{target} inurl:login`",
        f"`site:{target} intext:password`",
        f"`site:{target} inurl:config`",
        f"`site:{target} \"index of\"`",
        f"`site:{target} inurl:backup`",
        f"`site:{target} ext:sql`",
        f"`site:{target} inurl:phpinfo`",
        f"`\"@{target}\" filetype:xls`",
        f"`site:pastebin.com \"{target}\"`",
    ]

    result = f"🎯 *Google Dorks for: {target}*\n\n"
    result += "\n".join(dorks)
    result += "\n\n⚠️ _Use only on targets you have permission to test._"

    await update.message.reply_text(result, parse_mode="Markdown")

# ─── NETWORK: PORT SCANNER ────────────────────────────────

async def port_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: `/portscan <host> [port1,port2,...]`\nExample: `/portscan example.com 80,443,22`",
            parse_mode="Markdown"
        )
        return

    host = context.args[0]
    common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 5432, 6379, 8080, 8443]

    if len(context.args) > 1:
        try:
            ports = [int(p.strip()) for p in context.args[1].split(",")]
        except:
            await update.message.reply_text("❌ Invalid port format. Use: 80,443,22")
            return
    else:
        ports = common_ports

    await update.message.reply_text(
        f"🔍 Scanning `{host}` — {len(ports)} ports...\n_This may take a moment._",
        parse_mode="Markdown"
    )

    open_ports = []
    closed_ports = []

    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        await update.message.reply_text(f"❌ Could not resolve `{host}`", parse_mode="Markdown")
        return

    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                open_ports.append(port)
            else:
                closed_ports.append(port)
        except:
            closed_ports.append(port)

    service_map = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
        80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
        3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 6379: "Redis",
        8080: "HTTP-Alt", 8443: "HTTPS-Alt"
    }

    result_text = f"🖥️ *Port Scan: {host}* (`{ip}`)\n\n"
    if open_ports:
        result_text += "✅ *Open Ports:*\n"
        for p in open_ports:
            svc = service_map.get(p, "Unknown")
            result_text += f"  `{p}` — {svc}\n"
    else:
        result_text += "❌ No open ports found\n"

    result_text += f"\n🔒 Closed/Filtered: {len(closed_ports)} ports"

    await update.message.reply_text(result_text, parse_mode="Markdown")

# ─── NETWORK: PING ────────────────────────────────────────

async def ping_host(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/ping <host>`", parse_mode="Markdown")
        return

    host = context.args[0]
    await update.message.reply_text(f"📡 Pinging `{host}`...", parse_mode="Markdown")

    try:
        output = subprocess.check_output(
            ["ping", "-c", "4", host],
            stderr=subprocess.STDOUT,
            timeout=15,
            text=True
        )
        # Extract summary line
        lines = output.strip().split("\n")
        summary = "\n".join(lines[-3:])
        result = f"📡 *Ping: {host}*\n\n```\n{summary}\n```"
    except subprocess.CalledProcessError as e:
        result = f"❌ Host `{host}` is unreachable."
    except Exception as e:
        result = f"❌ Error: {str(e)}"

    await update.message.reply_text(result, parse_mode="Markdown")

# ─── NETWORK: HTTP HEADERS ────────────────────────────────

async def http_headers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/headers <url>`", parse_mode="Markdown")
        return

    url = context.args[0]
    if not url.startswith("http"):
        url = "https://" + url

    await update.message.reply_text(f"🔍 Fetching headers for `{url}`...", parse_mode="Markdown")

    try:
        r = requests.head(url, timeout=10, allow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0"})
        headers = dict(r.headers)

        security_headers = [
            "Strict-Transport-Security", "Content-Security-Policy",
            "X-Frame-Options", "X-Content-Type-Options",
            "Referrer-Policy", "Permissions-Policy", "Server"
        ]

        result = f"📋 *HTTP Headers: {url}*\n\n"
        result += f"Status: `{r.status_code}`\n\n"

        for h in security_headers:
            val = headers.get(h, "❌ Missing")
            icon = "✅" if h in headers else "⚠️"
            result += f"{icon} `{h}`:\n  `{val}`\n\n"

    except Exception as e:
        result = f"❌ Error: {str(e)}"

    await update.message.reply_text(result, parse_mode="Markdown")

# ─── NETWORK: ROBOTS.TXT ─────────────────────────────────

async def robots_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/robots <domain>`", parse_mode="Markdown")
        return

    domain = context.args[0]
    if not domain.startswith("http"):
        domain = "https://" + domain

    try:
        r = requests.get(f"{domain}/robots.txt", timeout=10)
        content = r.text[:2000]
        result = f"🤖 *robots.txt for {domain}*\n\n```\n{content}\n```"
    except Exception as e:
        result = f"❌ Error: {str(e)}"

    await update.message.reply_text(result, parse_mode="Markdown")

# ─── SECURITY: TIPS ───────────────────────────────────────

async def security_tips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random
    tips = [
        "🔐 Use a password manager. Never reuse passwords across sites.",
        "🛡️ Enable 2FA on every account, especially email and banking.",
        "📡 Avoid public WiFi for sensitive tasks. Use a VPN.",
        "🔄 Keep your OS and apps updated — patches fix known vulnerabilities.",
        "🎣 Phishing is the #1 attack vector. Always verify sender emails.",
        "🔑 Use hardware security keys (YubiKey) for critical accounts.",
        "💾 Backup your data: 3-2-1 rule (3 copies, 2 media types, 1 offsite).",
        "🧅 Tor Browser hides your identity online but is slow.",
        "🔍 Google yourself to see what info is publicly available about you.",
        "📱 App permissions matter — does a flashlight app need your contacts?",
        "🛜 Change your router's default credentials and disable WPS.",
        "🔒 Full disk encryption (BitLocker/FileVault) protects lost devices.",
        "⚠️ Social engineering bypasses all technical defenses — stay skeptical.",
        "🕵️ Use crt.sh and Shodan to see what's exposed about your domain.",
        "💡 Bug bounty programs pay you to find vulnerabilities legally.",
    ]
    tip = random.choice(tips)
    await update.message.reply_text(f"💡 *Security Tip*\n\n{tip}", parse_mode="Markdown")

# ─── SECURITY: TOOLS LIST ─────────────────────────────────

async def tools_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = (
        "🧰 *Essential Cybersecurity Tools*\n\n"
        "*Recon/OSINT*\n"
        "• `theHarvester` — email/domain recon\n"
        "• `Amass` — subdomain enumeration\n"
        "• `Shodan` — exposed devices search\n"
        "• `Maltego` — visual link analysis\n"
        "• `SpiderFoot` — automated OSINT\n\n"
        "*Scanning*\n"
        "• `Nmap` — port/service scanner\n"
        "• `Masscan` — fast port scanner\n"
        "• `Nikto` — web vulnerability scanner\n\n"
        "*Exploitation*\n"
        "• `Metasploit` — exploitation framework\n"
        "• `SQLmap` — SQL injection\n"
        "• `Burp Suite` — web app proxy/scanner\n\n"
        "*Password*\n"
        "• `Hashcat` — password cracking\n"
        "• `John the Ripper` — password cracking\n"
        "• `Hydra` — brute force tool\n\n"
        "*Wireless*\n"
        "• `Aircrack-ng` — WiFi security auditing\n"
        "• `Wireshark` — network packet analyzer\n\n"
        "*OS*\n"
        "• `Kali Linux` — pentesting distro\n"
        "• `Parrot OS` — security-focused OS\n"
    )
    await update.message.reply_text(result, parse_mode="Markdown")

# ─── SECURITY: CVE SEARCH ─────────────────────────────────

async def cve_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/cve <keyword>`\nExample: `/cve apache`", parse_mode="Markdown")
        return

    keyword = " ".join(context.args)
    await update.message.reply_text(f"🔍 Searching CVEs for `{keyword}`...", parse_mode="Markdown")

    try:
        r = requests.get(
            f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={keyword}&resultsPerPage=5",
            timeout=15
        )
        data = r.json()
        vulns = data.get("vulnerabilities", [])

        if not vulns:
            await update.message.reply_text(f"No CVEs found for `{keyword}`", parse_mode="Markdown")
            return

        result = f"🚨 *CVEs for: {keyword}*\n\n"
        for v in vulns:
            cve = v.get("cve", {})
            cve_id = cve.get("id", "N/A")
            desc = cve.get("descriptions", [{}])[0].get("value", "N/A")[:200]
            metrics = cve.get("metrics", {})
            score = "N/A"
            if "cvssMetricV31" in metrics:
                score = metrics["cvssMetricV31"][0]["cvssData"]["baseScore"]
            elif "cvssMetricV2" in metrics:
                score = metrics["cvssMetricV2"][0]["cvssData"]["baseScore"]

            result += f"*{cve_id}* (Score: `{score}`)\n{desc}...\n\n"

    except Exception as e:
        result = f"❌ Error: {str(e)}"

    await update.message.reply_text(result, parse_mode="Markdown")

# ─── SECURITY: HASH ───────────────────────────────────────

async def hash_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import hashlib
    if not context.args:
        await update.message.reply_text("Usage: `/hash <text>`", parse_mode="Markdown")
        return

    text = " ".join(context.args).encode()
    result = (
        f"#️⃣ *Hash Results*\n\n"
        f"`MD5`:    `{hashlib.md5(text).hexdigest()}`\n"
        f"`SHA1`:   `{hashlib.sha1(text).hexdigest()}`\n"
        f"`SHA256`: `{hashlib.sha256(text).hexdigest()}`\n"
        f"`SHA512`: `{hashlib.sha512(text).hexdigest()}`\n"
    )
    await update.message.reply_text(result, parse_mode="Markdown")

# ─── SECURITY: BASE64 ─────────────────────────────────────

async def encode_b64(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import base64
    if not context.args:
        await update.message.reply_text("Usage: `/encode <text>`", parse_mode="Markdown")
        return
    text = " ".join(context.args)
    encoded = base64.b64encode(text.encode()).decode()
    await update.message.reply_text(f"🔒 *Base64 Encoded:*\n`{encoded}`", parse_mode="Markdown")

async def decode_b64(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import base64
    if not context.args:
        await update.message.reply_text("Usage: `/decode <text>`", parse_mode="Markdown")
        return
    try:
        text = " ".join(context.args)
        decoded = base64.b64decode(text.encode()).decode()
        await update.message.reply_text(f"🔓 *Base64 Decoded:*\n`{decoded}`", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Invalid Base64 string.")

# ─── MENU CALLBACKS ───────────────────────────────────────

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_osint":
        text = (
            "🔍 *OSINT Commands*\n\n"
            "`/username <name>` — Username lookup\n"
            "`/email <email>` — Breach check\n"
            "`/whois <domain>` — WHOIS info\n"
            "`/dns <domain>` — DNS records\n"
            "`/ip <ip>` — IP geolocation\n"
            "`/subdomains <domain>` — Find subdomains\n"
            "`/dork <target>` — Google dorks\n"
        )
    elif data == "menu_network":
        text = (
            "🌐 *Network Commands*\n\n"
            "`/portscan <host>` — Port scanner\n"
            "`/ping <host>` — Ping host\n"
            "`/headers <url>` — HTTP headers\n"
            "`/robots <domain>` — robots.txt\n"
        )
    elif data == "menu_security":
        text = (
            "🛡️ *Security Commands*\n\n"
            "`/tips` — Random security tip\n"
            "`/tools` — Security tools list\n"
            "`/cve <keyword>` — CVE search\n"
            "`/hash <text>` — Hash a string\n"
            "`/encode <text>` — Base64 encode\n"
            "`/decode <text>` — Base64 decode\n"
        )
    elif data == "menu_help":
        await help_command(update, context)
        return
    else:
        return

    await query.edit_message_text(text, parse_mode="Markdown")

# ─── MAIN ─────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # OSINT
    app.add_handler(CommandHandler("username", username_lookup))
    app.add_handler(CommandHandler("email", email_check))
    app.add_handler(CommandHandler("whois", whois_lookup))
    app.add_handler(CommandHandler("dns", dns_lookup))
    app.add_handler(CommandHandler("ip", ip_info))
    app.add_handler(CommandHandler("subdomains", subdomains))
    app.add_handler(CommandHandler("dork", dork))

    # Network
    app.add_handler(CommandHandler("portscan", port_scan))
    app.add_handler(CommandHandler("ping", ping_host))
    app.add_handler(CommandHandler("headers", http_headers))
    app.add_handler(CommandHandler("robots", robots_txt))

    # Security
    app.add_handler(CommandHandler("tips", security_tips))
    app.add_handler(CommandHandler("tools", tools_list))
    app.add_handler(CommandHandler("cve", cve_search))
    app.add_handler(CommandHandler("hash", hash_text))
    app.add_handler(CommandHandler("encode", encode_b64))
    app.add_handler(CommandHandler("decode", decode_b64))

    # Menu buttons
    app.add_handler(CallbackQueryHandler(menu_callback))

    print("🤖 CyvxBot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
