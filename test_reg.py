import requests
import cv2
import numpy as np

# Create dummy user image
img = np.zeros((200, 200, 3), dtype=np.uint8)
cv2.rectangle(img, (50, 50), (150, 150), (255, 255, 255), -1)
cv2.imwrite("test_face.png", img)

with open("test_face.png", "rb") as f:
    res = requests.post("http://localhost:8000/api/register", data={"username": "test_user"}, files={"photo": f})
print("Register:", res.json())
