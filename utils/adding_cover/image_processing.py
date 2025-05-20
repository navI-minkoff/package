import cv2
import numpy as np


def preprocess_for_ocr(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    alpha = 1.7  # Множитель контраста
    beta = 10  # Смещение яркости
    contrast = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
    _, binary = cv2.threshold(contrast, 180, 255, cv2.THRESH_BINARY)
    scale = 2
    enlarged = cv2.resize(binary, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return enlarged


def preprocess_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Инвертировать, если фон тёмный, а текст светлый
    mean_brightness = np.mean(gray)
    if mean_brightness < 127:
        gray = cv2.bitwise_not(gray)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    binary = cv2.adaptiveThreshold(
        enhanced, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15,
        C=10
    )

    scale = 2
    resized = cv2.resize(binary, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # Повышение резкости
    kernel = np.array([
        [-1, -1, -1],
        [-1, 9, -1],
        [-1, -1, -1]
    ])
    sharpened = cv2.filter2D(resized, -1, kernel)

    return sharpened


def find_left_text_border(image_bgr, face_bottom, left, search_width=200):
    h, w, _ = image_bgr.shape
    for x in range(left - 1, -1, -1):
        column = image_bgr[face_bottom:face_bottom + search_width, x]
        if np.all(np.all(column == column[0], axis=1)):
            return x
    return 0


def find_top_text_border(image_bgr, left_border, face_bottom, search_wight=1000):
    h, w, _ = image_bgr.shape
    for y in range(face_bottom, h):
        row = image_bgr[y, left_border:left_border + search_wight]
        if np.all(np.all(row == row[0], axis=1)):
            return y
    return face_bottom
