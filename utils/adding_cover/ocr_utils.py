import cv2
import easyocr
import numpy as np
import Levenshtein
from utils.adding_cover.image_processing import preprocess_for_ocr, find_left_text_border, find_top_text_border


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
        bbox = item[0]
        text = item[1]
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
    top, right, bottom, left = roi_coordinates

    # Ограничиваем координаты размерами изображения
    roi_top = max(top, 0)
    roi_bottom = min(bottom, image_bgr.shape[0])
    roi_left = max(left, 0)
    roi_right = min(right, image_bgr.shape[1])

    roi = image_bgr[roi_top:roi_bottom, roi_left:roi_right]

    roi = preprocess_for_ocr(roi)

    # Сохраняем для отладки сохраняем
    cv2.imwrite("debug_roi.png", roi)

    # OCR для извлечения текста
    result = reader.readtext(
        roi,
        detail=1,
        paragraph=False,
        contrast_ths=0.1,
        adjust_contrast=0.5,
        width_ths=0.5,
        height_ths=0.5,
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

    left_border = find_left_text_border(image_bgr, bottom, left, search_width=200)
    top_border = find_top_text_border(image_bgr, left_border, bottom) + 50

    roi_top = top_border
    roi_bottom = min(top_border + 130, image_bgr.shape[0])
    roi_left = left_border
    roi_right = min(left_border + 1000, image_bgr.shape[1])

    roi_coordinates = (roi_top, roi_right, roi_bottom, roi_left)
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
