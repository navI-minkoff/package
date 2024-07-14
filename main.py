from photoshop import Session
import os


def generateStrings(prefix: str, start: int, end: int) -> list:
    result = []
    for i in range(start, end + 1):
        # Форматирование строки с заполнением нулями
        formatted_number = f"{prefix}-{i:03}"
        result.append(formatted_number)

    return result


# Функция для извлечения числовой части из имени файла
def extractNumber(filename):
    return int(filename.split('.')[0])


def generatePrefixes(start: int, prefix_count: int, postfix: str = '000') -> list:
    postfix.zfill(3)
    prefixes = []
    for i in range(start, start + prefix_count):
        formatted_prefix = f"{i:02}-" + postfix
        prefixes.append(formatted_prefix)
    return prefixes


def fillLayer(ps, doc, layer_name, color):
    # Находим слой с заданным названием
    target_layer = None
    for layer in doc.artLayers:
        if layer.name == layer_name:
            target_layer = layer
            break

    if target_layer is None:
        raise ValueError(f"Layer '{layer_name}' not found")

    # Делаем слой активным
    doc.activeLayer = target_layer
    # Заливаем слой цветом
    fill_color = ps.SolidColor()
    if color.lower() == 'dark':
        fill_color.rgb.red = 0
        fill_color.rgb.green = 0
        fill_color.rgb.blue = 0
    elif color.lower() == 'white':
        fill_color.rgb.red = 255
        fill_color.rgb.green = 255
        fill_color.rgb.blue = 255
    else:
        raise ValueError("Color must be 'black' or 'white'")

    # Выполняем заливку
    doc.selection.selectAll()
    doc.selection.fill(fill_color)
    doc.selection.deselect()


def deleteUnwantedLayers(doc, keep_layers):
    def process_layers(layers):
        layers_to_delete = []
        for layer in layers:
            if layer.name not in keep_layers:
                layers_to_delete.append(layer)
        for layer in layers_to_delete:
            layer.remove()

    # Получаем все слои в документе, включая слои в группах
    def get_all_layers(layer_set):
        layers = []
        for layer in layer_set:
            if layer.typename == "ArtLayer":
                layers.append(layer)
            elif layer.typename == "LayerSet":
                layers.extend(get_all_layers(layer.layers))
        return layers

    all_layers = get_all_layers(doc.layers)
    process_layers(all_layers)


def placeAndResizeImage(ps: Session, active_document, image_path: str, resize=False, edge='l') -> None:
    # Вставка изображения как смарт-объекта
    desc = ps.ActionDescriptor
    desc.putPath(ps.app.charIDToTypeID("null"), image_path)

    # Выполнение действия Place (вставить изображение)
    event_id = ps.app.charIDToTypeID("Plc ")
    ps.app.executeAction(event_id, desc)

    # Получение вставленного слоя
    placed_layer = active_document.activeLayer

    # Определение размеров документа
    doc_width = active_document.width

    # Определение размеров изображения
    image_width = placed_layer.bounds[2] - placed_layer.bounds[0]
    if resize:
        # Вычисление масштаба для подгонки высоты изображения к высоте документа
        scale = (doc_width / 2 - image_width) / image_width * 100 + 100
        placed_layer.resize(scale, scale)
        image_width = placed_layer.bounds[2] - placed_layer.bounds[0]

    if edge == 'l':
        new_x = -placed_layer.bounds[0] + doc_width / 2 - image_width
    else:
        new_x = -placed_layer.bounds[0] + doc_width / 2
    # Перемещение слоя
    placed_layer.translate(new_x, 0)


def getJpegFilenames(folder_path: str) -> list:
    # Получение всех файлов в папке
    all_files = os.listdir(folder_path)

    # Список для хранения имен JPEG файлов
    jpeg_files = []

    for file in all_files:
        # Получение расширения файла
        _, ext = os.path.splitext(file)

        # Проверка, что расширение является .jpg или .jpeg
        if ext.lower() not in ['.jpg', '.jpeg']:
            raise ValueError(f"Файл {file} не является JPEG файлом")

        # Добавление файла в список JPEG файлов
        jpeg_files.append(file)

    return jpeg_files


def packagingSpreads(ps: Session, active_document, jpeg_options, folder_path: str, jpeg_filenames: list[str],
                     teacher_path: str, output_path: str,
                     prefix: str = " ") -> None:
    # Генерация имен файлов
    photo_names = generateStrings(prefix, 1, len(jpeg_filenames))

    # Первоначальная вставка и изменение размера изображения
    placeAndResizeImage(ps, active_document, image_path=teacher_path, resize=True, edge='r')

    for i in range(len(jpeg_filenames)):
        placeAndResizeImage(ps, active_document, image_path=f"{folder_path}/{jpeg_filenames[i]}", resize=True)

        # Сохранение документа в JPEG
        active_document.saveAs(f"{output_path}/{photo_names[i]}.jpg", jpeg_options, asCopy=True)


def packingLists(ps: Session, active_document, jpeg_options,
                 folder_path: str, jpeg_filenames: list[str], output_path: str,
                 prefix: int = 2) -> bool:
    count_Jpeg = len(jpeg_filenames)
    if count_Jpeg % 2:
        count_Jpeg -= 1

    # Генерация имен файлов
    photo_names = generatePrefixes(prefix, count_Jpeg // 2)

    indexName = 0
    for i in range(0, count_Jpeg - 1, 2):
        placeAndResizeImage(ps, active_document, image_path=f"{folder_path}/{jpeg_filenames[i]}", resize=True, edge='l')
        placeAndResizeImage(ps, active_document, image_path=f"{folder_path}/{jpeg_filenames[i + 1]}", resize=True,
                            edge='r')

        # Сохранение документа в JPEG
        active_document.saveAs(f"{output_path}/{photo_names[indexName]}.jpg", jpeg_options, asCopy=True)
        indexName += 1
    return not len(jpeg_filenames) % 2


def packagingGroup(ps: Session, active_document, jpeg_options,
                   folder_path: str, jpeg_filenames: list[str], output_path: str,
                   folder_path_list: str, jpeg_filenames_list: list[str],
                   individual_path_list: str, jpeg_filenames_individual_list: list[str],
                   even_pages: bool, prefix: int, postfix: str = "000") -> None:
    count_Jpeg = len(jpeg_filenames)
    photo_names = generatePrefixes(prefix, count_Jpeg // 2 + 1, postfix)
    indexPhoto = 0
    indexName = 0

    if postfix != "000" and individual_path_list and any(
            postfix.lstrip('0') in filename for filename in jpeg_filenames_individual_list):
        if not even_pages:
            if count_Jpeg % 2:
                for jpeg_filename in jpeg_filenames_individual_list:
                    filename = jpeg_filename.split('.')[0]
                    for name in filename.split(' '):
                        if postfix.lstrip('0') == name:
                            placeAndResizeImage(ps, active_document,
                                                image_path=f"{individual_path_list}/{jpeg_filename}",
                                                resize=True,
                                                edge='l')
                            placeAndResizeImage(ps, active_document,
                                                image_path=f"{folder_path}/{jpeg_filenames[indexPhoto]}",
                                                resize=False, edge='r')
                            # Сохранение документа в JPEG
                            active_document.saveAs(f"{output_path}/{photo_names[indexPhoto]}.jpg", jpeg_options,
                                                   asCopy=True)

                            indexPhoto += 1
                            indexName += 1
            else:
                return
        else:
            for jpeg_filename in jpeg_filenames_individual_list:
                filename = jpeg_filename.split('.')
                for name in filename:
                    for index in name.split(' '):
                        if postfix.lstrip('0') == index:
                            placeAndResizeImage(ps, active_document,
                                                image_path=f"{folder_path_list}/{jpeg_filenames_list[-2]}",
                                                resize=True,
                                                edge='l')
                            placeAndResizeImage(ps, active_document,
                                                image_path=f"{individual_path_list}/{jpeg_filename}",
                                                resize=True, edge='r')

                            left_part, right_part = photo_names[indexPhoto].split('-')
                            # Преобразуем левую часть в целое число, уменьшаем на 1 и приводим обратно к строке
                            left_part = str(int(left_part) - 1).zfill(len(left_part))

                            # Сохранение документа в JPEG
                            active_document.saveAs(f"{output_path}/{left_part}-{right_part}.jpg", jpeg_options,
                                                   asCopy=True)

    else:
        if not even_pages:
            if count_Jpeg % 2:
                placeAndResizeImage(ps, active_document, image_path=f"{folder_path_list}/{jpeg_filenames_list[-1]}",
                                    resize=True,
                                    edge='l')
                placeAndResizeImage(ps, active_document, image_path=f"{folder_path}/{jpeg_filenames[indexPhoto]}",
                                    resize=False, edge='r')
                # Сохранение документа в JPEG
                active_document.saveAs(f"{output_path}/{photo_names[indexPhoto]}.jpg", jpeg_options, asCopy=True)

                indexPhoto += 1
                indexName += 1
            else:
                return

    deleteUnwantedLayers(active_document, ["Фон", "Разметка", "Пояснения"])
    # Генерация имен файлов
    for i in range(indexPhoto, count_Jpeg - 1, 2):
        placeAndResizeImage(ps, active_document, image_path=f"{folder_path}/{jpeg_filenames[i]}", resize=False,
                            edge='l')
        placeAndResizeImage(ps, active_document, image_path=f"{folder_path}/{jpeg_filenames[i + 1]}", resize=False,
                            edge='r')

        # Сохранение документа в JPEG
        active_document.saveAs(f"{output_path}/{photo_names[indexName]}.jpg", jpeg_options, asCopy=True)
        indexName += 1


def packege():
    # Путь к исходному файлу и картинке для добавления

    global jpeg_filenames, folder_path, group_jpeg_filenames, \
        folder_group_path, lists_jpeg_filenames, folder_lists_path, \
        groups_jpeg, individual_path_list, jpeg_filenames_individual_list

    source_psd_path = "C:/programms/undr/page.psd"
    image_teacher_path = "C:/undr/2024/Школа №18 9Г/макет/уч/1.jpg"
    output_path = "C:/undr/2024/Школа №18 9Г/печать"

    try:
        folder_path = "C:/undr/2024/Школа №18 9Г/макет/развр"
        jpeg_filenames = sorted(getJpegFilenames(folder_path), key=extractNumber)

        folder_lists_path = "C:/undr/2024/Школа №18 9Г/макет/сп"
        lists_jpeg_filenames = sorted(getJpegFilenames(folder_lists_path), key=extractNumber)

        individual_path_list = "C:/programms/undr/lists1/"
        jpeg_filenames_individual_list = getJpegFilenames(individual_path_list)

        folder_group_path = "C:/undr/2024/Школа №18 9Г/макет/гр/oбщ"
        group_jpeg_filenames = sorted(getJpegFilenames(folder_group_path), key=extractNumber)

        folder_group1_path = "C:/undr/2024/Школа №18 9Г/макет/гр/калинкина"
        group1_jpeg_filenames = sorted(getJpegFilenames(folder_group1_path), key=extractNumber)

        folder_group2_path = "C:/undr/2024/Школа №18 9Г/макет/гр/куликовских"
        group2_jpeg_filenames = sorted(getJpegFilenames(folder_group2_path), key=extractNumber)
        groups_jpeg = [
            {"folder_path": folder_group_path, "jpeg_filenames": group_jpeg_filenames, "postfix": "000",
             "design": "white"},
            {"folder_path": folder_group1_path, "jpeg_filenames": group1_jpeg_filenames, "postfix": "007",
             "design": "white"},
            {"folder_path": folder_group2_path, "jpeg_filenames": group2_jpeg_filenames, "postfix": "014",
             "design": "white"}
        ]

    except ValueError as e:
        print("Ошибка:", e)

    # Начало сессии Photoshop
    with Session(action="open", file_path=source_psd_path, auto_close=False) as ps:
        doc = ps.active_document

        # Настройки для сохранения в JPEG
        jpeg_options = ps.JPEGSaveOptions()
        jpeg_options.quality = 12  # JPEG (1-12)

        for layer in doc.layers:
            if layer.name == 'Пояснения' or layer.name == 'Разметка':
                layer.visible = False

        packagingSpreads(ps, doc, jpeg_options, folder_path,
                         jpeg_filenames, image_teacher_path, output_path, prefix="01")

        evenNumberPages = packingLists(ps, doc, jpeg_options, folder_lists_path,
                                       lists_jpeg_filenames, output_path, 2)

        for group in groups_jpeg:
            deleteUnwantedLayers(doc, ["Фон", "Разметка", "Пояснения"])
            fillLayer(ps, doc, "Фон", group["design"])
            packagingGroup(ps, doc, jpeg_options, group["folder_path"],
                           group["jpeg_filenames"], output_path, folder_lists_path, lists_jpeg_filenames,
                           individual_path_list, jpeg_filenames_individual_list,
                           evenNumberPages, len(group["jpeg_filenames"]) // 2 + 1,
                           postfix=group["postfix"])


if __name__ == '__main__':
    packege()
