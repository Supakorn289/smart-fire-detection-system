# config.py

# --- 1. ตั้งค่ากล้อง ---
CAMERA_ID = 0           
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FOV_CAMERA = 60.0       

# --- 2. ตั้งค่า AI ---
MODEL_PATH = 'models/fire.pt'  
CONFIDENCE_THRESHOLD = 0.4     

# --- 3. ตั้งค่า Telegram ---
TELEGRAM_TOKEN = 'ใส่_TOKEN_ของคุณที่นี่'
TELEGRAM_CHAT_ID = 'ใส่_CHAT_ID_ของคุณที่นี่'

# --- 4. ตั้งค่า Calibration (สำคัญมาก!) ---
# กำหนดตำแหน่ง Pixel ที่ต้องการให้เส้นปรากฏบนจอ

# จุดล่างสุด (Bottom Line) = 5 เมตร
# ให้ยึดติดขอบล่างจอเลย
PIXEL_Y_BOTTOM = FRAME_HEIGHT - 10 
DIST_BOTTOM = 5.0   

# จุดบนสุดของ Grid (Top Apex) = 30 เมตร
# กำหนดให้เส้น 30m อยู่ตรงกลางจอพอดี (หรือปรับเลขนี้ถ้าอยากให้สูง/ต่ำกว่านี้)
PIXEL_Y_TOP = 200    
DIST_TOP = 30.0      

# มุมเริ่มต้นของกล้อง
INITIAL_SERVO_ANGLE = 90