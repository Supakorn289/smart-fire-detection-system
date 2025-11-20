# notify.py
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_line_notify(message, image_path=None):
    # หมายเหตุ: ผมยังคงชื่อฟังก์ชันไว้ว่า send_line_notify เหมือนเดิม 
    # เพื่อที่คุณจะได้ไม่ต้องไปแก้ใน main.py (หลอกโปรแกรมว่าเป็นไลน์แต่ส่งเข้า Telegram)
    
    print(f"📨 กำลังส่งแจ้งเตือนไปยัง Telegram...")

    # 1. ส่งข้อความ (Text)
    try:
        url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url_msg, data=data)
    except Exception as e:
        print(f"❌ ส่งข้อความไม่ผ่าน: {e}")

    # 2. ส่งรูปภาพ (Image) - ถ้ามี
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