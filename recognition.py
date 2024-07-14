import cv2
import numpy as np

import cv2
from PIL import Image
import numpy as np


def split_and_crop(image_path, cropped_output_path):
    # Загрузка изображения
    image = cv2.imread(image_path)

    # Разделение изображения на левую и правую части
    height, width = image.shape[:2]
    mid_width = width // 2

    left_half = image[:, :mid_width]

    # Сохранение левой части
    cv2.imwrite(cropped_output_path, left_half)

    # # Преобразование левой части в градации серого
    # gray = cv2.cvtColor(left_half, cv2.COLOR_BGR2GRAY)
    #
    # # Бинаризация изображения (пороговая обработка)
    # _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    #
    # # Инверсия бинарного изображения
    # inverted_binary = cv2.bitwise_not(binary)
    #
    # # Поиск контуров на бинарном изображении
    # contours, _ = cv2.findContours(inverted_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #
    # # Нахождение ограничивающего прямоугольника для всех контуров
    # x, y, w, h = cv2.boundingRect(contours[0])
    #
    # # Обрезка изображения по ограничивающему прямоугольнику
    # cropped_image = left_half[y:y + h, x:x + w]
    #
    # # Сохранение обрезанного изображения
    # cv2.imwrite(cropped_output_path, cropped_image)


def resize_image(input_image_path, output_image_path, new_width, new_height):
    # Открываем изображение
    original_image = Image.open(input_image_path)

    # Изменяем размер изображения
    resized_image = original_image.resize((new_width, new_height), Image.LANCZOS)

    # Сохраняем измененное изображение
    resized_image.save(output_image_path)


def cropping_image(input_image_path, new_width, new_height):
    image = Image.open(input_image_path)

    width, height = image.size
    if new_width > width or new_height > height:
        return

    left = (width - new_width) / 2
    right = width - left
    top = (height - new_height) / 2
    bottom = height - top

    # Обрезаем изображение
    cropped_image = image.crop((left, top, right, bottom))

    # Сохраняем обрезанное изображение
    cropped_image.save(input_image_path)


def resize_image_by_factor(input_image_path, output_image_path, factor):
    # Открываем изображение
    img = Image.open(input_image_path)

    # Получаем текущие размеры изображения
    original_width, original_height = img.size

    # Вычисляем новые размеры
    new_width = int(original_width / factor)
    new_height = int(original_height / factor)

    # Изменяем размер изображения
    resized_img = img.resize((new_width, new_height), Image.LANCZOS)

    # Сохраняем уменьшенное изображение
    resized_img.save(output_image_path)


def find_template_in_image(image_path, template_path, output_image_path):
    # Загружаем основное изображение и шаблонное изображение
    image = cv2.imread(image_path)
    template = cv2.imread(template_path)

    # Получаем размеры шаблона
    template_height, template_width = template.shape[:2]

    # Применяем метод поиска шаблона
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)

    # Устанавливаем пороговое значение для обнаружения
    threshold = 0.75
    loc = np.where(result >= threshold)

    # Копируем изображение для отображения результатов
    output_image = template.copy()

    # Проверяем, найдены ли совпадения
    if len(loc[0]) == 0:
        print("Шаблон не найден на изображении.")
    else:
        # Рисуем прямоугольники вокруг найденных шаблонов
        for pt in zip(*loc[::-1]):
            cv2.rectangle(output_image, pt, (pt[0] + template_width, pt[1] + template_height), (0, 0, 255), 2)

    # Сохраняем изображение с нарисованными прямоугольниками
    cv2.imwrite(output_image_path, output_image)


input_image = "C:/programms/undr/recognition/01-015.jpg"
left_half = "C:/programms/undr/recognition/1.jpg"
output_image = "C:/programms/undr/recognition/1.jpg"
find_image = "C:/programms/undr/recognition/007.jpg"
list_image = "C:/programms/undr/recognition/02-000.jpg"

new_width = 1130
new_height = 1450

split_and_crop(input_image, output_image)

cropping_image(output_image, 2300, 2950)

resize_image_by_factor(output_image, output_image, 2.0353) #2.0353

cropping_image(output_image, 500, 500)

find_template_in_image(output_image, list_image, find_image)