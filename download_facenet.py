from deepface import DeepFace
import numpy as np

img = np.zeros((224, 224, 3), dtype=np.uint8)
try:
    res = DeepFace.represent(img, model_name="Facenet512", enforce_detection=False)
    print("Facenet512 Model loaded")
except Exception as e:
    print(e)
