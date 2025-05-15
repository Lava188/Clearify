# Clearify

A Flask-based assistive web application that helps users with visual impairments interact with text and objects in images and live camera feeds. Clearify supports:

- **Text-to-speech**: click on any word or interface element to hear it spoken aloud
- **OCR (image upload & capture)**: extract printed or handwritten text from uploaded images or webcam snapshots
- **Object detection**: identify and describe objects in images, snapshots, or real-time video

---

## Features

1. **Text Recognition (Upload)**
   - Upload an image containing text
   - Server runs OCR and returns the extracted text plus an MP3 audio file
2. **Text Recognition (Capture)**
   - Snap a photo via your webcam (press **C**)
   - Server processes the frame, extracts text, and plays the result
3. **Text Recognition (Live)**
   - Live OCR on your webcam feed; displays and speaks new text at regular intervals
4. **Object Detection (Upload & Capture)**
   - Upload an image or snap via webcam
   - Uses YOLOv5 + optional image captioning to identify objects and describe the scene
5. **Object Detection (Live)**
   - Real-time object detection on webcam feed; speaks detections every few seconds

---

## Prerequisites

- **Python 3.10** (or compatible 3.x)
- **pip** (Python package installer)
- A modern web browser

## Installation

# 1. Clone the repository

git clone https://github.com/Lava188/Clearify_Project.git
cd Clearify_Project

# 2. Install dependencies

pip install --upgrade pip
pip install -r requirements.txt

# 3. Usage

python main.py
