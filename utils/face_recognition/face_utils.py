import face_recognition
import cv2
import easyocr
import numpy as np
import dlib
import os
def get_face_encodings(image_path):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    encodings = face_recognition.face_encodings(image, face_locations)
    return image, face_locations, encodings

# 1. Получаем лицо мальчика с фото 01-001.jpg (считаем, что он слева - берем первое лицо)
image_01, locations_01, encodings_01 = get_face_encodings('img\\01-002.jpg')
if len(encodings_01) == 0:
    raise Exception("Лицо на фото 01-001.jpg не найдено")
boy_encoding = encodings_01[1]  # берем первое лицо (мальчик слева)

# 2. Получаем лица с фото 02-000.jpg и 03-000.jpg
image_02, locations_02, encodings_02 = get_face_encodings('img\\02-000.jpg')
image_03, locations_03, encodings_03 = get_face_encodings('img\\03-000.jpg')

# 3. Функция для поиска совпадений
def find_match(boy_encoding, encodings, tolerance=0.6):
    matches = face_recognition.compare_faces(encodings, boy_encoding, tolerance)
    return matches

matches_02 = find_match(boy_encoding, encodings_02)
# matches_03 = find_match(boy_encoding, encodings_03)

# 4. Выводим результаты и координаты лиц, которые совпали
def find_white_strip(image_bgr, face_bottom, left, right, search_height=60):
    h, w, _ = image_bgr.shape
    # Ограничим область поиска по ширине лица с небольшим запасом
    x1 = max(left - 10, 0)
    x2 = min(right + 10, w)
    # Ищем белую полосу в диапазоне от face_bottom до face_bottom + search_height
    for y in range(face_bottom, min(face_bottom + search_height, h)):
        line = image_bgr[y, x1:x2]
        # Преобразуем в яркость (оттенки серого)
        gray_line = cv2.cvtColor(line[np.newaxis, :, :], cv2.COLOR_BGR2GRAY)[0]
        # Считаем, сколько пикселей почти белые (например, > 230)
        white_pixels = np.sum(gray_line > 230)
        # Если больше 80% пикселей белые - нашли белую полосу
        if white_pixels / (x2 - x1) > 0.8:
            return y
    # Если не нашли, возвращаем стандартную границу (например, face_bottom + 10)
    return face_bottom + 10

def find_left_text_border(image_bgr, face_bottom, left, search_width=200):
    h, w, _ = image_bgr.shape
    # Идём влево от left до 0
    for x in range(left-1, -1, -1):
        column = image_bgr[face_bottom:face_bottom+search_width, x]
        # Проверяем, одинаковы ли все пиксели в этой колонке
        if np.all(np.all(column == column[0], axis=1)):
            return x
    return 0

def find_top_text_border(image_bgr, left_border, face_bottom, search_height=1000):
    h, w, _ = image_bgr.shape
    # Идём вниз от face_bottom до face_bottom+search_height
    for y in range(face_bottom, min(face_bottom+search_height, h)):
        row = image_bgr[y, left_border:left_border+1000]
        # Проверяем, одинаковы ли все пиксели в этой строке
        if np.all(np.all(row == row[0], axis=1)):
            return y
    return face_bottom

def draw_boxes_and_extract_names_adaptive(image, face_locations, matches, image_path, save_path, width=600):
    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    reader = easyocr.Reader(['ru'])
    for i, match in enumerate(matches):
        if match:
            top, right, bottom, left = face_locations[i]
            cv2.rectangle(image_bgr, (left, top), (right, bottom), (0, 255, 0), 2)

            # 1. Ищем левую границу текста
            left_border = find_left_text_border(image_bgr, bottom, left, search_width=200)
            # 2. Ищем верхнюю границу текста
            top_border = find_top_text_border(image_bgr, left_border, bottom, search_height=1400)
            # 3. Нижняя и правая границы
            roi_top = top_border
            roi_bottom = min(top_border + 90, image_bgr.shape[0])
            roi_left = left_border
            roi_right = min(left_border + 1000, image_bgr.shape[1])
            roi = image_bgr[roi_top:roi_bottom, roi_left:roi_right]

            # OCR для извлечения текста
            result = reader.readtext(roi)
            name = "Не найдено"
            if result:
                name = max(result, key=lambda x: len(x[1]))[1]
            print(f"Найден мальчик на {image_path} с именем: {name}")

draw_boxes_and_extract_names_adaptive(image_02, locations_02, matches_02, '02-000.jpg', '02-000_result.jpg')
#draw_boxes_and_extract_names(image_03, locations_03, matches_03, '03-000.jpg', '03-000_result.jpg')


