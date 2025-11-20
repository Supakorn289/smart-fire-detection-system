# main.py
import cv2
import time
import os
from config import CAMERA_ID, FRAME_WIDTH, FRAME_HEIGHT
from detection import FireDetector
from notify import send_line_notify

# สร้างโฟลเดอร์ static หากยังไม่มี
if not os.path.exists('static'):
    os.makedirs('static')

def main():
    # 1. เปิดกล้อง
    cap = cv2.VideoCapture(CAMERA_ID)
    cap.set(3, FRAME_WIDTH)
    cap.set(4, FRAME_HEIGHT)

    # 2. เรียกใช้ AI Class
    detector = FireDetector()

    # ตัวแปรสำหรับหน่วงเวลาส่งไลน์ (ไม่ให้ส่งรัวๆ)
    last_alert_time = 0
    alert_cooldown = 15  # วินาที (ส่งไลน์ได้ทุกๆ 15 วิ)

    print("🚀 System Started. Press 'Q' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 3. ส่งภาพเข้า AI
        detections = detector.detect(frame)

        # 4. วาดกรอบและแสดงผล
        found_fire = False
        alert_message = ""

        for d in detections:
            x1, y1, x2, y2 = d['bbox']
            label = f"{d['class']} {d['conf']:.2f}"
            info = f"Dist: {d['distance']:.1f}m | Ang: {d['angle']:.1f} deg"

            # วาดกรอบสี่เหลี่ยม
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            # เขียนข้อความ
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, info, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

            found_fire = True
            alert_message = f"🔥 พบ {d['class']}!\nระยะ: {d['distance']:.1f} เมตร\nทิศทาง: {d['direction']} {abs(d['angle']):.1f} องศา"

        # 5. แจ้งเตือน LINE (ถ้าเจอ + หมดเวลาคูลดาวน์)
        if found_fire and (time.time() - last_alert_time > alert_cooldown):
            # บันทึกภาพเพื่อส่ง
            img_path = "static/latest_alert.jpg"
            cv2.imwrite(img_path, frame)
            
            print("📨 Sending Notification...")
            send_line_notify(alert_message, img_path)
            
            last_alert_time = time.time()

        # แสดงภาพสดบนหน้าจอ
        cv2.imshow("Smart Fire Detection - Desktop Prototype", frame)

        # กด Q เพื่อออก
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()