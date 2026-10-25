import os, time, random, string, threading, html
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
TG = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHARS = string.ascii_lowercase + string.digits
DELAY = 6
LINE = "━━━━━━━━━━━━━━"

state = {"run": False, "mode": 0}
tried = set()
stats = {"n": 0, "found": 0, "last": "", "code": 0, "start": 0}

HELP = (
    "🎮 <b>بوت يوزرات Roblox</b>\n"
    + LINE + "\n"
    "🔹 /start3 ـ بحث الثلاثي (٣ خانات)\n"
    "🔹 /start4 ـ بحث الرباعي (٤ خانات)\n"
    "🔹 /status ـ حالة البحث\n"
    "🔹 /stop ـ إيقاف البحث\n"
    "🔹 /test اسم ـ فحص يوزر واحد\n"
    + LINE + "\n"
    "💡 البوت يرسل لك فقط اليوزرات المتاحة."
)


def send(chat, text):
    requests.post(TG + "/sendMessage",
                  json={"chat_id": chat, "text": text, "parse_mode": "HTML"})


def fmt_time(sec):
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h} ساعة و {m} دقيقة"
    if m:
        return f"{m} دقيقة و {s} ثانية"
    return f"{s} ثانية"


def check(name):
    params = {
        "Username": name,
        "Birthday": "1999-01-01",
        "Context": "Signup",
    }
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    r = requests.get("https://auth.roblox.com/v1/usernames/validate",
                     params=params, headers=headers, timeout=20)
    try:
        code = r.json().get("code")
    except Exception:
        code = None
    return r.status_code, code, r.text[:200]


def available(status, code):
    return status == 200 and code == 0


def make(n):
    while True:
        name = "".join(random.choice(CHARS) for _ in range(n))
        if not name.isdigit():
            return name


def search(chat, n):
    state["run"] = True
    state["mode"] = n
    stats["n"] = 0
    stats["found"] = 0
    stats["last"] = ""
    stats["code"] = 0
    stats["start"] = time.time()
    kind = "ثلاثي" if n == 3 else "رباعي"
    send(chat,
         "🚀 <b>بدأ البحث</b>\n" + LINE + "\n"
         f"🎯 النوع: <b>{kind}</b> ({n} خانات)\n"
         f"⏱ سرعة الفحص: يوزر كل {DELAY} ثواني\n"
         + LINE + "\n"
         "📩 بوصلك إشعار أول ما ألقى يوزر متاح.\n"
         "📊 /status للحالة  |  🛑 /stop للإيقاف")
    while state["run"]:
        name = make(n)
        if name in tried:
            continue
        try:
            status, code, text = check(name)
        except Exception as e:
            send(chat, "⚠️ <b>صار خطأ</b>\n" + html.escape(str(e))
                 + "\n🔄 بعيد المحاولة بعد دقيقة.")
            time.sleep(60)
            continue
        if status == 429:
            stats["code"] = 429
            send(chat, "⏳ <b>Roblox طلبت إبطاء الفحص</b>\n"
                       "بوقف دقيقتين وبكمل تلقائياً.")
            time.sleep(120)
            continue
        if status == 403:
            stats["code"] = 403
            send(chat, "🚫 <b>Roblox رفضت الطلب (403)</b>\n"
                 + html.escape(text[:200])
                 + "\n⏳ بوقف 5 دقايق وأعيد المحاولة.")
            time.sleep(300)
            continue
        tried.add(name)
        stats["n"] += 1
        stats["last"] = name
        stats["code"] = status
        if available(status, code):
            stats["found"] += 1
            elapsed = fmt_time(time.time() - stats["start"])
            send(chat,
                 "✅ <b>يوزر متاح!</b>\n" + LINE + "\n"
                 f"👤 <code>{html.escape(name)}</code>\n"
                 f"🔢 التجربة رقم: {stats['n']}\n"
                 f"⏱ بعد: {elapsed}\n"
                 + LINE + "\n"
                 "⚡ بادر بحجزه قبل لا ينسرق!")
        time.sleep(DELAY)
    send(chat,
         "🛑 <b>تم إيقاف البحث</b>\n" + LINE + "\n"
         f"🔎 اليوزرات اللي انفحصت: {stats['n']}\n"
         f"✅ المتاحة: {stats['found']}")


def status_text():
    if state["run"]:
        kind = "ثلاثي" if state["mode"] == 3 else "رباعي"
        elapsed = time.time() - stats["start"]
        rate = int(stats["n"] / elapsed * 3600) if elapsed > 0 else 0
        code = stats["code"]
        if code == 200:
            health = "سليم ✅"
        else:
            health = f"تنبيه ⚠️ ({code})"
        last = html.escape(stats["last"] or "-")
        return (
            "📊 <b>حالة البحث</b>\n" + LINE + "\n"
            f"🟢 الحالة: شغال ({kind})\n"
            f"⏱ مدة التشغيل: {fmt_time(elapsed)}\n"
            f"🔎 المفحوص: {stats['n']} يوزر\n"
            f"✅ المتاح: {stats['found']}\n"
            f"⚡ السرعة: حوالي {rate} يوزر بالساعة\n"
            f"👤 آخر يوزر: <code>{last}</code>\n"
            f"📡 اتصال Roblox: {health}"
        )
    return (
        "📊 <b>حالة البحث</b>\n" + LINE + "\n"
        "🔴 الحالة: متوقف\n"
        f"🔎 آخر جلسة: {stats['n']} يوزر | ✅ {stats['found']} متاح\n"
        + LINE + "\n"
        "▶️ ابدأ بـ /start3 أو /start4"
    )


def handle(m):
    chat = m["chat"]["id"]
    text = m.get("text", "")
    if text == "/id":
        return send(chat, f"🆔 رقمك: <code>{chat}</code>")
    if chat != OWNER_ID:
        return send(chat, "⛔ هذا البوت خاص بالمالك فقط.")
    if text in ("/start", "/help"):
        send(chat, HELP)
    elif text.startswith("/test"):
        parts = text.split()
        if len(parts) < 2:
            return send(chat, "ℹ️ الاستخدام: <code>/test اسم</code>")
        name = parts[1]
        try:
            s, c, t = check(name)
        except Exception as e:
            return send(chat, "⚠️ <b>خطأ</b>\n" + html.escape(str(e)))
        if available(s, c):
            result = "✅ متاح"
        elif s == 200 and c == 1:
            result = "❌ مأخوذ"
        elif s == 200:
            result = "🚫 غير صالح أو ممنوع\n" + html.escape(t)
        else:
            result = f"⚠️ رد غير متوقع ({s})\n" + html.escape(t)
        send(chat,
             "🧪 <b>نتيجة الفحص</b>\n" + LINE + "\n"
             f"👤 <code>{html.escape(name)}</code>\n"
             f"📌 {result}")
    elif text in ("/start3", "/start4"):
        if state["run"]:
            return send(chat, "⚠️ البحث شغال حالياً.\nاستخدم /stop لإيقافه أول.")
        n = 3 if text == "/start3" else 4
        threading.Thread(target=search, args=(chat, n), daemon=True).start()
    elif text == "/status":
        send(chat, status_text())
    elif text == "/stop":
        if state["run"]:
            state["run"] = False
        else:
            send(chat, "ℹ️ ما فيه بحث شغال الحين.")


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), H).serve_forever()


threading.Thread(target=run_server, daemon=True).start()

offset = 0
while True:
    try:
        r = requests.get(TG + "/getUpdates",
                         params={"offset": offset, "timeout": 30},
                         timeout=40).json()
        for u in r.get("result", []):
            offset = u["update_id"] + 1
            if "message" in u:
                handle(u["message"])
    except Exception:
        time.sleep(5)
