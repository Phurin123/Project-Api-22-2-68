from flask import Flask, request, jsonify, send_from_directory
import uuid
import os
from PIL import Image
from werkzeug.utils import secure_filename
from ultralytics import YOLO
from flask_cors import CORS
from urllib.parse import quote
import cv2
import numpy as np
import threading

# การตั้งค่า Flask
app = Flask(__name__)
CORS(app)

# โฟลเดอร์อัปโหลด
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'jfif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# โหลดโมเดล YOLO
model_porn = YOLO(os.path.join(os.path.dirname(__file__), 'models', 'best-porn.pt'))
model_weapon = YOLO(os.path.join(os.path.dirname(__file__), 'models', 'best-weapon.pt'))

# ฟังก์ชันตรวจสอบประเภทไฟล์
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ฟังก์ชันตรวจสอบว่าเป็นไฟล์ภาพจริง
def is_image(file_path):
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except (IOError, SyntaxError):
        return False

# ฟังก์ชันแปลง .jfif เป็น .jpg
def convert_jfif_to_jpg(input_path):
    output_path = input_path.rsplit('.', 1)[0] + '.jpg'
    with Image.open(input_path) as img:
        img.convert('RGB').save(output_path, 'JPEG')
    os.remove(input_path)  # ลบไฟล์เดิม
    return output_path

# ฟังก์ชันวาด Bounding Box
def draw_bounding_boxes(image_path, detections, output_path):
    image = cv2.imread(image_path)
    for detection in detections:
        x, y, w, h = map(int, detection["bbox"])
        label = detection["label"]
        confidence = detection["confidence"]

        # วาด Bounding Box
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # สีเขียว

        # สร้างข้อความที่ต้องการแสดง
        text = f"{label} ({confidence:.2f})"
        
        # วัดขนาดข้อความ
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        
        # วาดพื้นหลังข้อความ
        background_rect = (x, y - text_size[1] - 10, x + text_size[0], y)
        cv2.rectangle(image, (background_rect[0], background_rect[1]), 
                      (background_rect[2], background_rect[3]), (0, 255, 0), -1)  # สีเขียวทึบ

        # วาดข้อความ
        cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    cv2.imwrite(output_path, image)

# ฟังก์ชันสำหรับลบไฟล์
def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
    except Exception as e:
        print(f"Error deleting file: {e}")

# API วิเคราะห์ภาพ
@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    ext = file.filename.rsplit('.', 1)[-1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    if ext == 'jfif':
        file_path = convert_jfif_to_jpg(file_path)
        filename = os.path.basename(file_path)

    if not is_image(file_path):
        os.remove(file_path)
        return jsonify({'error': 'File is not a valid image'}), 400

    try:
        # วิเคราะห์ภาพ
        results_porn = model_porn.predict(source=file_path)
        detections_porn = []
        has_inappropriate_content = False

        for result in results_porn:
            for box in result.boxes:
                label = model_porn.names[int(box.cls)]
                confidence = float(box.conf)
                bbox = box.xywh.tolist()[0]
                
                if label.lower() in ["porn", "nude"]:  # ตรวจสอบว่าเป็นเนื้อหาที่ไม่เหมาะสม
                    has_inappropriate_content = True

                detections_porn.append({
                    "label": label,
                    "confidence": confidence,
                    "bbox": bbox
                })

        detections_weapon = []
        has_weapon = False

        results_weapon = model_weapon.predict(source=file_path)
        for result in results_weapon:
            for box in result.boxes:
                label = model_weapon.names[int(box.cls)]
                confidence = float(box.conf)
                bbox = box.xywh.tolist()[0]

                if label.lower() in ["weapon", "gun", "knife"]:  # ตรวจสอบว่าเป็นอาวุธ
                    has_weapon = True

                detections_weapon.append({
                    "label": label,
                    "confidence": confidence,
                    "bbox": bbox
                })

        # วาด Bounding Box
        result_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_' + filename)
        draw_bounding_boxes(file_path, detections_porn + detections_weapon, result_image_path)

        # กำหนด status
        if has_inappropriate_content or has_weapon:
            status = "failed"
        else:
            status = "passed"

        # ลบไฟล์ที่อัปโหลด
        os.remove(file_path)
        # ตั้งค่าให้ลบไฟล์ processed image หลังจาก 1 วินาที
        threading.Timer(1, delete_file, args=[result_image_path]).start()

        return jsonify({
            'status': status,
            'detections_porn': detections_porn,
            'detections_weapon': detections_weapon,
            'processed_image_url': f'http://127.0.0.1:5000/uploads/{quote("processed_" + filename)}'
        })

    except Exception as e:
        return jsonify({'error': f'Error during analysis: {e}'}), 500
    
# API สำหรับขอ API Key
@app.route('/request-api-key', methods=['POST'])
def request_api_key():
    data = request.get_json()
    email = data.get('email')
    if email:
        api_key = str(uuid.uuid4())
        return jsonify({'apiKey': api_key})
    return jsonify({'error': 'Email is required'}), 400

# ให้บริการไฟล์ที่อัปโหลด
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)

if __name__ == '__main__':
    app.run(debug=True)