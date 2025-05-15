import cv2
import numpy as np
import time
import threading
import queue
from paddleocr import PaddleOCR
from symspellpy import SymSpell, Verbosity
import pkg_resources
import re
import pyttsx3

# Khởi tạo PaddleOCR (chạy một lần khi khởi động)
ocr = PaddleOCR(use_angle_cls=True, lang='en')

sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
dictionary_path = pkg_resources.resource_filename(
    "symspellpy", "frequency_dictionary_en_82_765.txt")
sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

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

class OCRProcessor:
    def __init__(self):
        self.ocr_queue = []
        self.result_text = ""
        self.processing = False
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
    
    def add_frame(self, frame):
        if not self.processing:
            self.ocr_queue.append(frame)
    
    def _process_queue(self):
        while True:
            if len(self.ocr_queue) != 0:
                self.processing = True
                frame = self.ocr_queue.pop()
                try:
                    results = ocr.ocr(frame, cls=True)
                    current_frame_text = ""
                    for line in results:
                        for word_info in line:
                            if isinstance(word_info, (list, tuple)) and len(word_info) > 1:
                                text, confidence = word_info[1]
                                current_frame_text += text + " "
                    
                    if current_frame_text.strip():
                        self.result_text = postprocess_text(current_frame_text.strip())
                        print(f"Nhận diện: {self.result_text}")
                except Exception as e:
                    print(f"Lỗi PaddleOCR: {e}")
                self.processing = False
            time.sleep(0.01)
    
    def get_text(self):
        return self.result_text

class TextToSpeechEngine:
    def __init__(self, min_interval=5, max_speech_duration=5):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.speaking = False
        self.text_queue = []  # Hàng đợi chỉ lưu văn bản mới nhất
        self.last_text = ""
        self.last_speech_time = 0
        self.min_speech_interval = min_interval
        self.max_speech_duration = max_speech_duration  # Giới hạn thời gian đọc tối đa (15s)
        
        # Khởi tạo luồng đọc riêng biệt
        self.speech_thread = threading.Thread(target=self._process_speech_queue, daemon=True)
        self.speech_thread.start()

    def _process_speech_queue(self):
        while True:
            if self.text_queue and not self.speaking:
                text = self.text_queue[0]  # Lấy văn bản mới nhất (luôn là phần tử đầu tiên)
                self.text_queue = []  # Xóa hàng đợi sau khi lấy văn bản
                self.speaking = True
                
                # Tạo thread riêng để đọc văn bản
                speech_thread = threading.Thread(target=self._speak_with_timeout, args=(text,))
                speech_thread.start()
                
                # Chờ thread đọc hoàn thành hoặc hết thời gian
                speech_thread.join(timeout=self.max_speech_duration)
                
                # Nếu vẫn đang đọc, dừng engine
                if self.engine.isBusy():
                    self.engine.stop()
                
                self.speaking = False
                self.last_speech_time = time.time()
            
            time.sleep(0.1)

    def _speak_with_timeout(self, text):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Lỗi khi đọc văn bản: {e}")

    def say(self, text):
        current_time = time.time()
        
        # Chỉ thêm văn bản mới nếu khác văn bản trước đó và đã qua min_interval
        if text != self.last_text and (current_time - self.last_speech_time) >= self.min_speech_interval:
            # Xóa hàng đợi cũ và chỉ giữ văn bản mới nhất
            self.text_queue = [text]
            self.last_text = text

def perform_live_text():
    # Khởi tạo bộ xử lý OCR và bộ đọc văn bản
    ocr_processor = OCRProcessor()
    speech_engine = TextToSpeechEngine(min_interval=5, max_speech_duration=5)  

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Không thể mở camera")
        return

    ret, first_frame = cap.read()
    if not ret:
        print("Không thể đọc khung hình đầu tiên")
        return
    
    height, width = first_frame.shape[:2]
    roi_width = int(width * 0.8)
    roi_height = int(height * 0.4)
    roi_x = (width - roi_width) // 2
    roi_y = (height - roi_height) // 2

    frame_counter = 0
    ocr_interval = 30  

    print("Bắt đầu nhận diện văn bản trực tiếp. Nhấn 'q' để thoát.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Không thể đọc khung hình")
            break

        # Trích xuất vùng quan tâm (ROI)
        roi = frame[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width].copy()
        
        # Vẽ khung ROI
        cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_width, roi_y + roi_height), (0, 255, 0), 2)
        
        # Chỉ thêm frame vào hàng đợi OCR theo định kỳ
        frame_counter += 1
        if frame_counter >= ocr_interval:
            ocr_processor.add_frame(roi)
            frame_counter = 0
        
        # Lấy văn bản đã nhận diện và đọc
        recognized_text = ocr_processor.get_text()
        speech_engine.say(recognized_text)
        
        # Hiển thị văn bản trên màn hình
        cv2.putText(frame, recognized_text[:50], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Hiển thị trạng thái
        status = "On processing OCR" if ocr_processor.processing else "Ready"
        cv2.putText(frame, status, (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Nhan dien van ban truc tiep', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
