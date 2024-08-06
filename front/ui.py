import ctypes
import os
import sys
import threading
import time
from functools import partial

import flet as ft

from main import package
from utils.file_utils import getJpegFilenames, extractNumber


def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)


def front_main(page: ft.Page):
    page.title = "undr"
    page.theme_mode = "dark"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def _package():
        lists_jpeg = [
            {"lists_folder_path": selected_path_lists.value,
             "lists_jpeg_filenames": sorted(getJpegFilenames(selected_path_lists.value), key=extractNumber),
             "postfix": "000"}]

        individual_list_jpegs = os.listdir(selected_path_individual_lists.value)
        for list_jpeg in individual_list_jpegs:
            lists_jpeg.append(
                {"lists_folder_path": selected_path_individual_lists.value,
                 "lists_jpeg_filenames": [list_jpeg],
                 "postfix": list_jpeg.split(' ')[0].zfill(3)})

        groups_jpeg = [
            {"groups_jpeg": selected_path_group.value,
             "group_jpeg_filenames": sorted(getJpegFilenames(selected_path_group.value), key=extractNumber),
             "postfix": "000"}]

        individual_group_folders = os.listdir(selected_path_individual_group.value)
        for folder in individual_group_folders:
            path = selected_path_individual_group.value + f"/{folder}"
            groups_jpeg.append(
                {"groups_jpeg": path, "group_jpeg_filenames": sorted(getJpegFilenames(path), key=extractNumber),
                 "postfix": folder.split(' ')[0].zfill(3)})

        all_group_pages = 0
        for group in groups_jpeg:
            all_group_pages += len(group['group_jpeg_filenames']) / 2

        total_pages = len(os.listdir(selected_path_reversals.value)) + \
                      len(lists_jpeg[0]['lists_jpeg_filenames']) / 2 + \
                      len(lists_jpeg) - 1 + \
                      all_group_pages

        run_as_admin()
        start_monitoring(output_path, int(total_pages))
        package(reversals_folder_path=selected_path_reversals.value, image_teacher_path=selected_path_teacher.value,
                lists_jpeg=lists_jpeg, groups_jpeg=groups_jpeg)
        stop_event.set()
        progress_bar.value = 1.0
        progress_bar.update()
        progress_bar_value.value = 'Finish'
        progress_bar_value.update()

    def pick_path_reversals_result(e: ft.FilePickerResultEvent):
        selected_path_reversals.value = e.path
        selected_path_reversals.update()

    def pick_path_teacher_result(e: ft.FilePickerResultEvent):
        if len(e.files) == 1:
            selected_path_teacher.value = e.files[0].path
        else:
            selected_path_teacher.value = "Не выбрано!"
        selected_path_teacher.update()

    def pick_path_lists_result(e: ft.FilePickerResultEvent):
        selected_path_lists.value = e.path
        selected_path_lists.update()

    def pick_path_group_result(e: ft.FilePickerResultEvent):
        selected_path_group.value = e.path
        selected_path_group.update()

    def pick_path_individual_group_result(e: ft.FilePickerResultEvent):
        selected_path_individual_group.value = e.path
        selected_path_individual_group.update()

    def pick_path_individual_lists_result(e: ft.FilePickerResultEvent):
        selected_path_individual_lists.value = e.path
        selected_path_individual_lists.update()

    pick_path_reversals_dialog = ft.FilePicker(on_result=pick_path_reversals_result)
    selected_path_reversals = ft.Text()

    pick_path_teacher_dialog = ft.FilePicker(on_result=pick_path_teacher_result)
    selected_path_teacher = ft.Text()

    pick_path_lists_dialog = ft.FilePicker(on_result=pick_path_lists_result)
    selected_path_lists = ft.Text()

    pick_path_group_dialog = ft.FilePicker(on_result=pick_path_group_result)
    selected_path_group = ft.Text()

    pick_path_individual_lists_dialog = ft.FilePicker(on_result=pick_path_individual_lists_result)
    selected_path_individual_lists = ft.Text()

    pick_path_individual_group_dialog = ft.FilePicker(on_result=pick_path_individual_group_result)
    selected_path_individual_group = ft.Text()

    progress_bar_value = ft.Text()

    page.overlay.append(pick_path_reversals_dialog)
    page.overlay.append(pick_path_teacher_dialog)
    page.overlay.append(pick_path_lists_dialog)
    page.overlay.append(pick_path_group_dialog)
    page.overlay.append(pick_path_individual_lists_dialog)
    page.overlay.append(pick_path_individual_group_dialog)

    def switch_changed(e, elevated_button, text, row):
        if e.control.value:  # e.control.value is the current state of the switch
            if elevated_button not in row.controls:
                row.controls.append(elevated_button)
                row.controls.append(text)
        else:
            if elevated_button in row.controls:
                row.controls.remove(elevated_button)
                row.controls.remove(text)
        page.update()

    elevated_button_individual_list = ft.ElevatedButton(
        "Индивидуальные списки",
        icon=ft.icons.FOLDER_OPEN,
        on_click=lambda _: pick_path_individual_lists_dialog.get_directory_path(
            initial_directory=selected_path_reversals.value.rsplit("\\", 1)[0])
    )
    switch1 = ft.Switch(
        label="Индивидуальные списки",
        on_change=lambda e: switch_changed(e, elevated_button_individual_list,
                                           selected_path_individual_lists, row_lists)
    )

    elevated_button_individual_group = ft.ElevatedButton(
        "Индивидуальные групповые",
        icon=ft.icons.FOLDER_OPEN,
        on_click=lambda _: pick_path_individual_group_dialog.get_directory_path(
            initial_directory=selected_path_reversals.value.rsplit("\\", 1)[0])
    )
    switch2 = ft.Switch(
        label="Индивидуальные групповые",
        on_change=lambda e: switch_changed(e, elevated_button_individual_group,
                                           selected_path_individual_group, row_group)
    )

    row_lists = ft.Row(
        [
            ft.ElevatedButton(
                "Списки",
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: pick_path_lists_dialog.get_directory_path(
                    initial_directory=selected_path_reversals.value.rsplit("\\", 1)[0]),
            ),
            selected_path_lists
        ],
    )

    row_group = ft.Row(
        [
            ft.ElevatedButton(
                "Групповые",
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: pick_path_group_dialog.get_directory_path(
                    initial_directory=selected_path_reversals.value.rsplit("\\", 1)[0]),
            ),
            selected_path_group
        ],
    )
    progress_bar = ft.ProgressBar(value=0.0, color=ft.colors.WHITE, height=5, width=600)
    page.add(
        ft.Row(
            [
                ft.ElevatedButton(
                    "Развороты",
                    icon=ft.icons.FOLDER_OPEN,
                    on_click=lambda _: pick_path_reversals_dialog.get_directory_path(),
                ),
                selected_path_reversals,
            ],
        ),
        ft.Row(
            [
                ft.ElevatedButton(
                    "Учительница",
                    icon=ft.icons.FOLDER_OPEN,
                    on_click=lambda _: pick_path_teacher_dialog.pick_files(
                        initial_directory=selected_path_reversals.value.rsplit("\\", 1)[0]),
                ),
                selected_path_teacher,
            ],
        ),
        row_lists,
        row_group,
        ft.Row(
            [
                ft.ElevatedButton(
                    "Печать",
                    icon=ft.icons.PRINT,
                    on_click=lambda _: _package()
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
    )

    page.add(ft.Row([switch1]),
             ft.Row([switch2]),
             ft.Row(
                 [progress_bar],
                 alignment=ft.MainAxisAlignment.CENTER
             ),
             ft.Row([progress_bar_value],
                    alignment=ft.MainAxisAlignment.CENTER)
             )

    def update_progress(value):
        progress_bar.value = value
        progress_bar_value.value = str(int(value * 100)) + '%'
        progress_bar.update()
        progress_bar_value.update()
        page.update()

    def monitor_folder(folder_path, total_files, stop_event):
        while not stop_event.is_set():
            current_files = len(os.listdir(folder_path))
            progress = current_files / total_files if total_files > 0 else 0
            update_progress(progress)
            time.sleep(1)

    def start_monitoring(folder_path, total_files):
        stop_event.clear()
        monitor_thread = threading.Thread(target=monitor_folder, args=(folder_path, total_files, stop_event))
        monitor_thread.start()

    stop_event = threading.Event()
    output_path = "C:/undr/2024/Школа №18 9Г/res"


ft.app(target=front_main)
