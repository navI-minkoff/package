import os
import glob
import face_recognition
import cv2
import easyocr
import numpy as np
import Levenshtein

# Список всех возможных имён
all_student_names = [
    "Ахунов Максим", "Грехов Максим", "Болотова Нурайым", "Тевосян Карен",
    "Лисина Дарья", "Фокин Ярослав", "Абламова Лидия", "Фасхеева Кристина",
    "Войт Ева", "Деревянко Егор", "Плеханов Виталий", "Харин Мария",
    "Жуманазарова Аруж", "Дорен Артем", "Акрамова Залинаб", "Нечаухин Артем"
]

def match_with_dictionary(recognized_text, name_dictionary, max_distance=3):
    recognized_text = recognized_text.strip()
    best_match = None
    best_distance = None
    for name in name_dictionary:
        dist = Levenshtein.distance(recognized_text, name)
        if best_distance is None or dist < best_distance:
            best_distance = dist
            best_match = name
    if best_distance is not None and best_distance <= max_distance:
        return best_match
    else:
        return recognized_text

def get_face_encodings(image_path):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    encodings = face_recognition.face_encodings(image, face_locations)
    return image, face_locations, encodings

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

def preprocess_for_ocr(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # Усиление контраста
    alpha = 1.7  # Множитель контраста
    beta = 10    # Смещение яркости
    contrast = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
    # Бинаризация (порог можно подобрать)
    _, binary = cv2.threshold(contrast, 180, 255, cv2.THRESH_BINARY)
    # Увеличение размера (если текст мелкий)
    scale = 2
    enlarged = cv2.resize(binary, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return enlarged

def extract_name_from_face(image_bgr, face_location, reader):
    top, right, bottom, left = face_location
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
    roi = preprocess_for_ocr(roi)

    # OCR для извлечения текста
    result = reader.readtext(
        roi,
        detail=1,
        paragraph=False,
        contrast_ths=0.1,  # Уменьшите порог контраста для лучшего распознавания
        adjust_contrast=0.5,  # Настройте контраст
        width_ths=0.5,  # Экспериментируйте с этим значением
        height_ths=0.5,  # И с этим
    )
    name = "Не найдено"
    if result:
        name = max(result, key=lambda x: len(x[1]))[1]

    return name

def find_name_for_portrait(portrait_path, collage_paths, all_student_names, tolerance=0.6):
    image_portrait, locations_portrait, encodings_portrait = get_face_encodings(portrait_path)
    if not encodings_portrait:
        print(f"Лицо не найдено на {portrait_path}")
        return None

    # Если на портрете несколько лиц, выберите нужный индекс (например, 0)
    portrait_encoding = encodings_portrait[1]
    reader = easyocr.Reader(['ru'])

    for collage_path in collage_paths:
        image_collage, locations_collage, encodings_collage = get_face_encodings(collage_path)
        if not encodings_collage:
            continue

        # Получаем массив расстояний
        distances = face_recognition.face_distance(encodings_collage, portrait_encoding)
        # Фильтруем только те, что проходят по tolerance
        matches = face_recognition.compare_faces(encodings_collage, portrait_encoding, tolerance)
        match_indices = [i for i, is_match in enumerate(matches) if is_match]

        if match_indices:
            # Выбираем индекс с минимальным расстоянием среди совпавших
            best_match_index = min(match_indices, key=lambda i: distances[i])
            image_bgr = cv2.cvtColor(image_collage, cv2.COLOR_RGB2BGR)
            name_raw = extract_name_from_face(image_bgr, locations_collage[best_match_index], reader)
            name_final = match_with_dictionary(name_raw, all_student_names, max_distance=3)
            print(f"Портрет: {os.path.basename(portrait_path)} | Коллаж: {os.path.basename(collage_path)} | Имя: {name_final}")
            return name_final

    print(f"Портрет: {os.path.basename(portrait_path)} | Имя не найдено на коллажах")
    return None

# Пути к портретам и коллажам
portrait_files = sorted(glob.glob('img/01-*.jpg'))
collage_files = sorted(glob.glob('img/02-*.jpg') + glob.glob('img/03-*.jpg'))

# Для каждого портрета ищем имя на коллажах
for portrait_path in portrait_files:
    find_name_for_portrait(portrait_path, collage_files, all_student_names, tolerance=0.4)