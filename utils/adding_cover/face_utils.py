import json
import os
import glob
import face_recognition
import cv2
import easyocr
import numpy as np
import Levenshtein
from utils.file_utils import extractNumber, getJpegFilenames
from utils.photoshop_utils import designs_album, types_album


def load_album_coordinates():
    """
    Загружает координаты альбомов из settings.json.

    Returns:
        dict: Словарь с координатами или значения по умолчанию, если файл отсутствует/некорректен.
    """
    settings_file = os.path.join(os.path.dirname(__file__), r"..\settings.json")
    default_coordinates = {
        "Темный": {
            "Мини": [6400, 4160, 6630, 1460],
            "Медиум": [6400, 4160, 6630, 1460],
            "Премиум": [6400, 4160, 6630, 1460]
        },
        "Светлый": {
            "Мини": [6460, 2950, 6680, 450],
            "Медиум": None,
            "Премиум": [3350, 4450, 3670, 250]
        }
    }

    try:
        if os.path.exists(settings_file):
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
                return settings.get("album_coordinates", default_coordinates)
        else:
            print(f"Файл {settings_file} не найден. Используются координаты по умолчанию.")
            return default_coordinates
    except Exception as e:
        print(f"Ошибка при загрузке {settings_file}: {e}. Используются координаты по умолчанию.")
        return default_coordinates


def match_with_dictionary(recognized_text, name_dictionary, max_distance=3):
    """
    Сравнивает распознанный текст с именами из словаря, используя расстояние Левенштейна.
    Сравнение регистронезависимое.

    Args:
        recognized_text (str): Распознанный текст для сравнения.
        name_dictionary (iterable): Список или множество имен для сравнения.
        max_distance (int): Максимально допустимое расстояние Левенштейна (по умолчанию 3).

    Returns:
        str or None: Лучшее совпадающее имя из словаря или None, если подходящего совпадения нет.
    """
    recognized_text = recognized_text.strip().lower()
    best_match = None
    best_distance = None
    multiple_name_options = False

    for name in name_dictionary:
        name_lower = name.lower()
        dist = Levenshtein.distance(recognized_text, name_lower)
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


# def preprocess_for_ocr(roi):
#     gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
#     # Усиление контраста
#     alpha = 1.7  # Множитель контраста
#     beta = 10  # Смещение яркости
#     contrast = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
#     # Бинаризация (порог можно подобрать)
#     _, binary = cv2.threshold(contrast, 180, 255, cv2.THRESH_BINARY)
#     # Увеличение размера (если текст мелкий)
#     scale = 2
#     enlarged = cv2.resize(binary, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
#     return enlarged


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
        [-1, 9, -1],
        [-1, -1, -1]
    ])
    sharpened = cv2.filter2D(resized, -1, kernel)

    return sharpened


def get_leftmost_word(words):
    """
    Находит самое левое слово (или блок) в words от easyocr.readtext.
    Возвращает текст этого блока.
    """
    leftmost_text = "Не найдено"
    if not words:
        return leftmost_text

    min_x = float('inf')
    for item in words:
        bbox = item[0]  # bounding box: список из 4 точек
        text = item[1]
        # x-координата самой левой точки блока (обычно bbox[0][0])
        x = min(point[0] for point in bbox)
        if x < min_x:
            min_x = x
            leftmost_text = text
    return leftmost_text


def get_upmost_word(words):
    return


def extract_words_from_coordinates(image_bgr, roi_coordinates, reader):
    """
    Извлекает текст из заданной области изображения с помощью OCR.

    Args:
        image_bgr: Изображение в формате BGR (numpy array).
        roi_coordinates: Кортеж (top, right, bottom, left) с координатами области интереса.
        reader: Объект для OCR (например, easyocr.Reader).

    Returns:
        list: Список результатов OCR, где каждый элемент содержит данные о распознанном тексте
              (например, координаты, текст, уверенность). Пустой список, если ничего не найдено.
    """
    # Извлекаем координаты области интереса
    top, right, bottom, left = roi_coordinates

    # Ограничиваем координаты размерами изображения
    roi_top = max(top, 0)
    roi_bottom = min(bottom, image_bgr.shape[0])
    roi_left = max(left, 0)
    roi_right = min(right, image_bgr.shape[1])

    # Извлекаем область интереса (ROI)
    roi = image_bgr[roi_top:roi_bottom, roi_left:roi_right]

    # Предобработка изображения для OCR
    roi = preprocess_for_ocr(roi)

    # Для отладки сохраняем ROI
    cv2.imwrite("debug_roi.png", roi)

    # OCR для извлечения текста
    result = reader.readtext(
        roi,
        detail=1,
        paragraph=False,
        contrast_ths=0.1,  # Уменьшенный порог контраста
        adjust_contrast=0.5,  # Настройка контраста
        width_ths=0.5,  # Настройка ширины текста
        height_ths=0.5,  # Настройка высоты текста
    )

    return result


def extract_surname_from_face(image_bgr, face_location, reader):
    """
    Извлекает имя из изображения на основе положения лица.

    Args:
        image_bgr: Изображение в формате BGR (numpy array).
        face_location: Кортеж (top, right, bottom, left) с координатами лица.
        reader: Объект для OCR (например, easyocr.Reader).

    Returns:
        str: Найденное имя или None, если ничего не найдено.
    """
    top, right, bottom, left = face_location

    # 1. Ищем левую границу текста
    left_border = find_left_text_border(image_bgr, bottom, left, search_width=200)
    # 2. Ищем верхнюю границу текста
    top_border = find_top_text_border(image_bgr, left_border, bottom) + 50
    # 3. Определяем координаты области интереса (ROI)
    roi_top = top_border
    roi_bottom = min(top_border + 130, image_bgr.shape[0])
    roi_left = left_border
    roi_right = min(left_border + 1000, image_bgr.shape[1])

    # Формируем кортеж координат для функции извлечения слова
    roi_coordinates = (roi_top, roi_right, roi_bottom, roi_left)

    # Извлекаем имя с помощью функции extract_word_from_coordinates
    words = extract_words_from_coordinates(image_bgr, roi_coordinates, reader)

    surname = get_leftmost_word(words)

    return surname


def extract_surname_from_portrait(image_bgr, words_coordinates, reader):
    """
    Извлекает фамилию с соответствующего по виду и типу альбома портрета.

    Args:
        image_bgr: Изображение в формате BGR (numpy array).
        words_coordinates: Кортеж (top, right, bottom, left) с координатами слов.
        reader: Объект для OCR (например, easyocr.Reader).

    Returns:
        str: Найденная фамилия или None, если ничего не найдено.
    """
    top, right, bottom, left = words_coordinates

    roi_top = max(top, 0)
    roi_bottom = min(bottom, image_bgr.shape[0])
    roi_left = max(left, 0)
    roi_right = min(right, image_bgr.shape[1])

    roi_coordinates = (roi_top, roi_right, roi_bottom, roi_left)

    words = extract_words_from_coordinates(image_bgr, roi_coordinates, reader)

    surname = get_leftmost_word(words)

    return surname


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


def find_surname_for_portrait_from_dark_album(portrait_path, all_student_names):
    coords_for_words_from_portrait_dark_album = (6400, 4160, 6650, 1460)
    image = face_recognition.load_image_file(portrait_path)
    reader = easyocr.Reader(['ru'])
    surname = extract_surname_from_portrait(image_bgr=image,
                                            words_coordinates=coords_for_words_from_portrait_dark_album,
                                            reader=reader)
    surname_final = match_with_dictionary(surname, all_student_names, max_distance=2)

    return surname_final


def find_surname_for_portrait(portrait_path,
                              all_student_names,
                              album_design,
                              album_version,
                              collages_data=None,
                              tolerance=0.6):
    """
    Универсальная функция для извлечения фамилии из портрета на основе типа альбома и дизайна.

    Args:
        portrait_path (str): Путь к изображению портрета.
        all_student_names (list): Список всех возможных фамилий.
        album_design (str): Дизайн альбома ('Светлый' или 'Темный').
        album_version (str): Тип альбома ('Мини', 'Медиум', 'Премиум').
        collages_data (list, optional): Данные коллажей для светлого медиума.
        tolerance (float, optional): Порог для распознавания лиц (для коллажей).

    Returns:
        str or None: Найденная фамилия или None, если не найдено.
    """
    # Проверяем, является ли это светлым медиумом
    if album_design == designs_album[0] and album_version == types_album[1]:
        if collages_data is None:
            print(f"Ошибка: collages_data не предоставлены для {album_design}/{album_version}")
            return None
        return find_surname_for_portrait_from_collage(
            portrait_path=portrait_path,
            collages_data=collages_data,
            all_student_names=all_student_names,
            tolerance=tolerance
        )

    # Загружаем координаты из settings.json
    album_coordinates = load_album_coordinates()
    coords = album_coordinates.get(album_design, {}).get(album_version)
    if coords is None:
        print(f"Координаты не найдены для {album_design}/{album_version}")
        return None

    image = face_recognition.load_image_file(portrait_path)
    reader = easyocr.Reader(['ru'])

    surname = extract_surname_from_portrait(
        image_bgr=image,
        words_coordinates=tuple(coords),  # Преобразуем список в кортеж
        reader=reader
    )

    if surname and ' ' in surname:
        surname = surname.split(' ')[0]

    surname_final = match_with_dictionary(surname, all_student_names, max_distance=2)
    return surname_final


def find_surname_for_portrait_from_light_prem(portrait_path, all_student_names):
    coords_for_words_from_portrait_dark_album = (6400, 4160, 6630, 1460)
    image = face_recognition.load_image_file(portrait_path)
    reader = easyocr.Reader(['ru'])
    surname = extract_surname_from_portrait(image_bgr=image,
                                            words_coordinates=coords_for_words_from_portrait_dark_album,
                                            reader=reader)
    surname_final = match_with_dictionary(surname, all_student_names, max_distance=2)

    return surname_final


def find_surname_for_portrait_from_collage(portrait_path, collages_data, all_student_names, tolerance=0.6):
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
            surname = extract_surname_from_face(image_bgr, locations_collage[best_match_index], reader)

            if surname and ' ' in surname:
                surname = surname.split(' ')[0]

            surname_final = match_with_dictionary(surname, all_student_names, max_distance=2)
            print(
                f"Портрет: {os.path.basename(portrait_path)} | Коллаж: {os.path.basename(collage['path'])} | Имя: {surname_final}")
            return surname_final
    print(f"Портрет: {os.path.basename(portrait_path)} | Имя не найдено на коллажах")
    return None


def get_portrait_name_pairs(portrait_files_path, collage_files_path, all_student_names, album_version, album_design):
    """
    Создает пары (фамилия, индекс портрета) для портретов на основе коллажей и альбома.

    Args:
        portrait_files_path (str): Путь к папке с портретами.
        collage_files_path (str): Путь к папке с коллажами.
        all_student_names (list): Список всех возможных фамилий.
        album_version (str): Тип альбома ('Мини', 'Медиум', 'Премиум').
        album_design (str): Дизайн альбома ('Светлый' или 'Темный').

    Returns:
        list: Список кортежей (фамилия, индекс портрета).
    """
    portrait_files = sorted(getJpegFilenames(portrait_files_path), key=extractNumber)
    collage_files = sorted(getJpegFilenames(collage_files_path), key=extractNumber)

    portrait_files = [os.path.join(portrait_files_path, f) for f in portrait_files]
    collage_files = [os.path.join(collage_files_path, f) for f in collage_files]

    # Предобработка коллажей только для светлого медиума
    collages_data = None
    if album_design == 'Светлый' and album_version == 'Медиум':
        collages_data = preprocess_collages(collage_files)

    name_to_portrait_index = {}
    for idx, portrait_path in enumerate(portrait_files):
        name_final = find_surname_for_portrait(
            portrait_path=portrait_path,
            all_student_names=all_student_names,
            album_design=album_design,
            album_version=album_version,
            collages_data=collages_data,
            tolerance=0.4
        )
        if name_final is not None:
            if name_final in name_to_portrait_index:
                # Конфликт, если фамилия уже связана с другим портретом
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
    "Зияева", "Акылбекова",
    "Шуплецова",  # темный
    "Павлушина",  # светлый прем
    "Пучкин"  # светлый мини
]

# Пути к портретам и коллажам
portrait_files_path = r'C:\programms\undr\package\utils\adding_cover\img\развр_мин'
collage_files_path = r'C:\programms\undr\package\utils\adding_cover\img\сп'

print(get_portrait_name_pairs(portrait_files_path, collage_files_path, all_student_names,
                              album_version=types_album[0],
                              album_design=designs_album[0]))
