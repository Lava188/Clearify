from flask import Flask
import cv2
import torch
from gtts import gTTS
import os
from datetime import datetime
from PIL import Image
import numpy as np
from transformers import BlipProcessor, BlipForConditionalGeneration

app = Flask(__name__, static_folder='static')
app.config['AUDIO_FOLDER'] = 'static/audio'

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def adjust_brightness_contrast(img, alpha=1.0, beta=0):

    # Apply brightness and contrast adjustment
    adjusted_img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

    return adjusted_img

  
def perform_object_detection():
    cap = cv2.VideoCapture(0)
    # Load YOLOv5 model
    model = torch.hub.load('ultralytics/yolov5', 'yolov5l', pretrained=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow('Press "c" to Capture or "Esc" to Exit', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            # Save original
            original_img_path = 'static/captured/captured_image.jpg'
            cv2.imwrite(original_img_path, frame)
            # Adjust
            adjusted = adjust_brightness_contrast(frame, alpha=1.5, beta=20)
            adjusted_img_path = 'static/captured/adjusted_captured_image.jpg'
            cv2.imwrite(adjusted_img_path, adjusted)

            # Optional YOLO detection
            results = model(adjusted)

            # Caption with BLIP
            rgb = cv2.cvtColor(adjusted, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            inputs = processor(pil_img, return_tensors="pt")
            out = caption_model.generate(**inputs)
            description_text = processor.decode(out[0], skip_special_tokens=True).capitalize()

            # Append YOLO labels
            labels = results.pandas().xyxy[0]['name'].unique()
            obj_list = ", ".join(labels) if labels.size > 0 else "no objects"
            description_text += f" (Objects detected: {obj_list}.)"

            # Generate and save audio
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            audio_filename = f'description_{timestamp}.mp3'
            audio_path = os.path.join('static/audio', audio_filename)
            tts = gTTS(description_text, lang='en')
            tts.save(audio_path)

            cap.release()
            cv2.destroyAllWindows()
            return description_text, adjusted_img_path, audio_filename

        elif key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    return "", "", ""


