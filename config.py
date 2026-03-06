# config.py

# --- 1. ตั้งค่ากล้อง ---
CAMERA_ID = 0           
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FOV_CAMERA = 60.0       

# --- 2. ตั้งค่า AI ---
MODEL_PATH = 'models/fire.pt'  
CONFIDENCE_THRESHOLD = 0.3     
FIRE_THRESHOLD = 0.50      
SMOKE_THRESHOLD = 0.75     

# --- 3. ตั้งค่า Telegram ---
TELEGRAM_TOKEN = '8347036032:AAH1YCXsalj8mce2QU6ashdxTAK_ARyB3xc' 
TELEGRAM_CHAT_ID = '7372449059'

# --- 4. 📐 ตั้งค่าระยะทาง (Single-Axis Perspective Theory) ---
# ตัวแปร Z: ระยะทางจริง (หน่วย: เมตร)
MIN_DISTANCE = 1.0   # Z1: ระยะทางที่ใกล้ที่สุด 
MAX_DISTANCE = 10.0  # Z2: ระยะทางที่ไกลที่สุด

# ตัวแปร y: ตำแหน่งบนหน้าจอแกน Y (OpenCV: ขอบบนคือ 0, ขอบล่างคือ 480)
MIN_DIST_Y_PIXEL = FRAME_HEIGHT - 10     # y1: พิกเซลขอบเขตใกล้สุด (ชิดขอบล่าง)
MAX_DIST_Y_PIXEL = int(FRAME_HEIGHT / 2) # y2: พิกเซลขอบเขตไกลสุด (กลางภาพ)

# --- 5. ตั้งค่า Servo ---
INITIAL_SERVO_ANGLE = 0   

# --- 6. 🌍 ตั้งค่าพิกัด GPS ---
CAMERA_LAT = 18.79273619036605
CAMERA_LON = 98.98380734578086