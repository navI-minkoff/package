import os
import shutil

from utils import update_module
from utils.photoshop_utils import shared_postfix


def getJpegFilenames(folder_path):
    try:
        all_files = os.listdir(folder_path)
    except Exception as e:
        update_module.show_error_message(f"Файл {folder_path} указан неверно")
        print(f"Файл {folder_path} указан неверно: {e}")
    jpeg_files = []
    for file in all_files:
        _, ext = os.path.splitext(file)
        if ext.lower() not in ['.jpg', '.jpeg']:
            update_module.show_error_message(f"Файл {file} не является JPEG файлом")
            raise ValueError(f"Файл {file} не является JPEG файлом")
        jpeg_files.append(file)
    return jpeg_files


def getNameByNumberSpreads(count_spreads):
    name = 'разворот'
    count_spreads %= 10
    if count_spreads >= 2 and count_spreads <= 4:
        name += 'а'
    elif (count_spreads >= 5 and count_spreads <= 9) or count_spreads == 0:
        name += 'ов'

    return name


def extractNumber(filename):
    return int(filename.split('.')[0])


def renameFile(old_name, new_name):
    """
    Переименовывает файл old_name в новый new_name.

    :param old_name: Путь к исходному файлу
    :param new_name: Путь к новому файлу
    """
    try:
        os.rename(old_name, new_name)
    except FileNotFoundError:
        print(f"Файл {old_name} не найден.")
    except FileExistsError:
        print(f"Файл {new_name} уже существует.")
    except Exception as e:
        print(f"Ошибка при переименовании: {e}")


def moveAndCopyFiles(source_dir, destination_dir, files_to_copy=None, files_to_move=None):
    """
    Перемещает все файлы из исходной папки в целевую и копирует указанные файлы в ту же папку.

    :param source_dir: Путь к исходной папке
    :param destination_dir: Путь к целевой папке
    :param files_to_copy: Список файлов, которые нужно скопировать в целевую папку
    :param files_to_move: Список файлов, которые нужно перенести в целевую папку
    """

    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    if files_to_move:
        for filename in files_to_move:
            source_file = os.path.join(source_dir, filename)
            destination_file = os.path.join(destination_dir, filename)

            shutil.move(source_file, destination_file)

    if files_to_copy:
        for filename in files_to_copy:
            source_file = os.path.join(source_dir, filename)
            destination_file = os.path.join(destination_dir, f'{filename}')

            if os.path.exists(source_file):
                shutil.copy2(source_file, destination_file)
            else:
                print(f"Файл {filename} не найден в {destination_dir}")


def getFileWithDefiniteEnding(filenames, endswith, initially=True):
    if initially:
        return min(
            [f for f in filenames if f.endswith(f'{endswith}')],
            key=lambda x: int(x.split('-')[0]))
    else:
        return max(
            [f for f in filenames if f.endswith(f'{endswith}')],
            key=lambda x: int(x.split('-')[0]))


def distributionByNumberReversals(output_path, first_shared_list, last_shared_list):
    filenames = sorted(getJpegFilenames(f"{output_path}"))
    shared_lists = []
    for i in range(int(first_shared_list.split('-')[0]), int(last_shared_list.split('-')[0]) + 1):
        shared_lists.append(f'{i}'.zfill(2) + shared_postfix)
    shared_group = [i for i in filenames if i.endswith(f'{shared_postfix}') and i not in shared_lists]

    individual_postfix = set()
    for i in range(filenames.index(last_shared_list), len(filenames)):
        file = filenames[i].split('-')[1]
        if file not in individual_postfix and file != last_shared_list.split('-')[1]:
            individual_postfix.add(filenames[i].split('-')[1])

    shared_titles = [i for i in filenames if (i.split('-')[0] == '01' or i.split('-')[0] == '00') and i.split('-')[1] not in individual_postfix]

    for i in individual_postfix:
        files_for_move = [f for f in filenames if f.split('-')[1] == i]
        number_last_reversal = int(getFileWithDefiniteEnding(filenames, i, False).split('-')[0])
        moveAndCopyFiles(output_path,
                         output_path + '/' + f'{number_last_reversal} ' + getNameByNumberSpreads(number_last_reversal),
                         files_to_copy=shared_lists,
                         files_to_move=files_for_move)

    number_last_reversal = int(getFileWithDefiniteEnding(filenames, shared_postfix, False).split('-')[0])
    moveAndCopyFiles(output_path,
                     output_path + '/' + f'{number_last_reversal} ' + getNameByNumberSpreads(number_last_reversal),
                     files_to_move=shared_titles + shared_lists + shared_group)

    reversals_folders = [f for f in os.listdir(output_path) if not 'jpg' in f]
    for folder in reversals_folders:
        namingInOrder(output_path + '/' + folder)
        checkingForExtraPages(output_path + '/' + folder, shared_lists[-1])


def checkingForExtraPages(source_dir: str, name_last_general_spread: str):
    """
    Удаляет последний общий разворот, если он был лишний.
    :param source_dir: Путь к исходной папке
    :param name_last_general_spread: Название последнего общего разворота
    """
    all_filenames = getJpegFilenames(source_dir)
    title_pages = [f for f in all_filenames if f.split('-')[0] == '01']
    files_with_reversal_prefix = [f for f in all_filenames if f.split('-')[0] == name_last_general_spread.split('-')[0]]
    if len(files_with_reversal_prefix) > len(title_pages):
        os.remove(source_dir + '/' + name_last_general_spread)


def namingInOrder(source_dir):
    """
        Переименовывает файлы, чтобы они шли по порядку(01-001, 01-002, ...).
        :param source_dir: Путь к исходной папке
    """
    filenames = getJpegFilenames(source_dir)
    reversals = [i for i in filenames if i.split('-')[0] == '01']

    renameIndex = len(reversals) - 1
    readIndex = 0
    nameIndex = 0
    while readIndex <= renameIndex:
        if int(reversals[readIndex].split('-')[1].split('.')[0]) != nameIndex + 1:
            files_for_rename = [f for f in filenames if f.split('-')[1] == reversals[renameIndex].split('-')[1]]
            for file in files_for_rename:
                renameFile(source_dir + '/' + file,
                           source_dir + '/' + file.split('-')[0].zfill(2) + f'-{str(nameIndex + 1).zfill(3)}.jpg')
            renameIndex -= 1
        else:
            readIndex += 1
        nameIndex += 1
