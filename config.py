# config.py

# --- 1. ตั้งค่ากล้อง ---
CAMERA_ID = 0           
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FOV_CAMERA = 60.0       # มุมมองกว้างของกล้อง (Field of View)

# --- 2. ตั้งค่า AI ---
MODEL_PATH = 'models/fire.pt'  

# ค่าความมั่นใจพื้นฐาน
CONFIDENCE_THRESHOLD = 0.3     

# เกณฑ์แยกประเภท (Double Standard)
FIRE_THRESHOLD = 0.50      # ไฟ: 50% ขึ้นไป
SMOKE_THRESHOLD = 0.75     # ควัน: 75% ขึ้นไป (กรองเข้มงวด)

# --- 3. ตั้งค่า Telegram ---
TELEGRAM_TOKEN = '8347036032:AAH1YCXsalj8mce2QU6ashdxTAK_ARyB3xc' 
TELEGRAM_CHAT_ID = '7372449059'

# --- 4. ตั้งค่า Calibration (ระยะทาง 5m-30m) ---
# จุดล่างสุด (Bottom Line) = 5 เมตร
PIXEL_Y_BOTTOM = FRAME_HEIGHT - 10 
DIST_BOTTOM = 5.0   

# จุดบนสุดของ Grid (Top Apex) = 30 เมตร
PIXEL_Y_TOP = 200    
DIST_TOP = 30.0      

# --- 5. ตั้งค่า Servo ---
INITIAL_SERVO_ANGLE = 0   # มุมเริ่มต้นของ Servo (0 องศา = หันตรงหน้า)

# --- 6. 🌍 ตั้งค่าพิกัด GPS ของกล้อง (เชียงใหม่) ---
# จากลิงก์ที่คุณให้มา: 18.792669, 98.983969
CAMERA_LAT = 18.79273619036605
CAMERA_LON = 98.98380734578086