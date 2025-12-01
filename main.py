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
    bg_color = (50, 50, 50)
    text_color = (255, 255, 255)
    
    cv2.rectangle(frame, (0, 0), (FRAME_WIDTH, bar_height), bg_color, -1)
    
    center_x = FRAME_WIDTH // 2
    cv2.polylines(frame, [np.array([[center_x, bar_height], [center_x-10, bar_height-10], [center_x+10, bar_height-10]])], True, (0, 255, 255), 2)
    
    px_per_deg = FRAME_WIDTH / FOV_CAMERA 
    directions = [(0, "N"), (90, "E"), (180, "S"), (270, "W"), (360, "N")]
    
    for angle, label in directions:
        diff = angle - current_angle
        if diff < -180: diff += 360
        if diff > 180: diff -= 360
        if abs(diff) < (FOV_CAMERA / 2):
            x_pos = int(center_x + (diff * px_per_deg))
            cv2.putText(frame, label, (x_pos - 5, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
            cv2.line(frame, (x_pos, 30), (x_pos, bar_height), text_color, 1)

    cv2.putText(frame, f"{int(current_angle)} deg", (FRAME_WIDTH - 80, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

def main():
    cap = cv2.VideoCapture(CAMERA_ID)
    cap.set(3, FRAME_WIDTH)
    cap.set(4, FRAME_HEIGHT)

    detector = FireDetector()
    last_alert_time = 0
    alert_cooldown = 15

    # --- Simulation Variables ---
    sim_angle = 0.0      
    sim_speed = 0.1  # ความเร็วการหมุน (ปรับได้)

    print("🚀 System Started: GPS Targeting Enabled.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # =================================================================
        # 🔄 ส่วนจำลองการหมุน (Simulation Logic)
        # =================================================================
        sim_angle += sim_speed
        if sim_angle >= 360:
            sim_angle -= 360
            
        detector.update_servo_angle(sim_angle)
        # =================================================================

        detections = detector.detect(frame)

        # 1. วาด Compass Bar
        draw_compass(frame, detector.current_servo_angle)

        # 2. วาด Perspective Grid (5m - 30m)
        grid_data = [
            (5.0,  (0, 0, 255)), (6.0,  (0, 128, 255)), (7.5,  (0, 255, 255)), 
            (10.0, (200, 255, 200)), (15.0, (128, 128, 128)), (30.0, (221, 160, 221))
        ]

        vp_x = detector.vp_x
        vp_y = int(detector.vp_y)
        y_start_5m = detector.get_y_from_distance(5.0)

        # วาดเส้นโครงสามเหลี่ยม
        cv2.line(frame, (0, y_start_5m), (vp_x, vp_y), (0, 0, 0), 3)
        cv2.line(frame, (FRAME_WIDTH, y_start_5m), (vp_x, vp_y), (0, 0, 0), 3)

        # วาดเส้นแนวนอน
        for dist, color in grid_data:
            y_pos = detector.get_y_from_distance(dist)
            if 0 <= y_pos <= FRAME_HEIGHT:
                h_current = y_pos - vp_y
                h_total = y_start_5m - vp_y
                if h_total == 0: continue
                scale = h_current / h_total
                line_width = int(FRAME_WIDTH * scale)
                x_start = vp_x - (line_width // 2)
                x_end = vp_x + (line_width // 2)
                cv2.line(frame, (x_start, y_pos), (x_end, y_pos), color, 3)
                text = f"{dist} m"
                (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                text_x = vp_x - (w // 2)
                cv2.putText(frame, text, (text_x, y_pos - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        # 3. Alert Logic with GPS
        found_fire = False
        alert_msg = ""
        
        for d in detections:
            x1, y1, x2, y2 = d['bbox']
            
            # กรองขนาด (Double check)
            if ((x2 - x1) * (y2 - y1)) / (FRAME_WIDTH * FRAME_HEIGHT) < 0.015: continue 

            display_dist = d['distance']
            dist_str = f"{display_dist}m" if display_dist < 50 else ">50m"
            
            label = f"{d['class']} {dist_str}"
            angle_info = f"Az: {d['angle']} deg"
            
            # 🌍 ดึงค่า GPS มาแสดง
            lat, lon = d['gps']
            gps_info = f"GPS: {lat:.5f}, {lon:.5f}"

            # วาดกรอบและข้อมูล
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, label, (x1, y1 - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, angle_info, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(frame, gps_info, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            found_fire = True
            
            # 🌍 สร้างลิงก์ Google Maps สำหรับแจ้งเตือน
            google_map_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            
            alert_msg = (f"🔥 แจ้งเหตุเพลิงไหม้!\n"
                         f"ประเภท: {d['class']}\n"
                         f"ระยะห่าง: {dist_str}\n"
                         f"ทิศทาง: {d['angle']} องศา\n"
                         f"📍 พิกัดจุดเกิดเหตุ: {google_map_link}")

        # 4. ส่งแจ้งเตือน Telegram
        if found_fire and (time.time() - last_alert_time > alert_cooldown):
            img_path = "static/alert.jpg"
            cv2.imwrite(img_path, frame)
            print(f"🔔 GPS Alert Sent: {alert_msg}")
            send_telegram_notify(alert_msg, img_path)
            last_alert_time = time.time()

        cv2.putText(frame, "SIMULATION: GPS Tracking ON", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow("Smart Fire 360 - GPS Targeting", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()