import cv2
import torch
import pyttsx3
import time
import threading
import numpy as np
from ultralytics import YOLO

def preprocess_frame(frame):
    """Tiền xử lý nhẹ giữ nguyên màu sắc"""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    v = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(v)
    enhanced_hsv = cv2.merge([h, s, v])
    return cv2.cvtColor(enhanced_hsv, cv2.COLOR_HSV2BGR)

def object_detection():
    model = YOLO('yolov8m.pt')
    model.conf = 0.5
    
    tts_engine = pyttsx3.init()
    def speak(txt):
        tts_engine.say(txt)
        tts_engine.runAndWait()

    cap = cv2.VideoCapture(0)
    last_speech = 0
    speech_interval = 5
    detected_objects = []

    while True:
        ret, frame = cap.read()
        if not ret: break

        results = model(frame, verbose=False)
        current_frame_objects = []

        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                if box.conf >= 0.5:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    class_name = model.names[int(box.cls)]
                    current_frame_objects.append(class_name)
                    confidence = box.conf.item()
                    
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{class_name} {confidence:.2f}", 
                              (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, 
                              (0,255,0), 2)

        detected_objects = current_frame_objects

        now = time.time()
        if now - last_speech > speech_interval:
            last_speech = now
            labels = [model.names[int(box.cls)] for box in results[0].boxes if box.conf >= 0.5]
            if labels:
                threading.Thread(target=speak, args=(f"I see {', '.join(labels)}",)).start()

        cv2.imshow('Detection (Press C to quit)', frame)
        if cv2.waitKey(1) & 0xFF == ord('c'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return detected_objects