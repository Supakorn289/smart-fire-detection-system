import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def test_send():
    print("--- 🔍 เริ่มทดสอบการเชื่อมต่อ Telegram ---")
    print(f"Token ที่ใช้: {TELEGRAM_TOKEN[:10]}... (แสดงแค่บางส่วน)")
    print(f"Chat ID ที่ใช้: {TELEGRAM_CHAT_ID}")

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": "✅ ทดสอบระบบ: ข้อความนี้ส่งจาก Python สำเร็จแล้ว!"}

    try:
        response = requests.post(url, data=data)
        print(f"📡 สถานะการส่ง (Status Code): {response.status_code}")
        print(f"📄 ผลตอบกลับจาก Telegram: {response.text}")

        if response.status_code == 200:
            print("🎉 สำเร็จ! บอทของคุณทำงานได้ปกติ")
        elif response.status_code == 401:
            print("❌ ผิดพลาด: Token ไม่ถูกต้อง (Unauthorized)")
        elif response.status_code == 400:
            print("❌ ผิดพลาด: Chat ID ไม่ถูกต้อง หรือหาไม่เจอ")
        elif response.status_code == 403:
            print("❌ ผิดพลาด: บอทไม่มีสิทธิ์ส่งข้อความ (คุณลืมกด Start บอทหรือเปล่า?)")
        else:
            print("❌ ผิดพลาดอื่น ๆ")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_send()