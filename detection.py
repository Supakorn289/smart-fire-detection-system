# detection.py
from ultralytics import YOLO
from config import *
import math  # ⚠️ จำเป็นสำหรับการคำนวณ GPS

class FireDetector:
    def __init__(self):
        print(f"⏳ Loading AI Model form: {MODEL_PATH}...")
        self.model = YOLO(MODEL_PATH)
        print("✅ Model Loaded!")
        
        # --- 1. Perspective Calibration (Two-Point: 5m - 30m) ---
        y1 = PIXEL_Y_BOTTOM; d1 = DIST_BOTTOM
        y2 = PIXEL_Y_TOP; d2 = DIST_TOP
        
        self.k = (y1 - y2) / ((1/d1) - (1/d2))
        self.vp_y = y1 - (self.k / d1)
        self.vp_x = int(FRAME_WIDTH / 2)
        
        print(f"✅ Calibrated: VP_Y={self.vp_y:.1f}, K={self.k:.1f}")

        # --- 2. Servo Setting ---
        self.current_servo_angle = INITIAL_SERVO_ANGLE

        # --- 3. GPS Setting ---
        self.camera_lat = CAMERA_LAT
        self.camera_lon = CAMERA_LON

    def update_servo_angle(self, angle):
        """ อัปเดตมุม Servo """
        self.current_servo_angle = angle

    def get_y_from_distance(self, distance_m):
        """ แปลงระยะทาง (m) -> Pixel Y """
        if distance_m <= 0: return FRAME_HEIGHT
        return int(self.vp_y + (self.k / distance_m))

    def get_distance_from_y(self, y_pixel):
        """ แปลง Pixel Y -> ระยะทาง (m) """
        if abs(y_pixel - self.vp_y) < 0.1: return 999.0
        distance = self.k / (y_pixel - self.vp_y)
        if distance < 0: return 999.0
        return round(distance, 1)

    def calculate_azimuth(self, x_center):
        """ คำนวณทิศทางจริง (Azimuth) """
        pixels_from_center = x_center - (FRAME_WIDTH / 2)
        degrees_per_pixel = FOV_CAMERA / FRAME_WIDTH
        offset_angle = pixels_from_center * degrees_per_pixel
        
        final_angle = self.current_servo_angle + offset_angle
        return round(final_angle % 360, 1)

    def calculate_gps_target(self, distance_meters, bearing_degrees):
        """ 🌍 คำนวณพิกัดปลายทาง (จุดไฟไหม้) """
        R = 6378137 # รัศมีโลก (เมตร)
        
        lat1 = math.radians(self.camera_lat)
        lon1 = math.radians(self.camera_lon)
        bearing = math.radians(bearing_degrees)

        lat2 = math.asin(math.sin(lat1) * math.cos(distance_meters / R) +
                         math.cos(lat1) * math.sin(distance_meters / R) * math.cos(bearing))

        lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(distance_meters / R) * math.cos(lat1),
                                 math.cos(distance_meters / R) - math.sin(lat1) * math.sin(lat2))

        return math.degrees(lat2), math.degrees(lon2)

    def detect(self, frame):
        results = self.model(frame, verbose=False, conf=CONFIDENCE_THRESHOLD)
        detections = []

        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                class_name = self.model.names[cls_id]
                class_lower = class_name.lower()

                # =========================================================
                # 🔥 LOGIC กรองแยกประเภท (Smart Filtering)
                # =========================================================
                if 'smoke' in class_lower:
                    if conf < SMOKE_THRESHOLD: continue 
                elif 'fire' in class_lower or 'flame' in class_lower:
                    if conf < FIRE_THRESHOLD: continue
                
                # กรองขนาด (Size Filter)
                object_area = (x2 - x1) * (y2 - y1)
                if (object_area / (FRAME_WIDTH * FRAME_HEIGHT)) < 0.015: continue
                # =========================================================

                # คำนวณค่าทางฟิสิกส์
                center_x = (x1 + x2) / 2
                bottom_y = y2

                real_angle = self.calculate_azimuth(center_x)
                real_distance = self.get_distance_from_y(bottom_y)

                # 🌍 คำนวณ GPS เป้าหมาย
                fire_lat, fire_lon = self.calculate_gps_target(real_distance, real_angle)

                target_keywords = ['fire', 'smoke', 'flame']
                if any(word in class_lower for word in target_keywords):
                    detections.append({
                        'bbox': (x1, y1, x2, y2),
                        'class': class_name,
                        'conf': conf,
                        'angle': real_angle,
                        'distance': real_distance,
                        'gps': (fire_lat, fire_lon) # ส่งพิกัดออกไป
                    })

        return detections