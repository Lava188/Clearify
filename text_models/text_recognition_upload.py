import cv2
import os
from datetime import datetime
from flask import Flask, render_template, request, Response
from gtts import gTTS
from paddleocr import PaddleOCR

# Khởi tạo Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/captured'
app.config['AUDIO_FOLDER'] = 'static/audio'

# Tạo thư mục nếu chưa tồn tại
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)

# Khởi tạo PaddleOCR (sử dụng tiếng Anh và tự động sửa xoay)
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# Hàm điều chỉnh sáng/tương phản
def adjust_brightness_contrast(image, alpha=1.0, beta=0):
    return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)


def perform_ocr_and_audio(image_path):
    # Load ảnh và chuyển sang RGB
    img_bgr = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Tiền xử lý: tăng sáng/tương phản nhẹ
    img_processed = adjust_brightness_contrast(img_rgb, alpha=1.2, beta=20)

    # Lưu ảnh đã xử lý
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    adjusted_image_path = os.path.join(app.config['UPLOAD_FOLDER'], f'adjusted_image_{timestamp}.jpg')
    cv2.imwrite(adjusted_image_path, cv2.cvtColor(img_processed, cv2.COLOR_RGB2BGR))

    # OCR với PaddleOCR
    # Đầu vào là mảng numpy RGB
    results = ocr.ocr(img_processed, cls=True)

    # Gom kết quả text
    recognized_text = []
    for line in results:
        for word_info in line:
            text = word_info[1][0]
            recognized_text.append(text)
    text_output = " ".join(recognized_text).strip()
    if not text_output:
        text_output = "Error: No text detected."

    # Chuyển text thành giọng nói (MP3)
    audio_file = os.path.join(app.config['AUDIO_FOLDER'], f'output_{timestamp}.mp3')
    tts = gTTS(text=text_output, lang='en')
    tts.save(audio_file)

    return text_output, audio_file, adjusted_image_path, timestamp
