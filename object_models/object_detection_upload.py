from gtts import gTTS
import torch
from PIL import Image
import os
from datetime import datetime
from transformers import BlipProcessor, BlipForConditionalGeneration
from flask import Flask

app = Flask(__name__)

app.config['AUDIO_FOLDER'] = 'static/audio'

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def detect_objects(image_path):
    
    raw = Image.open(image_path).convert("RGB")
    inputs = processor(raw, return_tensors="pt")
    out = caption_model.generate(**inputs)
    description_text = processor.decode(out[0], skip_special_tokens=True).capitalize()

    # Generate audio from text
        
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    tts = gTTS(description_text, lang='en')

    audio_path = os.path.join(app.config['AUDIO_FOLDER'] ,  f'desciption_{timestamp}.mp3' )

    tts.save(audio_path)
    
    return description_text, audio_path, timestamp
