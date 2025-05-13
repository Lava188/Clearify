import cv2
import pytesseract
import numpy as np
import pyttsx3
import time
import threading

# Point pytesseract to where the tesseract executable is located
pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

def preprocess_image(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Cải thiện độ tương phản
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalize = clahe.apply(gray)
    
    # Làm mờ để giảm nhiễu
    blurred = cv2.GaussianBlur(equalize, (5, 5), 0)
    
    # Nhị phân hóa
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

class TextToSpeechEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  
        self.speaking = False
        self.text_queue = []
        self.last_text = ""
        self.last_speech_time = 0
        self.speech_gap = 1  # Khoảng cách tối thiểu giữa các lần đọc (giây)
        self.lock = threading.Lock()
        
        # Khởi tạo luồng đọc riêng biệt
        self.speech_thread = threading.Thread(target=self._process_speech_queue, daemon=True)
        self.speech_thread.start()
    
    def _process_speech_queue(self):
        while True:
            if self.text_queue and not self.speaking:
                with self.lock:
                    text = self.text_queue.pop(0)
                    self.speaking = True
                
                self.engine.say(text)
                self.engine.runAndWait()
                
                with self.lock:
                    self.speaking = False
            
            time.sleep(0.1)  
    
    def say(self, text):
        current_time = time.time()
        
        # Chỉ đọc nếu văn bản mới khác văn bản cũ và đã qua khoảng thời gian nghỉ
        if text != self.last_text and (current_time - self.last_speech_time) > self.speech_gap:
            with self.lock:
                # Xóa hàng đợi hiện tại và thêm văn bản mới
                self.text_queue = [text]
                self.last_text = text
                self.last_speech_time = current_time

def perform_live_text():
    # Khởi tạo bộ đọc văn bản
    speech_engine = TextToSpeechEngine()
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Không thể mở camera")
        return
    
    # Lấy chiều rộng và cao của khung hình
    ret, frame = cap.read()
    if not ret:
        print("Không thể đọc khung hình từ camera")
        return
    
    height, width = frame.shape[:2]
    
    # Tạo vùng nhận diện (giữa màn hình)
    roi_width = int(width * 0.6)  
    roi_height = int(height * 0.3)  
    
    roi_x = (width - roi_width) // 2  
    roi_y = (height - roi_height) // 2  
    

    last_ocr_time = 0
    ocr_interval = 0.5  # Thực hiện OCR mỗi 0.5 giây
    
    # Biến lưu trữ văn bản nhận diện được
    current_text = ""
    
    # Tạo luồng riêng cho OCR
    ocr_result = {"text": ""}
    ocr_lock = threading.Lock()
    
    def perform_ocr(roi_image):
        """Hàm thực hiện OCR trên một luồng riêng"""
        preprocessed = preprocess_image(roi_image)
        text = pytesseract.image_to_string(preprocessed, lang='eng').strip()
        
        # Chỉ cập nhật nếu tìm thấy văn bản
        if text:
            with ocr_lock:
                ocr_result["text"] = text
    
    print("Bắt đầu nhận diện văn bản. Nhấn 'c' để dừng.")
    
    while cap.isOpened():
        ret, frame = cap.read()
        
        if not ret:
            print("Không thể đọc khung hình")
            break
        
        # Trích xuất vùng quan tâm (ROI)
        roi = frame[roi_y:roi_y+roi_height, roi_x:roi_x+roi_width]
        
        # Vẽ khung xung quanh vùng nhận diện
        cv2.rectangle(frame, (roi_x, roi_y), (roi_x+roi_width, roi_y+roi_height), (0, 255, 0), 2)
        
        # Thực hiện OCR theo chu kỳ để tránh lag
        current_time = time.time()
        if current_time - last_ocr_time > ocr_interval:
            last_ocr_time = current_time
            
            # Thực hiện OCR trong một luồng riêng
            ocr_thread = threading.Thread(target=perform_ocr, args=(roi.copy(),))
            ocr_thread.daemon = True
            ocr_thread.start()
        
        # Lấy kết quả OCR từ luồng riêng
        with ocr_lock:
            current_text = ocr_result["text"]
        
        # Hiển thị văn bản nhận diện được
        cv2.rectangle(frame, (0, 0), (width, 30), (0, 0, 0), -1)
        cv2.putText(frame, current_text[:50], (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Đọc văn bản (sẽ được xử lý trong luồng riêng)
        if current_text:
            speech_engine.say(current_text)
        
        cv2.imshow('Nhan dien van ban - Nhan C de thoat', frame)
        if cv2.waitKey(1) & 0xFF == ord('c'):
            break
        
    cap.release()
    cv2.destroyAllWindows()
