from ultralytics import YOLO
import cv2
from config import MODEL_PATH, CONFIDENCE_THRESHOLD, FOV_CAMERA, FRAME_WIDTH, KNOWN_DIST_COEFF

class FireDetector:
    def __init__(self):
        # ส่วนที่ 1: เริ่มต้นระบบ
        print(f"⏳ Loading AI Model form: {MODEL_PATH}...")
        # โหลดไฟล์สมอง AI (.pt) เข้ามาในหน่วยความจำ
        self.model = YOLO(MODEL_PATH)
        print("✅ Model Loaded! Ready to detect fire.")

    def detect(self, frame):
        # ส่วนที่ 2: สั่งให้ AI มองภาพ
        # stream=True ช่วยให้ทำงานเร็วขึ้นกับวิดีโอ
        results = self.model(frame, verbose=False, conf=CONFIDENCE_THRESHOLD)
        
        detections = [] # เตรียมตระกร้าไว้ใส่สิ่งของที่เจอ

        # วนลูปดูผลลัพธ์ (เผื่อเจอไฟหลายจุดพร้อมกัน)
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # ส่วนที่ 3: แกะข้อมูลพิกัด (Coordinate)
                # x1, y1 = มุมซ้ายบน | x2, y2 = มุมขวาล่าง
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # ดึงค่าความมั่นใจ (0.0 - 1.0) และชื่อคลาส
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                class_name = self.model.names[cls_id]

                # --- DEBUG: ดูว่า AI เห็นเป็นชื่ออะไร ---
                # (ช่วยแก้ปัญหาเวลาโหลดโมเดลมาแล้วไม่รู้ว่ามันตั้งชื่อว่า fire หรือ Fire)
                # print(f"DEBUG: AI sees -> {class_name} ({conf:.2f})")

                # ส่วนที่ 4: คำนวณคณิตศาสตร์ (Logic)
                
                # 4.1 หาจุดกึ่งกลาง (Center X) เพื่อดูทิศทาง
                center_x = (x1 + x2) / 2
                
                # 4.2 คำนวณมุม (Angle)
                # แปลงจาก Pixel เป็น องศา โดยเทียบกับจุดกลางภาพ
                # ถ้า pixel_offset เป็นลบ = อยู่ซ้าย, เป็นบวก = อยู่ขวา
                pixel_offset = center_x - (FRAME_WIDTH / 2)
                angle = (pixel_offset / FRAME_WIDTH) * FOV_CAMERA
                direction = "ขวา" if angle > 0 else "ซ้าย"

                # 4.3 คำนวณระยะทาง (Distance Estimation)
                # หลักการ: "ยิ่งใกล้ ภาพยิ่งใหญ่ ยิ่งไกล ภาพยิ่งเล็ก"
                # เราใช้ความสูงของกล่อง (box_height) มาหารค่าคงที่
                box_height = y2 - y1
                if box_height > 0:
                    distance = KNOWN_DIST_COEFF / box_height
                else:
                    distance = 0

                # ส่วนที่ 5: การกรอง (Filtering)
                # เราจะสนใจเฉพาะสิ่งที่มีชื่อเกี่ยวกับ ไฟ หรือ ควัน
                target_keywords = ['fire', 'smoke', 'flame']
                
                # แปลงชื่อที่เจอเป็นตัวพิมพ์เล็ก แล้วเช็คว่าตรงกับ keyword ไหม
                if any(word in class_name.lower() for word in target_keywords):
                    detections.append({
                        'bbox': (x1, y1, x2, y2),
                        'class': class_name,
                        'conf': conf,
                        'angle': angle,
                        'direction': direction,
                        'distance': distance
                    })

        return detections