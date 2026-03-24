import os
from mvp.app import _ensure_sample_image, _SAMPLE_FILE
import cv2

if os.path.exists(_SAMPLE_FILE):
    os.remove(_SAMPLE_FILE)
_ensure_sample_image()
img = cv2.imread(_SAMPLE_FILE)
print("TestPrint.png shape:", img.shape)
print("Success!")
