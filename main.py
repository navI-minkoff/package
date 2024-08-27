import os

from photoshop import Session

from utils.photoshop_utils import packagingSpreads, packingLists, packagingGroup, deleteUnwantedLayers, fillLayer, \
    packingLastListsWithGroupPages, layersCannotRemoved, paintLayer
from utils.file_utils import getJpegFilenames, extractNumber
from utils.naming_utils import generatePrefixes


# layersCannotRemoved = ["Фон", "Разметка", "Пояснения"]
# paintLayer = "Фон"


def package(reversals_folder_path, image_teacher_path,
            lists_jpeg, groups_jpeg, output_path, source_psd_path,
            album_version, album_design=None):
    # source_psd_path = "C:/programms/undr/page.psd"
    # output_path = "C:/undr/2024/Школа №18 9Г/res"

    # album_design = "dark"  # dark = album_design
    #
    # album_version = "med"  # min/prem = album_version

    # try:
    #
    #
    # lists_jpeg_filenames = sorted(getJpegFilenames(lists_jpeg), key=extractNumber)

    # individual_path_list = "C:/programms/undr/lists1/"
    # jpeg_filenames_individual_list = getJpegFilenames(individual_path_list)

    # group_jpeg_filenames = sorted(getJpegFilenames(groups_jpeg), key=extractNumber)

    # group1_jpeg_filenames = sorted(getJpegFilenames(folder_group1_path), key=extractNumber)
    #
    # group2_jpeg_filenames = sorted(getJpegFilenames(folder_group2_path), key=extractNumber)
    #
    #
    # except ValueError as e:
    #     print("Ошибка:", e)

    # groups_jpeg = [
    #     {"groups_jpeg": "C:/programms/undr/group",
    #      "group_jpeg_filenames": sorted(getJpegFilenames("C:/programms/undr/group"), key=extractNumber),
    #      "postfix": "000"}
    #     # {"groups_jpeg": "C:/programms/undr/group1",
    #     #  "group_jpeg_filenames": sorted(getJpegFilenames("C:/programms/undr/group1"), key=extractNumber), "postfix": "001"}
    # ]
    #
    # lists_jpeg = [
    #     {"lists_folder_path": "C:/programms/undr/lists",
    #      "lists_jpeg_filenames": sorted(getJpegFilenames("C:/programms/undr/lists"), key=extractNumber),
    #      "postfix": "000"}
    #     # {"groups_jpeg": "C:/programms/undr/lists1",
    #     #  "group_jpeg_filenames": sorted(getJpegFilenames("C:/programms/undr/lists1"), key=extractNumber), "postfix": "001"}
    #
    # ]
    # individual_group_folders = os.listdir("C:/programms/undr/group1")
    # for folder in individual_group_folders:
    #     path = "C:/programms/undr/group1" + f"/{folder}"
    #     groups_jpeg.append(
    #         {"groups_jpeg": path, "group_jpeg_filenames": sorted(getJpegFilenames(path), key=extractNumber),
    #          "postfix": folder.split(' ')[0].zfill(3)})
    #
    # individual_list_jpegs = os.listdir("C:/programms/undr/lists1")
    # for list_jpeg in individual_list_jpegs:
    #     path = "C:/programms/undr/lists1"
    #     lists_jpeg.append(
    #         {"lists_folder_path": path, "lists_jpeg_filenames": [list_jpeg],
    #          "postfix": list_jpeg.split(' ')[0].zfill(3)})

    with Session(action="open", file_path=source_psd_path, auto_close=False, ps_version="2022") as ps:
        doc = ps.active_document

        jpeg_options = ps.JPEGSaveOptions()
        jpeg_options.quality = 12

        for layer in doc.layers:
            if layer.name == 'Пояснения' or layer.name == 'Разметка':
                layer.visible = False

        packagingSpreads(ps, doc, jpeg_options, reversals_folder_path,
                         sorted(getJpegFilenames(reversals_folder_path), key=extractNumber),
                         image_teacher_path,
                         output_path)

        packingLists(ps, doc, jpeg_options, lists_jpeg[0]['lists_folder_path'],
                     lists_jpeg[0]['lists_jpeg_filenames'], output_path, 2)

        packingLastListsWithGroupPages(ps, doc, jpeg_options,
                                       lists_jpeg, groups_jpeg, output_path,
                                       album_version)
        for group in groups_jpeg:
            deleteUnwantedLayers(doc, layersCannotRemoved)
            fillLayer(ps, doc, paintLayer, album_design)
            packagingGroup(ps, doc, jpeg_options, group["groups_jpeg"], group["group_jpeg_filenames"],
                           output_path,
                           len(lists_jpeg[0]['lists_jpeg_filenames']) // 2 + 2, postfix=group["postfix"],
                           album_version="med", lists_is_even=len(lists_jpeg[0]["lists_jpeg_filenames"]) % 2 == 0)
