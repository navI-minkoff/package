from photoshop import Session
from utils.photoshop_utils import packagingSpreads, packingLists, packagingGroup, deleteUnwantedLayers, fillLayer
from utils.file_utils import getJpegFilenames, extractNumber
from utils.naming_utils import generatePrefixes

def packege():
    global jpeg_filenames, folder_path, group_jpeg_filenames, \
        folder_group_path, lists_jpeg_filenames, folder_lists_path, \
        groups_jpeg, individual_path_list, jpeg_filenames_individual_list

    source_psd_path = "C:/programms/undr/page.psd"
    image_teacher_path = "C:/undr/2024/Школа №18 9Г/макет/уч/1.jpg"
    output_path = "C:/undr/2024/Школа №18 9Г/res"

    try:
        folder_path = "C:/undr/2024/Школа №18 9Г/макет/развр1"
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
            {"folder_path": folder_group_path, "jpeg_filenames": group_jpeg_filenames, "postfix": "000", "design": "white"},
            {"folder_path": folder_group1_path, "jpeg_filenames": group1_jpeg_filenames, "postfix": "007", "design": "white"},
            {"folder_path": folder_group2_path, "jpeg_filenames": group2_jpeg_filenames, "postfix": "014", "design": "white"}
        ]

    except ValueError as e:
        print("Ошибка:", e)

    with Session(action="open", file_path=source_psd_path, auto_close=False) as ps:
        doc = ps.active_document

        jpeg_options = ps.JPEGSaveOptions()
        jpeg_options.quality = 12

        for layer in doc.layers:
            if layer.name == 'Пояснения' or layer.name == 'Разметка':
                layer.visible = False

        # packagingSpreads(ps, doc, jpeg_options, folder_path, jpeg_filenames, image_teacher_path, output_path, prefix="01")

        evenNumberPages = packingLists(ps, doc, jpeg_options, folder_lists_path, lists_jpeg_filenames, output_path, 2)

        for group in groups_jpeg:
            deleteUnwantedLayers(doc, ["Фон", "Разметка", "Пояснения"])
            fillLayer(ps, doc, "Фон", group["design"])
            packagingGroup(ps, doc, jpeg_options, group["folder_path"], group["jpeg_filenames"], output_path, folder_lists_path,
                           lists_jpeg_filenames, individual_path_list, jpeg_filenames_individual_list, evenNumberPages,
                           len(lists_jpeg_filenames) // 2 + 2, postfix=group["postfix"])

if __name__ == '__main__':
    packege()
