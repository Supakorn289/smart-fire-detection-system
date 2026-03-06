# detection.py
from ultralytics import YOLO
from config import *
import math

class FireDetector:
    def __init__(self):
        print(f"⏳ Loading AI Model form: {MODEL_PATH}...")
        self.model = YOLO(MODEL_PATH)
        print("✅ Model Loaded!")
        
        # ================================================================
        # 📐 1. Single-Axis Perspective Projection (Pinhole Camera Model)
        # ================================================================
        # นำค่าจาก config มาตั้งเป็นตัวแปรตามทฤษฎีคณิตศาสตร์
        Z1 = MIN_DISTANCE
        Z2 = MAX_DISTANCE
        y1 = MIN_DIST_Y_PIXEL
        y2 = MAX_DIST_Y_PIXEL
        
        # สมการที่ 1: หาพิกัดเส้นขอบฟ้าจำลอง (H) - ท้องฟ้าตัดพื้นดิน
        self.H = ((Z2 * y2) - (Z1 * y1)) / (Z2 - Z1)
        
        # สมการที่ 2: หาค่าคงที่ของกล้อง (K) - สัดส่วนการบีบอัดของเลนส์
        self.K = Z1 * (y1 - self.H)
        
        # จุดศูนย์กลางแนวราบ
        self.vp_x = int(FRAME_WIDTH / 2)
        
        print(f"✅ Theory Calibrated: Horizon(H)={self.H:.1f}, Camera Constant(K)={self.K:.1f}")

        # --- 2. Servo & GPS Setting ---
        self.current_servo_angle = INITIAL_SERVO_ANGLE
        self.camera_lat = CAMERA_LAT
        self.camera_lon = CAMERA_LON

    def update_servo_angle(self, angle):
        self.current_servo_angle = angle

    def get_distance_from_y(self, y_pixel):
        """ 
        สมการที่ 3: หาระยะทางจุดเกิดเหตุ (Zt) จากพิกเซลฐาน (yt)
        """
        # ป้องกัน error หารด้วยศูนย์ และวัตถุที่อยู่เลยเส้นขอบฟ้าขึ้นไป (บนฟ้า)
        if y_pixel <= self.H: 
            return 999.0 
            
        # Zt = K / (yt - H)
        Zt = self.K / (y_pixel - self.H)
        return round(Zt, 1)

    def get_y_from_distance(self, distance_m):
        """ 
        สมการแปลงกลับ: หาพิกเซลหน้าจอ (yt) จากระยะทาง (Zt) เพื่อใช้วาด UI 
        """
        if distance_m <= 0: return FRAME_HEIGHT
        
        # จากสมการ Zt = K / (yt - H) ย้ายข้างเป็น yt = (K / Zt) + H
        yt = (self.K / distance_m) + self.H
        return int(yt)

    def calculate_azimuth(self, x_center):
        pixels_from_center = x_center - (FRAME_WIDTH / 2)
        degrees_per_pixel = FOV_CAMERA / FRAME_WIDTH
        offset_angle = pixels_from_center * degrees_per_pixel
        final_angle = self.current_servo_angle + offset_angle
        return round(final_angle % 360, 1)

    def calculate_gps_target(self, distance_meters, bearing_degrees):
        R = 6378137
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

                # กรองประเภทและความมั่นใจ
                if 'smoke' in class_lower:
                    if conf < SMOKE_THRESHOLD: continue 
                elif 'fire' in class_lower or 'flame' in class_lower:
                    if conf < FIRE_THRESHOLD: continue
                
                # กรองขนาดของวัตถุ
                object_area = (x2 - x1) * (y2 - y1)
                if (object_area / (FRAME_WIDTH * FRAME_HEIGHT)) < 0.015: continue

                # ⚠️ ทริคสำคัญ: ดึงค่า 'ขอบล่างสุดของ Bounding Box' (y2) มาเป็นตัวแปร yt
                center_x = (x1 + x2) / 2
                yt_bottom = y2

                real_angle = self.calculate_azimuth(center_x)
                real_distance = self.get_distance_from_y(yt_bottom)
                
                # ตัดวัตถุที่อยู่ใกล้กว่าระยะขั้นต่ำที่เราตั้งไว้ (Noise ฝุ่นใกล้กล้อง)
                if real_distance < MIN_DISTANCE:
                    continue

                fire_lat, fire_lon = self.calculate_gps_target(real_distance, real_angle)

                target_keywords = ['fire', 'smoke', 'flame']
                if any(word in class_lower for word in target_keywords):
                    detections.append({
                        'bbox': (x1, y1, x2, y2),
                        'class': class_name,
                        'conf': conf,
                        'angle': real_angle,
                        'distance': real_distance,
                        'gps': (fire_lat, fire_lon)
                    })
        return detections