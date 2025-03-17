import chunk
import ctypes
import os
import shutil
import sys

import comtypes
from photoshop import Session

from utils import update_module
from utils.photoshop_utils import packagingSpreads, packingLists, packagingGroup, deleteUnwantedLayers, fillLayer, \
    packingLastListsWithGroupPages, layersCannotRemoved, paintLayer, shared_postfix
from utils.file_utils import getJpegFilenames, extractNumber, getNameByNumberSpreads, distributionByNumberReversals, \
    getFileWithDefiniteEnding
from utils.naming_utils import generatePrefixes


def package(reversals_folder_path, image_teacher_path,
            lists_jpeg, groups_jpeg, output_path, source_psd_path,
            album_version, album_design=None, auto_close=False):
    try:
        with Session(action="open", file_path=source_psd_path,
                     auto_close=True if auto_close == "True" else False) as ps:
            doc = ps.active_document
            jpeg_options = ps.JPEGSaveOptions()
            jpeg_options.quality = 12
            fillLayer(ps, doc, paintLayer, album_design)

            deleteUnwantedLayers(doc, layersCannotRemoved)
            for layer in doc.layers:
                if layer.name == 'Пояснения' or layer.name == 'Разметка':
                    layer.visible = False

            # packagingSpreads(ps, doc, jpeg_options, reversals_folder_path,
            #                  sorted(getJpegFilenames(reversals_folder_path), key=extractNumber),
            #                  image_teacher_path,
            #                  output_path)

            packingLists(ps, doc, jpeg_options, lists_jpeg[0]['lists_folder_path'],
                         lists_jpeg[0]['lists_jpeg_filenames'], output_path, 2)

            deleteUnwantedLayers(doc, layersCannotRemoved)
            packingLastListsWithGroupPages(ps, doc, jpeg_options,
                                           lists_jpeg, groups_jpeg, output_path,
                                           album_version)

            first_file_from_shared_lists = getFileWithDefiniteEnding(sorted(getJpegFilenames(f"{output_path}")),
                                                                     shared_postfix, True)
            last_file_from_shared_lists = getFileWithDefiniteEnding(sorted(getJpegFilenames(f"{output_path}")),
                                                                    shared_postfix, False)
            for group in groups_jpeg:
                deleteUnwantedLayers(doc, layersCannotRemoved)
                packagingGroup(ps, doc, jpeg_options, group["groups_jpeg"], group["group_jpeg_filenames"],
                               output_path,
                               len(lists_jpeg[0]['lists_jpeg_filenames']) // 2 + 3, postfix=group["postfix"],
                               album_version=album_version,
                               lists_is_even=len(lists_jpeg[0]["lists_jpeg_filenames"]) % 2 == 0)

            distributionByNumberReversals(output_path, first_file_from_shared_lists, last_file_from_shared_lists)
    except Exception as e:
        update_module.show_error_message(f"Ошибка: {e}")
        print(f"Error during packaging: {e}")
