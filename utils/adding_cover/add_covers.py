import os
import shutil

from utils.settings_utils import load_settings
from utils.adding_cover.portrait_naming import get_portrait_name_pairs
from utils.adding_cover.read_excel_columns import read_excel_columns_to_map
from utils.adding_cover.read_excel_columns import get_surnames_and_covers_from_table
from utils.photoshop_utils import types_album, designs_album


def map_surnames_to_covers(excel_file_path, portrait_files_path, collage_files_path,
                           header_row, col1_name, col2_name,
                           type_album, design_album):
    """
    Сопоставляет фамилии из таблицы с индексами портретов и номерами обложек.

    Args:
        excel_file_path (str): Путь к Excel-файлу с таблицей.
        portrait_files_path (str): Путь к папке с портретами.
        collage_files_path (str): Путь к папке с коллажами.
        header_row (int): Номер строки заголовка в таблице.
        col1_name (str): Название столбца с фамилиями.
        col2_name (str): Название столбца с номерами обложек.

    Returns:
        dict: Словарь, где ключи - фамилии, значения - кортежи (индекс портрета, номер обложки).
    """
    data = get_surnames_and_covers_from_table(excel_file_path, header_row, col1_name, col2_name)

    all_student_names = list(data.keys())

    portrait_name_pairs = get_portrait_name_pairs(portrait_files_path, collage_files_path, all_student_names,
                                                  type_album, design_album)

    result = {}

    for surname, portrait_index in portrait_name_pairs:
        if surname in data:
            cover_number = data[surname]
            result[surname] = (portrait_index, cover_number)
        else:
            print(f"Фамилия {surname} не найдена в таблице")

    return result


def copy_and_rename_covers(surname_to_index_cover, covers_folder_path, output_path):
    """
    Копирует обложки из указанной папки в итоговую папку, переименовывая их на основе индексов.

    Args:
        surname_to_index_cover (dict): Словарь, где ключи - фамилии, значения - кортежи (индекс портрета, номер обложки).
        covers_folder_path (str): Путь к папке с обложками.
        output_path (str): Путь к итоговой папке для сохранения переименованных обложек.

    Returns:
        None
    """
    os.makedirs(output_path, exist_ok=True)

    cover_files = [f for f in os.listdir(covers_folder_path) if f.lower().endswith(('.jpg', '.jpeg'))]

    for surname, (portrait_index, cover_number) in surname_to_index_cover.items():
        output_filename = f"00-{str(portrait_index + 1).zfill(3)}.jpg"

        source_filename = f"{cover_number}.jpg"

        if source_filename in cover_files:
            source_file_path = os.path.join(covers_folder_path, source_filename)
            destination_file_path = os.path.join(output_path, output_filename)

            try:
                shutil.copy2(source_file_path, destination_file_path)
                print(f"Скопирована обложка для {surname}: {source_filename} -> {output_filename}")
            except FileNotFoundError:
                print(f"Файл {source_filename} не найден в {covers_folder_path}")
            except Exception as e:
                print(f"Ошибка при копировании {source_filename} для {surname}: {e}")
        else:
            print(f"Обложка {source_filename} для {surname} не найдена в {covers_folder_path}")


def adding_covers_based_on_portrait(portrait_files_path, collage_files_path, output_path,
                                    type_album, design_album):
    settings = load_settings()
    # excel
    file_path = settings.get("excel_path")  # Путь к Excel
    header_row = settings.get("header_row")  # Номер строки с заголовками
    col1_name = settings.get("surname_column")  # Название колонки с фамилией
    col2_name = settings.get("cover_column")  # Название колонки с номером обложки
    covers_folder_path = settings.get("covers_path")

    # Пути к папкам
    # output_path = r"C:\programms\undr\package\utils\adding_cover\img\обложки"

    # Пути к портретам и коллажам
    # portrait_files_path = r'C:\programms\undr\package\utils\adding_cover\img\развр_мед'
    # collage_files_path = r'C:\programms\undr\package\utils\adding_cover\img\сп_мед'
    surname_to_index_cover = map_surnames_to_covers(file_path, portrait_files_path, collage_files_path,
                                                    header_row, col1_name, col2_name,
                                                    type_album, design_album)

    copy_and_rename_covers(surname_to_index_cover, covers_folder_path, output_path)

#
# if __name__ == "__main__":
#     adding_covers_based_on_portrait()

