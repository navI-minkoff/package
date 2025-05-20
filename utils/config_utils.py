import json
import os

def load_album_coordinates():
    """
    Загружает координаты альбомов из settings.json.

    Returns:
        dict: Словарь с координатами или значения по умолчанию, если файл отсутствует/некорректен.
    """
    settings_file = os.path.join(os.path.dirname(__file__), r".\settings.json")
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