# app.py
from flask import Flask, render_template_string
import os

app = Flask(__name__)

# HTML Template ง่ายๆ (เขียนใส่ในนี้เลยจะได้ไม่ต้องสร้างไฟล์แยก)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Fire Detection Dashboard</title>
    <meta http-equiv="refresh" content="5"> <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #f0f0f0; }
        h1 { color: #d9534f; }
        .container { background: white; padding: 20px; margin: 20px auto; width: 80%; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        img { max-width: 100%; border: 5px solid #d9534f; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 Smart Fire Monitor Dashboard</h1>
        <p>ภาพเหตุการณ์ล่าสุด (อัปเดตอัตโนมัติ)</p>
        <img src="/static/latest_alert.jpg" onerror="this.style.display='none'" alt="ยังไม่มีการแจ้งเตือน">
        <p><i>ระบบกำลังทำงาน 24 ชั่วโมง...</i></p>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    # รัน Web Server ที่ Port 5000
    app.run(debug=True, port=5000)