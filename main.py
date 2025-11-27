# main.py
import cv2
import time
import os
from config import CAMERA_ID, FRAME_WIDTH, FRAME_HEIGHT
from detection import FireDetector
from notify import send_telegram_notify

# สร้างโฟลเดอร์ static ไว้เก็บรูปชั่วคราว
if not os.path.exists('static'):
    os.makedirs('static')

def main():
    cap = cv2.VideoCapture(CAMERA_ID)
    cap.set(3, FRAME_WIDTH)
    cap.set(4, FRAME_HEIGHT)

    detector = FireDetector()

    # ตัวแปรกันส่งรัว
    last_alert_time = 0
    alert_cooldown = 15  # วินาที

    print("🚀 System Started. Press 'Q' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 1. ตรวจจับ
        detections = detector.detect(frame)

        # 2. 🎨 วาดเส้นบอกระยะ (Grid Lines) - ตามที่คุณขอ
        # (ระยะ, สี BGR, ข้อความ)
        grid_lines = [
            (20, (0, 255, 0), "20m"),    # เขียว
            (50, (0, 255, 255), "50m"),  # เหลือง/ฟ้า
            (100, (0, 0, 255), "100m")   # แดง
        ]

        for dist, color, text in grid_lines:
            y_pos = detector.get_y_from_distance(dist)
            # วาดเฉพาะถ้าเส้นอยู่ในจอ
            if 0 <= y_pos <= FRAME_HEIGHT:
                cv2.line(frame, (0, y_pos), (FRAME_WIDTH, y_pos), color, 2)
                cv2.putText(frame, text, (10, y_pos - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # 3. วาดกรอบและเตรียมแจ้งเตือน
        found_fire = False
        alert_msg = ""

        for d in detections:
            x1, y1, x2, y2 = d['bbox']
            label = f"{d['class']} {d['distance']}m"
            info = f"Angle: {d['angle']} deg"

            # วาดกรอบแดง
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, info, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            found_fire = True
            alert_msg = f"🔥 พบเหตุ: {d['class']}\nระยะ: {d['distance']} เมตร\nทิศทาง: {d['angle']} องศา"

        # 4. ส่ง Telegram Notification
        if found_fire and (time.time() - last_alert_time > alert_cooldown):
            img_path = "static/alert.jpg"
            cv2.imwrite(img_path, frame) # บันทึกภาพที่มีเส้น Grid และกรอบแดง
            
            send_telegram_notify(alert_msg, img_path)
            last_alert_time = time.time()

        cv2.imshow("Smart Fire Detection (Grid Overlay)", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()