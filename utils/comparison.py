import os
import hashlib

# Пример использования:
folder1 = 'C:/undr/2024/Школа №18 9Г/печать/7 разворотов'
folder2 = 'C:/undr/2024/Школа №18 9Г/печать/test'


def calculate_file_hash(filepath, chunk_size=1024):
    """Вычисление хэша файла для его сравнения"""
    hash_obj = hashlib.md5()  # Используем MD5 для простоты
    with open(filepath, 'rb') as file:
        while chunk := file.read(chunk_size):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def compare_images_by_name(folder1, folder2):
    # Получаем списки файлов из обеих папок
    files1 = set(os.listdir(folder1))
    files2 = set(os.listdir(folder2))

    # Находим совпадающие по именам файлы
    common_files = files1.intersection(files2)

    identical_files = []
    different_files = []

    # Сравниваем файлы по содержимому
    for filename in common_files:
        file1_path = os.path.join(folder1, filename)
        file2_path = os.path.join(folder2, filename)

        # Сравниваем хэши файлов
        if calculate_file_hash(file1_path) == calculate_file_hash(file2_path):
            identical_files.append(filename)
        else:
            different_files.append(filename)

    return {
        'identical_files': identical_files,
        'different_files': different_files,
        'only_in_folder1': files1.difference(files2),
        'only_in_folder2': files2.difference(files1)
    }


result = compare_images_by_name(folder1, folder2)

print("Идентичные файлы:", result['identical_files'])
print("Отличающиеся файлы:", result['different_files'])
print("Только в первой папке:", result['only_in_folder1'])
print("Только во второй папке:", result['only_in_folder2'])
