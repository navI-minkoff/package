import os


def getJpegFilenames(folder_path):
    all_files = os.listdir(folder_path)
    jpeg_files = []
    for file in all_files:
        _, ext = os.path.splitext(file)
        if ext.lower() not in ['.jpg', '.jpeg']:
            raise ValueError(f"Файл {file} не является JPEG файлом")
        jpeg_files.append(file)
    return jpeg_files


def extractNumber(filename):
    return int(filename.split('.')[0])
