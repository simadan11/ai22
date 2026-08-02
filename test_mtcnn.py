from mtcnn import MTCNN
import cv2
import numpy as np

try:
    detector = MTCNN()
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    results = detector.detect_faces(img)
    print("MTCNN works:", results)
except Exception as e:
    print(e)
