import numpy as np
import cv2
import pytesseract
from gtts import gTTS
import os
from datetime import datetime
from symspellpy import SymSpell, Verbosity
import pkg_resources
import re

from paddleocr import PaddleOCR

# pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

ocr = PaddleOCR(use_angle_cls=True, lang='en')

sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
dictionary_path = pkg_resources.resource_filename(
    "symspellpy", "frequency_dictionary_en_82_765.txt") 
sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

def preprocess_image(img):
    img_copy = img.copy()
    
    gray = cv2.cvtColor(img_copy, cv2.COLOR_BGR2GRAY)
    
    # Áp dụng cân bằng histogram để cải thiện độ tương phản
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    
    # Áp dụng làm mờ Gaussian để loại bỏ nhiễu
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Áp dụng ngưỡng thích ứng để xử lý điều kiện ánh sáng khác nhau
    thresh1 = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    
    _, thresh2 = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Giảm nhiễu sau khi áp dụng ngưỡng
    kernel = np.ones((1, 1), np.uint8)
    opening1 = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel, iterations=1)
    opening2 = cv2.morphologyEx(thresh2, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # Thêm biên để cải thiện nhận diện chữ
    dilation1 = cv2.dilate(opening1, kernel, iterations=1)
    dilation2 = cv2.dilate(opening2, kernel, iterations=1)
    
    # Tăng cường cạnh để nhận diện văn bản tốt hơn
    edges = cv2.Canny(gray, 100, 200)
    
    # Trả về một mảng các hình ảnh đã xử lý để thử nhiều phương pháp
    processed_imgs = [gray, dilation1, dilation2, edges]
    
    return processed_imgs

def postprocess_text(text):
    # Loại bỏ các ký tự đặc biệt không mong muốn
    text = re.sub(r'[^\w\s.,?!-]', '', text)
    text = ' '.join(text.split())
    words = text.split()
    corrected_words = []
    for word in words:
        suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
        if suggestions:
            corrected_words.append(suggestions[0].term) # Lấy gợi ý tốt nhất
        else:
            corrected_words.append(word)
    corrected_text = ' '.join(corrected_words)
    return corrected_text


def perform_text_capture():
    os.makedirs('static/captured', exist_ok=True)
    os.makedirs('static/audio', exist_ok=True)
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        return "Error: Could not access the camera"
    
    while True:
        ret, frame = cap.read()
        if not ret:
            return "Error: Failed to capture image"

        h, w = frame.shape[:2]
        # Vẽ khung nhận diện
        cv2.rectangle(frame, (int(w*0.1), int(h*0.1)), 
                     (int(w*0.9), int(h*0.9)), (0, 255, 0), 2)
        
        cv2.putText(frame, '', (20, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow('Text Capture', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            # Lưu hình ảnh gốc
            original_img_path = f'static/captured/original_image.jpg'
            processed_img_path = f'static/captured/processed_image.jpg'
            
            cv2.imwrite(original_img_path, frame)
            
            # # Áp dụng với tiền lý hình ảnh
            # processed_imgs = preprocess_image(frame)
            
            # # Lưu một trong các phiên bản đã xử lý để hiển thị
            # cv2.imwrite(processed_img_path, processed_imgs[2]) 
            
            # cap.release()
            # cv2.destroyAllWindows()
            # print("Images captured and processed")
            
            # all_recognized_text = ""
            # for img in processed_imgs:
            #     try:
            #         img_np = np.array(img)
            #         results = ocr.ocr(img_np, cls=True)
            #         for line in results:
            #             for word_info in line:
            #                 if isinstance(word_info, (list, tuple)) and len(word_info) > 1:
            #                     text, confidence = word_info[1]
            #                     all_recognized_text += text + " "
            #     except Exception as e:
            #         print(f"Lỗi khi nhận diện với PaddleOCR: {e}")
            
            all_recognized_text = ""
            try:
                img_np = np.array(frame)
                results = ocr.ocr(img_np, cls=True)
                for line in results:
                    for word_info in line:
                        if isinstance(word_info, (list, tuple)) and len(word_info) > 1:
                            text, confidence = word_info[1]
                            all_recognized_text += text + " "
            except Exception as e:
                print(f"Lỗi khi nhận diện với PaddleOCR: {e}")
            

            if all_recognized_text.strip():
                text_output = postprocess_text(all_recognized_text.strip())
                print("Recognized text (PaddleOCR):")
                print(text_output)

                audio_path = f"static/audio/output_audio_paddle.mp3"
                tts = gTTS(text=text_output, lang='en')
                tts.save(audio_path)

                return text_output, processed_img_path, audio_path
            else:
                return "Không thể nhận diện văn bản bằng PaddleOCR.", processed_img_path
            
        elif key == 27:  # Phím ESC
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return "Đã hủy chụp hình"