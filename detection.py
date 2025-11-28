# detection.py
from ultralytics import YOLO
from config import *

class FireDetector:
    def __init__(self):
        print(f"⏳ Loading AI Model form: {MODEL_PATH}...")
        self.model = YOLO(MODEL_PATH)
        print("✅ Model Loaded!")
        
        # --- 1. การตั้งค่า Perspective Calibration (ระยะทาง 5m-30m) ---
        # ใช้สูตร Two-Point Calibration แก้สมการหาค่า k และ vp_y
        y1 = PIXEL_Y_BOTTOM
        d1 = DIST_BOTTOM
        y2 = PIXEL_Y_TOP
        d2 = DIST_TOP
        
        # แก้สมการหาค่าคงที่กล้อง (k)
        # สูตร: k = (y1 - y2) / (1/d1 - 1/d2)
        self.k = (y1 - y2) / ((1/d1) - (1/d2))
        
        # แทนค่า k กลับไปหาจุดขอบฟ้า (vp_y)
        self.vp_y = y1 - (self.k / d1)
        
        self.vp_x = int(FRAME_WIDTH / 2) # จุดกึ่งกลางภาพแนวนอน
        print(f"✅ Calibrated: VP_Y={self.vp_y:.1f}, K={self.k:.1f}")

        # --- 2. การตั้งค่า Servo (ทิศทาง) ---
        # รับค่ามุม Servo เริ่มต้นจาก Config
        # ตัวแปรนี้จะเก็บค่ามุมปัจจุบันของมอเตอร์ เพื่อใช้คำนวณทิศจริง
        self.current_servo_angle = INITIAL_SERVO_ANGLE

    def update_servo_angle(self, angle):
        """ 
        ฟังก์ชันสำหรับอัปเดตค่ามุม Servo 
        (เรียกใช้จาก main.py เมื่อมีการหมุนกล้อง/จำลองการหมุน) 
        """
        self.current_servo_angle = angle

    def get_y_from_distance(self, distance_m):
        """ แปลงระยะทาง (เมตร) -> ตำแหน่ง Pixel Y (Perspective Logic) """
        if distance_m <= 0: return FRAME_HEIGHT
        
        # สูตร: y = vp_y + (k / distance)
        pixel_offset = self.k / distance_m
        y_pos = int(self.vp_y + pixel_offset)
        
        return y_pos

    def get_distance_from_y(self, y_pixel):
        """ แปลงตำแหน่ง Pixel Y -> ระยะทาง (เมตร) (Perspective Logic) """
        # ป้องกันการหารด้วยศูนย์ (ถ้า y ตรงกับ vp_y พอดี)
        if abs(y_pixel - self.vp_y) < 0.1: return 999.0
        
        # สูตรกลับ: distance = k / (y - vp_y)
        distance = self.k / (y_pixel - self.vp_y)
        
        # ถ้าคำนวณแล้วระยะติดลบ (อยู่เหนือเส้นขอบฟ้า) ให้ปัดเป็นไกลมาก
        if distance < 0: return 999.0
        
        return round(distance, 1)

    def calculate_azimuth(self, x_center):
        """
        สูตร: ทิศจริง = มุม Servo + (ระยะห่างจากกลางภาพ * องศาต่อพิกเซล)
        """
        # 1. หาว่าวัตถุอยู่ห่างจากกลางภาพกี่พิกเซล (ซ้ายเป็นลบ, ขวาเป็นบวก)
        pixels_from_center = x_center - (FRAME_WIDTH / 2)
        
        # 2. แปลงพิกเซล เป็น องศา
        degrees_per_pixel = FOV_CAMERA / FRAME_WIDTH
        angle_offset = pixels_from_center * degrees_per_pixel
        
        # 3. รวมกับมุมที่ Servo หันอยู่ (ใช้ตัวแปร self.current_servo_angle)
        final_angle = self.current_servo_angle + angle_offset
        
        # 4. ปรับให้อยู่ในวงกลม 0-360 องศา
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

                # คำนวณจุดกึ่งกลางและฐานของวัตถุ
                center_x = (x1 + x2) / 2
                bottom_y = y2

                # เรียกใช้ฟังก์ชันคำนวณมุม (Azimuth) และระยะ (Perspective Distance)
                real_angle = self.calculate_azimuth(center_x)
                real_distance = self.get_distance_from_y(bottom_y)

                target_keywords = ['fire', 'smoke', 'flame']
                if any(word in class_name.lower() for word in target_keywords):
                    detections.append({
                        'bbox': (x1, y1, x2, y2),
                        'class': class_name,
                        'conf': conf,
                        'angle': real_angle,      # มุมจริง 360 องศา
                        'distance': real_distance # ระยะทางจาก Perspective mapping
                    })

        return detections