import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")
default_settings = {
    "file_path": "",
    "theme": "Dark",
    "close_psd": "True",
    "token": "",
    "covers_path": "",
    "excel_path": "",
    "surname_column": "",
    "cover_column": "",
    "header_row": 1
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            loaded_settings = json.load(f)
            # Добавляем недостающие ключи с значениями по умолчанию
            for key, value in default_settings.items():
                if key not in loaded_settings:
                    loaded_settings[key] = value
            return loaded_settings
    else:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_settings, f, indent=4)
        return default_settings


def save_settings(settings):
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)


