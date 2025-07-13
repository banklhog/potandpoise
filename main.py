from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from linebot.exceptions import InvalidSignatureError
import random
from datetime import datetime, time, timedelta

app = Flask(__name__)

# 🌐 สำหรับเช็คว่า Webhook URL ทำงานหรือยัง
@app.route("/")
def index():
    print("🔔 UptimeRobot มาเคาะแล้ว")
    return "LINE Bot is running. ✅"

# 🔐 ใส่ Token กับ Secret จาก LINE Developer Console
line_bot_api = LineBotApi('lniPvxeERBazet5yEFbLbahKQYKHJM3nvFFTcTtTH/fuS+RhqtDspYfHesEdAlfmTOme1Y0KGXlWCE46TJXV/4aaMp5c99qKCFyGni34oNgt5tatgYFmCa4QFHPxi1fa4x7nfv0hLIgOdpRadRY7EwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('5f745a4dfb4a605869d525db965bc9de')

# 🎲 รายการสุ่มกระถาง (ข้อความ + รูป)
pots_with_images = [
    ("🌿 คุณได้กระถางทรงกลม สีน้ำตาลน่ารัก!", "https://i.postimg.cc/Y9q9GCp4/2024-12-16-7b231898a517f-1.webp"),
    ("🌵 กระถางลายหินธรรมชาติสุดเท่", "https://i.postimg.cc/Y9q9GCp4/2024-12-16-7b231898a517f-1.webp"),
    ("🌸 กระถางชมพูฟุ้งฟิ้ง หวานละมุน", "https://i.postimg.cc/1RbqTDmJ/Untitled.png"),
    # ... เพิ่มภาพตามรายการที่มี
]

# 🕒 เก็บเวลาที่ตอบข้อความอัตโนมัติ (เลิกงาน 30 นาที)
user_reply_time = {}
# 🕒 เก็บช่วงที่ตอบไปแล้ว (เช้า/บ่าย)
user_reply_log = {}

def is_out_of_office():
    now = datetime.now().time()
    return (
        time(12, 0) <= now <= time(13, 0) or
        now >= time(20, 0) or
        now <= time(8, 0)
    )

def get_day_key():
    return datetime.now().strftime("%Y-%m-%d")

def get_time_period():
    now = datetime.now().time()
    if time(8, 0) <= now < time(12, 0):
        return "morning"
    elif time(13, 0) <= now < time(20, 0):
        return "afternoon"
    return None

# 📬 Route รับ webhook จาก LINE
@app.route("/webhook", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print("✅ LINE ส่ง webhook มาแล้ว")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ Invalid signature")
        return "Invalid signature", 400
    return 'OK'

# 📨 เมื่อมีข้อความเข้ามา
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.lower()
    user_id = event.source.user_id
    now = datetime.now()
    print("📨 ได้รับข้อความจากผู้ใช้:", text)

    if "เสี่ยงดวง" in text:
        msg, image_url = random.choice(pots_with_images)
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text=msg),
                ImageSendMessage(
                    original_content_url=image_url,
                    preview_image_url=image_url
                )
            ]
        )
        return

    elif "วิธีสั่งซื้อ" in text:
        return  # ปล่อยให้ Auto-reply ตอบ

    elif is_out_of_office():
        last_reply_time = user_reply_time.get(user_id)
        if not last_reply_time or now - last_reply_time > timedelta(minutes=30):
            reply = (
                "ขอบคุณที่ทักมานะคะ 🌱\n"
                "ตอนนี้แอดมินอาจกำลังรดน้ำต้นไม้อยู่~ ☔️\n"
                "เดี๋ยวกลับมาตอบไว ๆ เลยน้าาา 💬"
            )
            user_reply_time[user_id] = now
        else:
            return

    else:
        day_key = get_day_key()
        period = get_time_period()

        if period:
            if user_id not in user_reply_log:
                user_reply_log[user_id] = {}
            if user_reply_log[user_id].get(day_key) != period:
                reply = (
                   
                            "ขอบคุณที่แวะมาหา Pot & Poise นะคะ 🌿\n\n"
                            "ตอนนี้ร้านปิดทำการแล้ว~ 🌙\n"
                            "แต่ไม่ต้องห่วงค่ะ แอดมินจะรีบมาตอบทันทีเมื่อเปิดร้านนะ 💬✨\n\n"
                            "เวลาทำการของเรา:  \n"
                            "จันทร์–เสาร์ | 08:00–20:00 น.  \n"
                            "หยุดทุกวันอาทิตย์ (แต่ต้นไม้ยังคิดถึงคุณเสมอ 🌱)\n\n"
                            "ขอบคุณที่อดใจรอค่ะ 💚"
                        )

                user_reply_log[user_id][day_key] = period
            else:
                return
        else:
            return

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
