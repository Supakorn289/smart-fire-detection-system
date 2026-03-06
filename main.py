# main.py
import cv2
import time
import os
import numpy as np
from config import *
from detection import FireDetector
from notify import send_telegram_notify

if not os.path.exists('static'):
    os.makedirs('static')

def draw_compass(frame, current_angle):
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

    sim_angle = 0.0      
    sim_speed = 0.1  

    print(f"🚀 System Started: Single-Axis Perspective ({MIN_DISTANCE}m - {MAX_DISTANCE}m)")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # 1. Simulation Logic
        sim_angle += sim_speed
        if sim_angle >= 360: sim_angle -= 360
        detector.update_servo_angle(sim_angle)

        detections = detector.detect(frame)

        # 2. Draw Compass
        draw_compass(frame, detector.current_servo_angle)

        # =================================================================
        # 🚗 3. Draw Clean Perspective Trapezoid (UI)
        # =================================================================
        color_ui = (0, 0, 0) # สีดำ
        line_thickness = 3
        
        vp_x = detector.vp_x
        vp_y = int(detector.H) # เส้นขอบฟ้าที่ถูกคำนวณจากสมการที่ 1
        
        # ระยะ Y เริ่มต้นและสิ้นสุด
        y_bottom = MIN_DIST_Y_PIXEL
        y_top = MAX_DIST_Y_PIXEL

        x_bottom_left = 0
        x_bottom_right = FRAME_WIDTH

        # คำนวณความกว้างของเส้นบน (Max Distance) แบบสมส่วน
        if (y_bottom - vp_y) != 0:
            scale = (y_top - vp_y) / (y_bottom - vp_y)
        else:
            scale = 0.1

        line_width_top = int(FRAME_WIDTH * scale)
        x_top_left = vp_x - (line_width_top // 2)
        x_top_right = vp_x + (line_width_top // 2)

        # วาดเส้นขอบ 4 ด้าน
        cv2.line(frame, (x_bottom_left, y_bottom), (x_top_left, y_top), color_ui, line_thickness)       # ซ้าย
        cv2.line(frame, (x_bottom_right, y_bottom), (x_top_right, y_top), color_ui, line_thickness)     # ขวา
        cv2.line(frame, (x_bottom_left, y_bottom), (x_bottom_right, y_bottom), (0, 0, 255), line_thickness) # ล่างสุด (แดง)
        cv2.line(frame, (x_top_left, y_top), (x_top_right, y_top), (255, 0, 255), line_thickness)           # บนสุด (ม่วง)

        # วาดข้อความระบุระยะ (ไม่ต้องวาดถี่ๆ ให้รก)
        text_max = f"{MAX_DISTANCE} m"
        text_min = f"{MIN_DISTANCE} m"
        
        (w_max, _), _ = cv2.getTextSize(text_max, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.putText(frame, text_max, (vp_x - (w_max // 2), y_top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_ui, 2)
        
        (w_min, _), _ = cv2.getTextSize(text_min, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.putText(frame, text_min, (vp_x - (w_min // 2), y_bottom - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_ui, 2)
        # =================================================================

        # 4. Alert Logic
        found_fire = False
        alert_msg = ""
        
        for d in detections:
            x1, y1, x2, y2 = d['bbox']
            display_dist = d['distance']
            
            if display_dist > 999:
                dist_str = "> Limit"
            else:
                dist_str = f"{display_dist}m"
            
            label = f"{d['class']} {dist_str}"
            angle_info = f"Az: {d['angle']} deg"
            lat, lon = d['gps']
            gps_info = f"GPS: {lat:.5f}, {lon:.5f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, label, (x1, y1 - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, angle_info, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(frame, gps_info, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            found_fire = True
            google_map_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            
            alert_msg = (f"🔥 แจ้งเหตุเพลิงไหม้!\n"
                         f"ประเภท: {d['class']}\n"
                         f"ระยะห่าง: {dist_str}\n"
                         f"ทิศทาง: {d['angle']} องศา\n"
                         f"📍 พิกัดจุดเกิดเหตุ: {google_map_link}")

        if found_fire and (time.time() - last_alert_time > alert_cooldown):
            img_path = "static/alert.jpg"
            cv2.imwrite(img_path, frame)
            print(f"🔔 Alert Sent!")
            send_telegram_notify(alert_msg, img_path)
            last_alert_time = time.time()

        cv2.putText(frame, "SIMULATION: GPS Tracking ON", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow("Smart Fire 360 - Clean UI", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()