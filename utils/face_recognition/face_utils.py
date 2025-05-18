import os
import glob
import face_recognition
import cv2
import easyocr
import numpy as np
import Levenshtein
from utils.file_utils import extractNumber, getJpegFilenames


def match_with_dictionary(recognized_text, name_dictionary, max_distance=3):
    recognized_text = recognized_text.strip()
    best_match = None
    best_distance = None
    multiple_name_options = False

    for name in name_dictionary:
        dist = Levenshtein.distance(recognized_text, name)
        if best_distance is None or dist < best_distance:
            best_distance = dist
            best_match = name
            multiple_name_options = False
        elif dist == best_distance:
            multiple_name_options = True
    if best_distance is not None and \
            not multiple_name_options and \
            best_distance <= max_distance:
        return best_match
    else:
        return None


def get_face_encodings(image_path):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    encodings = face_recognition.face_encodings(image, face_locations)
    return image, face_locations, encodings


def find_left_text_border(image_bgr, face_bottom, left, search_width=200):
    h, w, _ = image_bgr.shape
    # Идём влево от left до 0
    for x in range(left - 1, -1, -1):
        column = image_bgr[face_bottom:face_bottom + search_width, x]
        # Проверяем, одинаковы ли все пиксели в этой колонке
        if np.all(np.all(column == column[0], axis=1)):
            return x
    return 0


def find_top_text_border(image_bgr, left_border, face_bottom, search_wight=1000):
    h, w, _ = image_bgr.shape
    # Идём вниз от face_bottom до face_bottom+search_height
    for y in range(face_bottom, h):
        row = image_bgr[y, left_border:left_border + search_wight]
        # Проверяем, одинаковы ли все пиксели в этой строке
        if np.all(np.all(row == row[0], axis=1)):
            return y
    return face_bottom


def preprocess_for_ocr(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # Усиление контраста
    alpha = 1.7  # Множитель контраста
    beta = 10  # Смещение яркости
    contrast = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
    # Бинаризация (порог можно подобрать)
    _, binary = cv2.threshold(contrast, 180, 255, cv2.THRESH_BINARY)
    # Увеличение размера (если текст мелкий)
    scale = 2
    enlarged = cv2.resize(binary, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return enlarged


def preprocess_image(img):
    # Перевод в оттенки серого
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Инвертировать, если фон тёмный, а текст светлый
    mean_brightness = np.mean(gray)
    if mean_brightness < 127:
        gray = cv2.bitwise_not(gray)

    # Увеличение контраста (CLAHE — адаптивное выравнивание гистограммы)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Адаптивная бинаризация
    binary = cv2.adaptiveThreshold(
        enhanced, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15,
        C=10
    )

    # Увеличение масштаба
    scale = 2
    resized = cv2.resize(binary, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # Повышение резкости
    kernel = np.array([
        [-1, -1, -1],
        [-1,  9, -1],
        [-1, -1, -1]
    ])
    sharpened = cv2.filter2D(resized, -1, kernel)

    return sharpened

def get_leftmost_word(result):
    """
    Находит самое левое слово (или блок) в result от easyocr.readtext.
    Возвращает текст этого блока.
    """
    leftmost_text = "Не найдено"
    if not result:
        return leftmost_text

    min_x = float('inf')
    for item in result:
        bbox = item[0]  # bounding box: список из 4 точек
        text = item[1]
        # x-координата самой левой точки блока (обычно bbox[0][0])
        x = min(point[0] for point in bbox)
        if x < min_x:
            min_x = x
            leftmost_text = text
    return leftmost_text

def extract_name_from_face(image_bgr, face_location, reader):
    top, right, bottom, left = face_location
    cv2.rectangle(image_bgr, (left, top), (right, bottom), (0, 255, 0), 2)

    # 1. Ищем левую границу текста
    left_border = find_left_text_border(image_bgr, bottom, left, search_width=200)
    # 2. Ищем верхнюю границу текста
    top_border = find_top_text_border(image_bgr, left_border, bottom) + 50
    # 3. Нижняя и правая границы
    roi_top = top_border
    roi_bottom = min(top_border + 130, image_bgr.shape[0])
    roi_left = left_border
    roi_right = min(left_border + 1000, image_bgr.shape[1])
    roi = image_bgr[roi_top:roi_bottom, roi_left:roi_right]
    roi = preprocess_for_ocr(roi)

    cv2.imwrite("debug_roi.png", roi)

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

    name = get_leftmost_word(result)

    return name


def get_top_faces(locations, encodings, top_n=2):
    # locations: список кортежей (top, right, bottom, left)
    # encodings: список эмбеддингов в том же порядке

    # Получаем индексы сортировки по координате top (от меньшего к большему)
    sorted_indices = sorted(range(len(locations)), key=lambda i: locations[i][0])
    # Берём индексы верхних top_n лиц
    selected_indices = sorted_indices[:top_n]
    # Возвращаем только выбранные лица и их эмбеддинги
    locations = [locations[i] for i in selected_indices]
    encodings = [encodings[i] for i in selected_indices]

    return locations, encodings


def preprocess_collages(collage_paths):
    collages_data = []
    for path in collage_paths:
        image, locations, encodings = get_face_encodings(path)
        locations, encodings = get_top_faces(locations, encodings, top_n=2) if len(locations) > 4 else (
        locations, encodings)
        collages_data.append({
            "path": path,
            "image": image,
            "locations": locations,
            "encodings": encodings
        })
    return collages_data

def find_name_for_portrait_from_portrait():
    return
def find_name_for_portrait_from_collage(portrait_path, collages_data, all_student_names, tolerance=0.6):
    image_portrait, locations_portrait, encodings_portrait = get_face_encodings(portrait_path)
    if not encodings_portrait:
        print(f"Лицо не найдено на {portrait_path}")
        return None
    portrait_encoding = encodings_portrait[0]
    reader = easyocr.Reader(['ru'])

    for collage in collages_data:
        encodings_collage = collage["encodings"]
        locations_collage = collage["locations"]
        image_collage = collage["image"]
        if not encodings_collage:
            continue
        distances = face_recognition.face_distance(encodings_collage, portrait_encoding)
        matches = face_recognition.compare_faces(encodings_collage, portrait_encoding, tolerance)
        match_indices = [i for i, is_match in enumerate(matches) if is_match]
        if match_indices:
            best_match_index = min(match_indices, key=lambda i: distances[i])
            image_bgr = cv2.cvtColor(image_collage, cv2.COLOR_RGB2BGR)
            name_raw = extract_name_from_face(image_bgr, locations_collage[best_match_index], reader)
            name_final = match_with_dictionary(name_raw.split(' ')[0], all_student_names, max_distance=2)
            print(
                f"Портрет: {os.path.basename(portrait_path)} | Коллаж: {os.path.basename(collage['path'])} | Имя: {name_final}")
            return name_final
    print(f"Портрет: {os.path.basename(portrait_path)} | Имя не найдено на коллажах")
    return None


def get_portrait_name_pairs(portrait_files_path, collage_files_path, all_student_names):
    portrait_files = sorted(getJpegFilenames(portrait_files_path), key=extractNumber)
    collage_files = sorted(getJpegFilenames(collage_files_path), key=extractNumber)

    portrait_files = [os.path.join(portrait_files_path, f) for f in portrait_files]
    collage_files = [os.path.join(collage_files_path, f) for f in collage_files]
    collages_data = preprocess_collages(collage_files)

    name_to_portrait_index = {}
    for idx, portrait_path in enumerate(portrait_files):
        name_final = find_name_for_portrait_from_collage(portrait_path, collages_data, all_student_names, tolerance=0.4)

        if name_final is not None:
            if name_final in name_to_portrait_index:
                # Конфликт если фамилия уже связано с другим портретом
                prev_idx = name_to_portrait_index[name_final]
                print(f"Конфликт для имени '{name_final}': портреты {prev_idx} и {idx} получают None")
                name_to_portrait_index[name_final] = None
            else:
                name_to_portrait_index[name_final] = idx

    results = [(name, idx) for name, idx in name_to_portrait_index.items() if idx is not None]

    return results

# Список всех возможных имён
all_student_names = [
    "Тевосян", "Лисица", "Фасаева", "Грехов",
    "Фокин", "Абаимова", "Войт", "Ахунов",
    "Деревянко", "Болотова", "Жуманазарова", "Дюрич",
    "Плеханов", "Хдрян", "Акрамова", "Нечеухин",
    "Зияева", "Акылбекова"
]

# Пути к портретам и коллажам
portrait_files_path = r'C:\programms\undr\package\utils\face_recognition\img\развр'
collage_files_path = r'C:\programms\undr\package\utils\face_recognition\img\сп'

print(get_portrait_name_pairs(portrait_files_path, collage_files_path, all_student_names))