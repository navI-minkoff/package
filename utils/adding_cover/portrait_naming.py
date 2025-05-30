import os
import cv2
import face_recognition
import easyocr
from utils.adding_cover.face_recognition_utils import preprocess_collages, get_face_encodings
from utils.adding_cover.ocr_utils import extract_surname_from_face, extract_surname_from_portrait, match_with_dictionary
from utils.config_utils import load_album_coordinates
from utils.file_utils import getJpegFilenames, extractNumber
from utils.photoshop_utils import designs_album, types_album


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


def find_surname_for_portrait_from_collage(portrait_path,
                                           collages_data,
                                           all_student_names,
                                           tolerance=0.6):
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
    # "Тевосян", "Лисица", "Фасаева", "Грехов",
    # "Фокин", "Абаимова", "Войт", "Ахунов",
    # "Деревянко", "Болотова", "Жуманазарова", "Дюрич",
    # "Плеханов", "Хдрян", "Акрамова", "Нечеухин",
    # "Зияева", "Акылбекова",
    # "Шуплецова",  #темный
    # "Павлушина",  #светлый прем
    # "Пучкин"      #светлый мини
    "Овакииян", "Самылкина", "Назарова", "Додов",
    "Курбаназаров", "Айдаралиева", "Капарбекова", "Яковенко",
    "Усубян", "Нозилова", "Рахимова", "Усубян",
    "Беляков", "Зулпуева", "Джомикова", "Култаев",
    "Усмонов", "Татоян", "Мамажанова", "Давлатов",
    "Эшмуратов", "Мамедова", "Мирзоев", "Чекиров",
]

# Пути к портретам и коллажам
# portrait_files_path = r'C:\programms\undr\package\utils\adding_cover\img\развр_мед'
# collage_files_path = r'C:\programms\undr\package\utils\adding_cover\img\сп_мед'
#
# print(get_portrait_name_pairs(portrait_files_path, collage_files_path, all_student_names,
#                               album_version=types_album[1],
#                               album_design=designs_album[0]))
