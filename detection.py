from ultralytics import YOLO
import cv2
import numpy as np  # ต้องใช้ numpy ช่วยคำนวณเส้นตรง
from config import MODEL_PATH, CONFIDENCE_THRESHOLD, FOV_CAMERA, FRAME_WIDTH, FRAME_HEIGHT

class FireDetector:
    def __init__(self):
        print(f"⏳ Loading AI Model form: {MODEL_PATH}...")
        self.model = YOLO(MODEL_PATH)
        print("✅ Model Loaded!")
        
        # --- 🎯 ส่วนตั้งค่า Calibration (ปรับจูนตรงนี้!) ---
        
        # 1. ตั้งค่าระยะทาง (แกน Y)
        # ตรรกะ: ต่ำ(Pixel เยอะ) = ใกล้ | สูง(Pixel น้อย) = ไกล
        # ให้คุณลองวัดจริงแล้วมาแก้เลขตรงนี้
        self.pixel_y_near = 250  # สมมติ: ขอบล่างสุดของจอ
        self.dist_near = 1.0     # สมมติ: ระยะ 1 เมตร
        
        self.pixel_y_far = 190   # สมมติ: กลางจอ
        self.dist_far = 14.0     # สมมติ: ระยะ 20 เมตร

        # 2. จำลองมุมกล้อง (Servo Angle)
        # ในเฟสหน้าเราจะรับค่านี้มาจาก Hardware จริง
        # ตอนนี้สมมติว่ากล้องหันไปทิศตะวันออก (90 องศา)
        self.current_servo_angle = 90 

    def calculate_distance(self, y_bottom):
        # ใช้สูตรเทียบปัญญัติไตรยางศ์ (Linear Interpolation)
        # แปลงค่า Pixel Y ให้เป็น เมตร
        distance = np.interp(
            y_bottom, 
            [self.pixel_y_far, self.pixel_y_near], # ช่วง Pixel (บน -> ล่าง)
            [self.dist_far, self.dist_near]        # ช่วงระยะจริง (ไกล -> ใกล้)
        )
        return round(distance, 1)

    def calculate_azimuth(self, x_center):
        # 1. คำนวณว่าวัตถุอยู่ห่างจากกลางภาพกี่องศา (Pixel Offset Angle)
        # กลางภาพคือ 0 องศา
        # ขวาสุดคือ +FOV/2
        # ซ้ายสุดคือ -FOV/2
        
        pixels_from_center = x_center - (FRAME_WIDTH / 2)
        degrees_per_pixel = FOV_CAMERA / FRAME_WIDTH
        offset_angle = pixels_from_center * degrees_per_pixel
        
        # 2. รวมกับมุมของกล้อง (Servo Logic)
        # ทิศจริง = มุมกล้อง + มุมในภาพ
        # (ถ้าอยู่ซ้าย offset จะติดลบเองตามสูตรด้านบน)
        final_angle = self.current_servo_angle + offset_angle
        
        # ปรับให้เป็น 0-360 เสมอ (เช่น ถ้าได้ 370 ให้ปัดเป็น 10)
        final_angle = final_angle % 360
        
        return round(final_angle, 1)

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

                # --- เริ่มคำนวณตาม Logic ของคุณ ---
                
                # 1. หาจุดอ้างอิง
                center_x = (x1 + x2) / 2  # จุดกลางแกน X (สำหรับหามุม)
                bottom_y = y2             # จุดล่างสุดแกน Y (สำหรับหาระยะ - เท้าติดพื้น)

                # 2. เข้าสูตรคำนวณ
                real_angle = self.calculate_azimuth(center_x)
                real_distance = self.calculate_distance(bottom_y)

                # 3. DEBUG: ปริ้นท์ดูค่าดิบๆ เพื่อใช้ Calibrate
                # (ให้ดูค่านี้ตอนคุณยืนเทสระยะ แล้วเอาไปแก้ใน __init__)
                print(f"🔍 DEBUG: Y_Bottom={bottom_y} -> Dist={real_distance}m | Angle={real_angle}")

                target_keywords = ['fire', 'smoke', 'flame', 'person'] # ใส่ person ไว้เทสก่อน
                
                if any(word in class_name.lower() for word in target_keywords):
                    detections.append({
                        'bbox': (x1, y1, x2, y2),
                        'class': class_name,
                        'conf': conf,
                        'angle': real_angle,    # มุมจริง (ทิศ)
                        'direction': "N/A",     # ไม่ใช้แล้ว เพราะเรารู้เป็นองศาจริงแล้ว
                        'distance': real_distance
                    })

        return detections