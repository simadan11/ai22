import cv2
import numpy as np
import os
import glob
from mtcnn import MTCNN
import logging

recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = MTCNN()

def get_face(img_bytes):
    try:
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None
            
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = detector.detect_faces(rgb_img)
        
        if len(results) == 0:
            # Fallback: assume center crop
            h, w = img.shape[:2]
            sz = min(h, w)
            y, x = (h - sz) // 2, (w - sz) // 2
            face = img[y:y+sz, x:x+sz]
        else:
            # Use the bounding box with highest confidence
            best_face = max(results, key=lambda r: r['confidence'])
            x, y, w, h = best_face['box']
            x = max(0, x)
            y = max(0, y)
            face = img[y:y+h, x:x+w]
            if face.size == 0:
                 return None
            
        gray_face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        return cv2.resize(gray_face, (200, 200))
    except Exception as e:
        logging.error(f"Error in get_face: {e}")
        return None

def train_model():
    faces = []
    ids = []
    label_map = {}
    current_id = 1
    
    base_dir = "data/faces/approved"
    if not os.path.exists(base_dir):
        return {}
        
    for user_dir in os.listdir(base_dir):
        user_path = os.path.join(base_dir, user_dir)
        if os.path.isdir(user_path):
            label_map[current_id] = user_dir
            for img_path in glob.glob(os.path.join(user_path, "*.png")):
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    # resize to 200x200 just in case
                    img = cv2.resize(img, (200, 200))
                    faces.append(img)
                    ids.append(current_id)
            current_id += 1
            
    if len(faces) > 0:
        recognizer.train(faces, np.array(ids))
    return label_map

label_map = train_model() or {}

def predict(img_bytes):
    face = get_face(img_bytes)
    if face is None:
        return None, None
        
    try:
        label, confidence = recognizer.predict(face)
        # confidence goes from 0 (perfect match) upwards. Let's allow up to 100 for LBPH.
        if confidence < 100:
            return label_map.get(label, None), confidence
    except cv2.error:
        pass
    return None, None
