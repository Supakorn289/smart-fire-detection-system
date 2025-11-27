# detection.py
from ultralytics import YOLO
import numpy as np
from config import *

class FireDetector:
    def __init__(self):
        print(f"⏳ Loading AI Model form: {MODEL_PATH}...")
        self.model = YOLO(MODEL_PATH)
        print("✅ Model Loaded!")
        
        # รับค่า Calibration มาจาก config
        self.pixel_y_near = PIXEL_Y_NEAR
        self.dist_near = DIST_NEAR
        self.pixel_y_far = PIXEL_Y_FAR
        self.dist_far = DIST_FAR
        
        # มุมกล้องปัจจุบัน (อนาคตรับค่าจาก Hardware)
        self.current_servo_angle = INITIAL_SERVO_ANGLE

    def calculate_distance(self, y_bottom):
        """แปลง Pixel Y -> ระยะทาง (เมตร)"""
        if y_bottom > FRAME_HEIGHT: y_bottom = FRAME_HEIGHT
        
        distance = np.interp(
            y_bottom,
            [self.pixel_y_far, self.pixel_y_near], # ช่วง Input (บน -> ล่าง)
            [self.dist_far, self.dist_near]        # ช่วง Output (ไกล -> ใกล้)
        )
        return round(distance, 1)

    def get_y_from_distance(self, target_distance):
        """แปลง ระยะทาง (เมตร) -> Pixel Y (เพื่อวาดเส้น Grid)"""
        y_pixel = np.interp(
            target_distance,
            [self.dist_near, self.dist_far],       # ช่วง Input (ใกล้ -> ไกล)
            [self.pixel_y_near, self.pixel_y_far]  # ช่วง Output (ล่าง -> บน)
        )
        return int(y_pixel)

    def calculate_azimuth(self, x_center):
        """คำนวณมุมทิศ 360 องศา"""
        # 1. หามุม Offset ในภาพ (-30 ถึง +30 องศา)
        pixels_from_center = x_center - (FRAME_WIDTH / 2)
        degrees_per_pixel = FOV_CAMERA / FRAME_WIDTH
        offset_angle = pixels_from_center * degrees_per_pixel
        
        # 2. รวมกับมุมจริงของกล้อง
        final_angle = self.current_servo_angle + offset_angle
        
        # ปรับให้เป็น 0-360 เสมอ
        return round(final_angle % 360, 1)

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

                # --- Logic C Calculations ---
                center_x = (x1 + x2) / 2
                bottom_y = y2

                real_angle = self.calculate_azimuth(center_x)
                real_distance = self.calculate_distance(bottom_y)

                # Filter เฉพาะ Fire/Smoke
                target_keywords = ['fire', 'smoke', 'flame']
                if any(word in class_name.lower() for word in target_keywords):
                    detections.append({
                        'bbox': (x1, y1, x2, y2),
                        'class': class_name,
                        'conf': conf,
                        'angle': real_angle,
                        'distance': real_distance
                    })

        return detections