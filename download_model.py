from deepface import DeepFace
import numpy as np
import cv2

# Dummy image to trigger model download
img = np.zeros((224, 224, 3), dtype=np.uint8)
try:
    DeepFace.represent(img, model_name="VGG-Face", enforce_detection=False)
    print("Model loaded")
except Exception as e:
    print(e)
