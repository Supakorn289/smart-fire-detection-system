import requests
import time
# เอา Token ของคุณมาใส่ตรงนี้ (ห้ามลบเครื่องหมายคำพูด)
TOKEN = "ใส่_TOKEN_ของคุณ_ตรงนี้"

def get_chat_id():
    url = f"https://api.telegram.org/bot8347036032:AAH1YCXsalj8mce2QU6ashdxTAK_ARyB3xc/getUpdates"
    print("🔍 กำลังรอข้อความจากคุณ... (กรุณาทักแชทบอทของคุณเดี๋ยวนี้)")
    
    while True:
        try:
            response = requests.get(url)
            data = response.json()
            
            if "result" in data and len(data["result"]) > 0:
                # เจอข้อความแล้ว!
                latest_msg = data["result"][-1]
                chat_id = latest_msg["message"]["chat"]["id"]
                first_name = latest_msg["message"]["chat"]["first_name"]
                
                print("\n" + "="*30)
                print(f"🎉 เจอแล้ว! Chat ID ของคุณคือ: {chat_id}")
                print(f"👤 ชื่อผู้ใช้: {first_name}")
                print("="*30)
                print("👉 เอาเลขนี้ไปใส่ใน config.py ได้เลย")
                break
            else:
                # ยังไม่เจอ รอ 2 วินาทีแล้วเช็คใหม่
                print(".", end="", flush=True)
                time.sleep(2)
                
        except Exception as e:
            print(f"❌ Error: {e}")
            break

if __name__ == "__main__":
    get_chat_id()