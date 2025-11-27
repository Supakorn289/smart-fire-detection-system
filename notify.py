# notify.py
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_notify(message, image_path=None):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ ยังไม่ได้ตั้งค่า Token/Chat ID ใน config.py")
        return

    print(f"📨 กำลังส่งแจ้งเตือนไปยัง Telegram...")

    # 1. ส่งข้อความ
    try:
        url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url_msg, data=data)
    except Exception as e:
        print(f"❌ ส่งข้อความไม่ผ่าน: {e}")

    # 2. ส่งรูปภาพ (ถ้ามี)
    if image_path:
        try:
            url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            with open(image_path, 'rb') as img_file:
                files = {'photo': img_file}
                data = {"chat_id": TELEGRAM_CHAT_ID}
                requests.post(url_photo, data=data, files=files)
            print("✅ ส่งภาพสำเร็จ!")
        except Exception as e:
            print(f"❌ ส่งภาพไม่ผ่าน: {e}")