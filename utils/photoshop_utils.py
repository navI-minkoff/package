from utils.naming_utils import generateStrings, generatePrefixes


def fillLayer(ps, doc, layer_name, color):
    target_layer = None
    for layer in doc.artLayers:
        if layer.name == layer_name:
            target_layer = layer
            break

    if target_layer is None:
        raise ValueError(f"Layer '{layer_name}' not found")

    doc.activeLayer = target_layer
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


def placeAndResizeImage(ps, active_document, image_path, resize=False, edge='l'):
    desc = ps.ActionDescriptor
    desc.putPath(ps.app.charIDToTypeID("null"), image_path)
    event_id = ps.app.charIDToTypeID("Plc ")
    ps.app.executeAction(event_id, desc)
    placed_layer = active_document.activeLayer
    doc_width = active_document.width
    image_width = placed_layer.bounds[2] - placed_layer.bounds[0]
    if resize:
        scale = (doc_width / 2 - image_width) / image_width * 100 + 100
        placed_layer.resize(scale, scale)
        image_width = placed_layer.bounds[2] - placed_layer.bounds[0]
    if edge == 'l':
        new_x = -placed_layer.bounds[0] + doc_width / 2 - image_width
    else:
        new_x = -placed_layer.bounds[0] + doc_width / 2
    placed_layer.translate(new_x, 0)


def packagingSpreads(ps, active_document, jpeg_options, folder_path, jpeg_filenames, teacher_path, output_path, prefix):
    photo_names = generateStrings(prefix, 1, len(jpeg_filenames))
    placeAndResizeImage(ps, active_document, image_path=teacher_path, resize=True, edge='r')
    for i in range(len(jpeg_filenames)):
        placeAndResizeImage(ps, active_document, image_path=f"{folder_path}/{jpeg_filenames[i]}", resize=True)
        active_document.saveAs(f"{output_path}/{photo_names[i]}.jpg", jpeg_options, asCopy=True)


def packingLists(ps, active_document, jpeg_options, folder_path, jpeg_filenames, output_path, prefix):
    count_Jpeg = len(jpeg_filenames)
    if count_Jpeg % 2:
        count_Jpeg -= 1
    photo_names = generatePrefixes(prefix, count_Jpeg // 2)
    indexName = 0
    for i in range(0, count_Jpeg - 1, 2):
        placeAndResizeImage(ps, active_document, image_path=f"{folder_path}/{jpeg_filenames[i]}", resize=True, edge='l')
        placeAndResizeImage(ps, active_document, image_path=f"{folder_path}/{jpeg_filenames[i + 1]}", resize=True,
                            edge='r')
        active_document.saveAs(f"{output_path}/{photo_names[indexName]}.jpg", jpeg_options, asCopy=True)
        indexName += 1
    return not len(jpeg_filenames) % 2


def packagingGroup(ps, active_document, jpeg_options, folder_path, jpeg_filenames, output_path, folder_path_list,
                   jpeg_filenames_list, individual_path_list, jpeg_filenames_individual_list, even_pages, prefix,
                   postfix):
    count_Jpeg = len(jpeg_filenames)
    photo_names = generatePrefixes(prefix, count_Jpeg // 2 + (count_Jpeg % 2 != 0), postfix)
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
                                                image_path=f"{individual_path_list}/{jpeg_filename}", resize=True,
                                                edge='l')
                            placeAndResizeImage(ps, active_document,
                                                image_path=f"{folder_path}/{jpeg_filenames[indexPhoto]}", resize=False,
                                                edge='r')
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
                                                image_path=f"{folder_path_list}/{jpeg_filenames_list[-2]}", resize=True,
                                                edge='l')
                            placeAndResizeImage(ps, active_document,
                                                image_path=f"{individual_path_list}/{jpeg_filename}", resize=True,
                                                edge='r')
                            left_part, right_part = photo_names[indexPhoto].split('-')
                            left_part = str(int(left_part) - 1).zfill(len(left_part))
                            active_document.saveAs(f"{output_path}/{left_part}-{right_part}.jpg", jpeg_options,
                                                   asCopy=True)
    else:
        if not even_pages:
            if count_Jpeg % 2:
                placeAndResizeImage(ps, active_document, image_path=f"{folder_path_list}/{jpeg_filenames_list[-1]}",
                                    resize=True, edge='l')
                placeAndResizeImage(ps, active_document, image_path=f"{folder_path}/{jpeg_filenames[indexPhoto]}",
                                    resize=False, edge='r')
                active_document.saveAs(f"{output_path}/{photo_names[indexPhoto]}.jpg", jpeg_options, asCopy=True)
                indexPhoto += 1
                indexName += 1
            else:
                return
    deleteUnwantedLayers(active_document, ["Фон", "Разметка", "Пояснения"])
    for i in range(indexPhoto, count_Jpeg - 1, 2):
        placeAndResizeImage(ps, active_document, image_path=f"{folder_path}/{jpeg_filenames[i]}", resize=False,
                            edge='l')
        placeAndResizeImage(ps, active_document, image_path=f"{folder_path}/{jpeg_filenames[i + 1]}", resize=False,
                            edge='r')
        active_document.saveAs(f"{output_path}/{photo_names[indexName]}.jpg", jpeg_options, asCopy=True)
        indexName += 1
