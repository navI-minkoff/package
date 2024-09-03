import os

from utils import update_module


def getJpegFilenames(folder_path):
    all_files = os.listdir(folder_path)
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
