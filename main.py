from photoshop import Session

from utils.photoshop_utils import packagingSpreads, packingLists, packagingGroup, deleteUnwantedLayers, fillLayer, \
    packingLastListsWithGroupPages
from utils.file_utils import getJpegFilenames, extractNumber
from utils.naming_utils import generatePrefixes

layersCannotRemoved = ["Фон", "Разметка", "Пояснения"]
paintLayer = "Фон"


def package(folder_path, folder_group_path, image_teacher_path,
            folder_lists_path, individual_path_list=None):
    global jpeg_filenames_individual_list, groups_jpeg, group_jpeg_filenames, jpeg_filenames, lists_jpeg_filenames
    source_psd_path = "C:/programms/undr/page.psd"
    output_path = "C:/undr/2024/Школа №18 9Г/res"

    groups_jpeg = []
    lists_jpeg = []
    design = "light"  # dark

    album_version = "med" # min/prem

    try:
        jpeg_filenames = sorted(getJpegFilenames(folder_path), key=extractNumber)

        lists_jpeg_filenames = sorted(getJpegFilenames(folder_lists_path), key=extractNumber)

        # individual_path_list = "C:/programms/undr/lists1/"
        # jpeg_filenames_individual_list = getJpegFilenames(individual_path_list)

        group_jpeg_filenames = sorted(getJpegFilenames(folder_group_path), key=extractNumber)

        # group1_jpeg_filenames = sorted(getJpegFilenames(folder_group1_path), key=extractNumber)
        #
        # group2_jpeg_filenames = sorted(getJpegFilenames(folder_group2_path), key=extractNumber)


    except ValueError as e:
        print("Ошибка:", e)


    groups_jpeg = [
        {"folder_path": folder_group_path, "jpeg_filenames": group_jpeg_filenames, "postfix": "000"}
    ]

    lists_jpeg = [
        {"folder_path": folder_group_path, "jpeg_filenames": group_jpeg_filenames, "postfix": "000"}
    ]

    groups_jpeg = [
        {"folder_path": "C:/programms/undr/group", "jpeg_filenames": sorted(getJpegFilenames("C:/programms/undr/group"), key=extractNumber), "postfix": "000"},
        {"folder_path": "C:/programms/undr/group1",
         "jpeg_filenames": sorted(getJpegFilenames("C:/programms/undr/group1"), key=extractNumber), "postfix": "001"}
    ]

    lists_jpeg = [
        {"folder_path": "C:/programms/undr/lists", "jpeg_filenames": sorted(getJpegFilenames("C:/programms/undr/lists"), key=extractNumber), "postfix": "000"},
        {"folder_path": "C:/programms/undr/lists1",
         "jpeg_filenames": sorted(getJpegFilenames("C:/programms/undr/lists1"), key=extractNumber), "postfix": "001"}

    ]
    with Session(action="open", file_path=source_psd_path, auto_close=False, ps_version="2022") as ps:
        doc = ps.active_document

        jpeg_options = ps.JPEGSaveOptions()
        jpeg_options.quality = 12

        for layer in doc.layers:
            if layer.name == 'Пояснения' or layer.name == 'Разметка':
                layer.visible = False

        packagingSpreads(ps, doc, jpeg_options, folder_path,
                         jpeg_filenames, image_teacher_path, output_path)

        packingLists(ps, doc, jpeg_options, folder_lists_path,
                                       lists_jpeg_filenames, output_path, 2)

        packingLastListsWithGroupPages(ps, doc, jpeg_options,
                                       lists_jpeg, groups_jpeg, output_path)
        for group in groups_jpeg:
            deleteUnwantedLayers(doc, layersCannotRemoved)
            fillLayer(ps, doc, paintLayer, design)
            packagingGroup(ps, doc, jpeg_options, folder_group_path, group["jpeg_filenames"], output_path,
                           folder_lists_path,
                           lists_jpeg_filenames, individual_path_list, jpeg_filenames_individual_list,
                           len(lists_jpeg_filenames) // 2 + 2, postfix=group["postfix"])
