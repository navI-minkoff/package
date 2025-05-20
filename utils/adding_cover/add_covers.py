import os
import shutil

from utils.adding_cover.portrait_naming import get_portrait_name_pairs
from utils.adding_cover.read_excel_columns import read_excel_columns_to_map
from utils.adding_cover.read_excel_columns import get_surnames_and_covers_from_table
from utils.photoshop_utils import types_album, designs_album


def map_surnames_to_covers(excel_file_path, portrait_files_path, collage_files_path, header_row, col1_name, col2_name):
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
    # Получаем данные из таблицы (фамилии и номера обложек)
    data = get_surnames_and_covers_from_table(excel_file_path, header_row, col1_name, col2_name)

    # Извлекаем только фамилии
    all_student_names = list(data.keys())

    # Получаем пары (фамилия, индекс портрета) с помощью get_portrait_name_pairs
    portrait_name_pairs = get_portrait_name_pairs(portrait_files_path, collage_files_path, all_student_names,
                                                  types_album[1], designs_album[0])

    # Создаем результирующий словарь для сопоставления фамилий, индексов и обложек
    result = {}

    # Для каждой пары (фамилия, индекс) из get_portrait_name_pairs
    for surname, portrait_index in portrait_name_pairs:
        if surname in data:
            # Сопоставляем фамилию с индексом портрета и номером обложки из таблицы
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
    # Создаем итоговую папку, если она не существует
    os.makedirs(output_path, exist_ok=True)

    # Получаем список файлов обложек
    cover_files = [f for f in os.listdir(covers_folder_path) if f.lower().endswith(('.jpg', '.jpeg'))]

    for surname, (portrait_index, cover_number) in surname_to_index_cover.items():
        # Формируем имя выходного файла в формате 00-XXX.jpg
        output_filename = f"00-{str(portrait_index + 1).zfill(3)}.jpg"

        # Формируем имя исходного файла обложки (предполагается, что имя файла совпадает с номером обложки)
        source_filename = f"{cover_number}.jpg"  # Предполагаем, что файлы названы по номеру обложки

        # Проверяем, существует ли файл обложки
        if source_filename in cover_files:
            source_file_path = os.path.join(covers_folder_path, source_filename)
            destination_file_path = os.path.join(output_path, output_filename)

            try:
                # Копируем файл в итоговую папку
                shutil.copy2(source_file_path, destination_file_path)
                print(f"Скопирована обложка для {surname}: {source_filename} -> {output_filename}")
            except FileNotFoundError:
                print(f"Файл {source_filename} не найден в {covers_folder_path}")
            except Exception as e:
                print(f"Ошибка при копировании {source_filename} для {surname}: {e}")
        else:
            print(f"Обложка {source_filename} для {surname} не найдена в {covers_folder_path}")


def adding_covers_based_on_portrait():
    # excel
    file_path = r"C:\programms\undr\класс.xlsx"
    header_row = 1
    col1_name = "Фамилия Имя"
    col2_name = "Номер обложки"

    # Пути к папкам
    covers_folder_path = r"C:\undr\!ПРОГИ\Обложки"
    output_path = r"C:\programms\undr\package\utils\adding_cover\img\обложки"

    # Пути к портретам и коллажам
    portrait_files_path = r'C:\programms\undr\package\utils\adding_cover\img\развр_мед'
    collage_files_path = r'C:\programms\undr\package\utils\adding_cover\img\сп_мед'
    surname_to_index_cover = map_surnames_to_covers(file_path, portrait_files_path, collage_files_path,
                                                    header_row, col1_name, col2_name)


    # Вызов функции
    copy_and_rename_covers(surname_to_index_cover, covers_folder_path, output_path)


# Пример использования
if __name__ == "__main__":
    adding_covers_based_on_portrait()

