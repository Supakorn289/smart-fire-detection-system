# main.py
import cv2
import time
import os
import numpy as np
from config import CAMERA_ID, FRAME_WIDTH, FRAME_HEIGHT, FOV_CAMERA
from detection import FireDetector
from notify import send_telegram_notify

if not os.path.exists('static'):
    os.makedirs('static')

# --- ฟังก์ชันวาดเข็มทิศ (Compass Bar) ---
def draw_compass(frame, current_angle):
    """ วาดแถบเข็มทิศด้านบนจอ """
    bar_height = 40
    bg_color = (50, 50, 50) # สีเทาเข้ม
    text_color = (255, 255, 255)
    
    # วาดพื้นหลังแถบ
    cv2.rectangle(frame, (0, 0), (FRAME_WIDTH, bar_height), bg_color, -1)
    
    # สามเหลี่ยมชี้ทิศปัจจุบัน (ตรงกลาง)
    center_x = FRAME_WIDTH // 2
    cv2.polylines(frame, [np.array([[center_x, bar_height], [center_x-10, bar_height-10], [center_x+10, bar_height-10]])], True, (0, 255, 255), 2)
    
    # วาดตัวอักษรทิศ (N, E, S, W)
    px_per_deg = FRAME_WIDTH / FOV_CAMERA 
    directions = [(0, "N"), (90, "E"), (180, "S"), (270, "W"), (360, "N")]
    
    for angle, label in directions:
        # หาความต่างระหว่างมุมทิศกับมุมกล้อง
        diff = angle - current_angle
        
        # แก้ไขเรื่องมุมวนรอบ (เช่น มุม 350 กับ 10 ห่างกันแค่ 20)
        if diff < -180: diff += 360
        if diff > 180: diff -= 360
            
        # ถ้าทิศนี้อยู่ในมุมมองกล้อง (FOV) ให้วาด
        if abs(diff) < (FOV_CAMERA / 2):
            x_pos = int(center_x + (diff * px_per_deg))
            cv2.putText(frame, label, (x_pos - 5, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
            cv2.line(frame, (x_pos, 30), (x_pos, bar_height), text_color, 1)

    # แสดงมุมเป็นตัวเลขมุมขวาบน
    cv2.putText(frame, f"{int(current_angle)} deg", (FRAME_WIDTH - 80, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)


def main():
    cap = cv2.VideoCapture(CAMERA_ID)
    cap.set(3, FRAME_WIDTH)
    cap.set(4, FRAME_HEIGHT)

    detector = FireDetector()
    last_alert_time = 0
    alert_cooldown = 15

    # --- ตัวแปรสำหรับจำลองการหมุน (Simulation Variables) ---
    sim_angle = 0.0      # มุมเริ่มต้น
    sim_speed = 0.5      # ความเร็วการหมุน (องศาต่อเฟรม) ปรับเลขนี้ให้หมุนเร็ว/ช้า

    print("🚀 System Started: Auto-Rotation Simulation ON.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # =================================================================
        # 🔄 ส่วนจำลองการหมุน (Simulation Logic)
        # =================================================================
        sim_angle += sim_speed
        
        # ถ้าหมุนครบ 360 องศา ให้วนกลับมา 0
        if sim_angle >= 360:
            sim_angle -= 360
            
        # ส่งค่ามุมจำลองเข้าสู่ระบบคำนวณ (สำคัญมาก!)
        detector.update_servo_angle(sim_angle)
        # =================================================================

        detections = detector.detect(frame)

        # =================================================================
        # 1. วาด Compass Bar (เข็มทิศ)
        # =================================================================
        draw_compass(frame, detector.current_servo_angle)

        # =================================================================
        # 2. วาด Perspective Grid (5m - 30m Triangle)
        # =================================================================
        
        # ข้อมูลระยะและสี
        grid_data = [
            (5.0,  (0, 0, 255)),      # 5m - แดง (ล่างสุด)
            (6.0,  (0, 128, 255)),    # 6m - ส้ม
            (7.5,  (0, 255, 255)),    # 7.5m - เหลือง
            (10.0, (200, 255, 200)),  # 10m - ครีม/เขียวอ่อน
            (15.0, (128, 128, 128)),  # 15m - เทา
            (30.0, (221, 160, 221))   # 30m - ม่วงอ่อน (บนสุด)
        ]

        # ดึงค่า VP และพิกัด Y เริ่มต้น/สิ้นสุด
        vp_x = detector.vp_x
        vp_y = int(detector.vp_y)
        y_start_5m = detector.get_y_from_distance(5.0)

        # วาดเส้นโครงสร้างหลัก สีดำ (Triangle Frame)
        # ลากจากมุมล่างจอ ไปยังจุดขอบฟ้า (VP)
        cv2.line(frame, (0, y_start_5m), (vp_x, vp_y), (0, 0, 0), 3)
        cv2.line(frame, (FRAME_WIDTH, y_start_5m), (vp_x, vp_y), (0, 0, 0), 3)

        # วาดเส้นแนวนอนตามระยะ
        for dist, color in grid_data:
            y_pos = detector.get_y_from_distance(dist)

            # เช็คว่าเส้นอยู่ในจอ
            if 0 <= y_pos <= FRAME_HEIGHT:
                # คำนวณความกว้างเส้นโดยใช้สามเหลี่ยมคล้าย
                h_current = y_pos - vp_y
                h_total = y_start_5m - vp_y
                
                if h_total == 0: continue
                
                scale = h_current / h_total
                line_width = int(FRAME_WIDTH * scale)
                
                x_start = vp_x - (line_width // 2)
                x_end = vp_x + (line_width // 2)

                # วาดเส้น
                cv2.line(frame, (x_start, y_pos), (x_end, y_pos), color, 3)

                # เขียนตัวเลข
                text = f"{dist} m"
                (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                text_x = vp_x - (w // 2)
                cv2.putText(frame, text, (text_x, y_pos - 8), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        # =================================================================
        # 3. วาดกรอบไฟ & ข้อมูล
        # =================================================================
        found_fire = False
        alert_msg = ""
        for d in detections:
            x1, y1, x2, y2 = d['bbox']
            
            # เตรียมข้อความแสดงผล
            display_dist = d['distance']
            if display_dist > 50: display_dist_str = ">50m"
            else: display_dist_str = f"{display_dist}m"
            
            label = f"{d['class']} {display_dist_str}"
            angle_info = f"Azimuth: {d['angle']} deg"

            # วาดกรอบและข้อความ
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, label, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, angle_info, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            found_fire = True
            alert_msg = f"🔥 พบเหตุ: {d['class']}\nระยะ: {display_dist_str}\nทิศทาง: {d['angle']} องศา"

        # 4. แจ้งเตือน Telegram
        if found_fire and (time.time() - last_alert_time > alert_cooldown):
            img_path = "static/alert.jpg"
            cv2.imwrite(img_path, frame)
            print(f"🔔 ส่งแจ้งเตือน: {alert_msg}")
            send_telegram_notify(alert_msg, img_path)
            last_alert_time = time.time()

        # เพิ่มข้อความบอกสถานะจำลอง
        cv2.putText(frame, "SIMULATION MODE: Rotating...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.imshow("Smart Fire 360 - Auto Rotation", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()