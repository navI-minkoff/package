import ctypes
import json
import os
import subprocess
import sys
import threading
import time

import flet as ft

from main_module.package_module import package
from utils import update_module
from utils.admin_root import ensure_admin, restart_with_admin, run_as_admin
from utils.file_utils import getJpegFilenames, extractNumber
from utils.photoshop_utils import types_album, designs_album
from utils.naming_utils import truncateAfterWordOrLast

buttons_height = 40


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except OSError as e:
        print(f"Error checking admin status: {e}")
        return False


# Путь к файлу настроек
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "utils", "settings.json")

# Структура настроек по умолчанию
default_settings = {
    "file_path": "",
    "theme": "Dark",
    "close_psd": "True"
}

path_to_layout_text = ft.Text()
path_to_layout = None


def get_directory_path_folder(dialog, selected_path: ft.Text):
    global path_to_layout_text
    global path_to_layout
    if not path_to_layout_text.value:
        dialog.get_directory_path()
        path_to_layout_text = selected_path
    elif not path_to_layout:
        path_to_layout = truncateAfterWordOrLast(path_to_layout_text.value)
        dialog.get_directory_path(initial_directory=path_to_layout)
    else:
        dialog.get_directory_path(initial_directory=path_to_layout)


def get_directory_path_file(dialog, selected_path):
    global path_to_layout_text
    global path_to_layout
    if not path_to_layout_text.value:
        dialog.pick_files()
        path_to_layout_text = selected_path
    elif not path_to_layout:
        path_to_layout = truncateAfterWordOrLast(path_to_layout_text.value)
        dialog.pick_files(initial_directory=path_to_layout)
    else:
        dialog.pick_files(initial_directory=path_to_layout)


def clear_directory_path():
    global path_to_layout_text
    global path_to_layout
    path_to_layout_text = ft.Text()
    path_to_layout = None


# Функция для загрузки настроек из файла
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    else:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(default_settings, f, indent=4)
        return default_settings


# Функция для сохранения настроек в файл
def save_settings(settings):
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f)


settings = load_settings()
stop_package_thread = False
stop_package_event = threading.Event()


def front_main(page: ft.Page):
    page.title = "undr"
    page.theme_mode = settings["theme"]
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Создание контейнера для вывода ошибок
    global error_container
    error_container = ft.Container(
        content=ft.Text(value="", color="white"),
        padding=ft.padding.all(10),
        bgcolor="red",
        border_radius=ft.border_radius.all(8),
        opacity=0.0,  # Начальная непрозрачность (скрыто)
        animate_opacity=300,  # Анимация исчезновения
        alignment=ft.alignment.bottom_right,
    )

    # Функция для открытия диалогового окна настроек
    def open_settings_dialog(e):
        def pick_file_result(e: ft.FilePickerResultEvent):
            if len(e.files) == 1:
                psd_file_path_text.value = e.files[0].path
            else:
                psd_file_path_text.value = "Не выбрано!"
            psd_file_path_text.update()

        file_picker = ft.FilePicker(on_result=pick_file_result)
        page.overlay.append(file_picker)
        psd_file_path_text = ft.Text(settings["file_path"], width=300)
        close_psd_file_checkbox = ft.Checkbox(label="Закрывать PSD файл",
                                              value=True if settings["close_psd"] == "True" else False)

        def save_and_close(e):
            settings["theme"] = theme_dropdown.value
            if not psd_file_path_text.value:
                update_module.show_error_message("Не выбран psd файл")
                return
            elif psd_file_path_text.value.split('.')[-1] != 'psd':
                update_module.show_error_message("Выберите файл формата psd")
                return
            settings["file_path"] = psd_file_path_text.value
            settings["close_psd"] = f"{close_psd_file_checkbox.value}"
            save_settings(settings)
            settings_dialog.open = False
            change_theme()
            page.update()

        def change_theme():
            page.theme_mode = settings["theme"]
            page.update()

        theme_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Light"),
                ft.dropdown.Option("Dark"),
            ],
            value=settings["theme"],
            label="Тема",
        )

        settings_dialog = ft.AlertDialog(
            title=ft.Text("Настройки"),
            content=ft.Column([
                ft.Row([
                    ft.Text("PSD файл:"),
                    ft.IconButton(icon=ft.icons.FOLDER_OPEN, on_click=lambda _: file_picker.pick_files()),
                    psd_file_path_text,

                ]),
                theme_dropdown,
                close_psd_file_checkbox
            ]),
            actions=[
                ft.TextButton("Сохранить", on_click=save_and_close)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(settings_dialog)
        settings_dialog.open = True
        page.update()

    def close_settings_dialog(dialog):
        dialog.open = False
        page.update()

    def update_progress_bar(value, status):
        progress_bar.value = value
        progress_bar.update()
        progress_bar_value.value = status
        progress_bar_value.update()

    def _package():

        if check_all_paths_specified([selected_path_lists.value] + [selected_path_individual_lists.value],
                                     [selected_path_group.value] + [selected_path_individual_group.value]):
            return

        lists_jpeg = [
            {"lists_folder_path": selected_path_lists.value,
             "lists_jpeg_filenames": sorted(getJpegFilenames(selected_path_lists.value), key=extractNumber),
             "postfix": "000"}]

        if selected_path_individual_lists.value:
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

        if selected_path_individual_group.value:
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

        album_design = designs_album[1] if design_switcher.value else designs_album[0]

        full_output_path = os.path.join(selected_path_output.value, dropdown.value, album_design)
        os.makedirs(full_output_path, exist_ok=True)

        start_monitoring(full_output_path, int(total_pages))
        # run_as_admin()
        package(reversals_folder_path=selected_path_reversals.value, image_teacher_path=selected_path_teacher.value,
                lists_jpeg=lists_jpeg, groups_jpeg=groups_jpeg,
                output_path=full_output_path, source_psd_path=settings["file_path"],
                album_type=dropdown.value,
                album_design=album_design,
                auto_close=settings["close_psd"])
        stop_event.set()
        clear_directory_path()
        update_progress_bar(1.0, 'Finish')

    def check_all_paths_specified(lists_jpeg, groups_jpeg):
        if not settings["file_path"]:
            update_module.show_error_message("Не выбран psd файл")
            return True
        if not selected_path_reversals.value or not selected_path_teacher.value \
                or not lists_jpeg[0] or not groups_jpeg[0] \
                or (elevated_button_individual_list in row_lists.controls and not lists_jpeg[1]) \
                or (elevated_button_individual_group in row_group.controls and not groups_jpeg[1]) \
                or not selected_path_output.value:
            update_module.show_error_message('Укажите все пути')
            return True
        if not dropdown.value:
            update_module.show_error_message('Выберите вид альбома')
            return True

        return False

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

    def pick_path_output_result(e: ft.FilePickerResultEvent):
        selected_path_output.value = e.path
        selected_path_output.update()

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

    pick_path_output_dialog = ft.FilePicker(on_result=pick_path_output_result)
    selected_path_output = ft.Text()

    progress_bar_value = ft.Text()

    page.overlay.append(pick_path_reversals_dialog)
    page.overlay.append(pick_path_teacher_dialog)
    page.overlay.append(pick_path_lists_dialog)
    page.overlay.append(pick_path_group_dialog)
    page.overlay.append(pick_path_individual_lists_dialog)
    page.overlay.append(pick_path_individual_group_dialog)
    page.overlay.append(pick_path_output_dialog)

    def switch_changed(e, elevated_button, text, row):
        if e.control.value:
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
        height=buttons_height,
        icon=ft.icons.FOLDER_OPEN,
        on_click=lambda _: get_directory_path_folder(pick_path_individual_lists_dialog, selected_path_individual_lists))
    switch1 = ft.Switch(
        label="Индивидуальные списки",
        height=buttons_height,
        on_change=lambda e: switch_changed(e, elevated_button_individual_list,
                                           selected_path_individual_lists, row_lists)
    )

    elevated_button_individual_group = ft.ElevatedButton(
        "Индивидуальные групповые",
        height=buttons_height,
        icon=ft.icons.FOLDER_OPEN,
        on_click=lambda _: get_directory_path_folder(pick_path_individual_group_dialog, selected_path_individual_group)
    )
    switch2 = ft.Switch(
        label="Индивидуальные групповые",
        height=buttons_height,
        on_change=lambda e: switch_changed(e, elevated_button_individual_group,
                                           selected_path_individual_group, row_group)
    )

    design_switcher = ft.Switch(
        label="Темный",
        value=False,
    )
    # Создание списка вариантов
    dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option(types_album[0]),
            ft.dropdown.Option(types_album[1]),
            ft.dropdown.Option(types_album[2])
        ],
        height=buttons_height * 1.2,
        width=200,
        label="Вид альбома"
    )

    dropdown_switcher_row = ft.Row(controls=[dropdown,
                                             ft.Text("  Светлый"),
                                             design_switcher,
                                             ],
                                   )

    row_lists = ft.Row(
        [
            ft.ElevatedButton(
                "Списки",
                height=buttons_height,
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: get_directory_path_folder(pick_path_lists_dialog, selected_path_lists)
            ),
            selected_path_lists
        ],
    )

    row_group = ft.Row(
        [
            ft.ElevatedButton(
                "Групповые",
                height=buttons_height,
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: get_directory_path_folder(pick_path_group_dialog, selected_path_group)
            ),
            selected_path_group
        ],
    )
    progress_bar = ft.ProgressBar(value=0.0, color=ft.colors.WHITE, height=5, width=600)
    page.add(
        ft.Row([ft.Text(''),
                ft.IconButton(
                    icon=ft.icons.SETTINGS,
                    icon_size=30,
                    on_click=open_settings_dialog,
                    alignment=ft.alignment.center_right
                ),
                ],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Row(
            [
                ft.ElevatedButton(
                    "Развороты",
                    height=buttons_height,
                    icon=ft.icons.FOLDER_OPEN,
                    on_click=lambda _: get_directory_path_folder(pick_path_reversals_dialog, selected_path_reversals),
                ),
                selected_path_reversals]

        ),
        ft.Row(
            [
                ft.ElevatedButton(
                    "Учителя",
                    height=buttons_height,
                    icon=ft.icons.FOLDER_OPEN,
                    on_click=lambda _: get_directory_path_file(pick_path_teacher_dialog, selected_path_teacher)
                ),
                selected_path_teacher,
            ],
        ),
        row_lists,
        row_group,
        dropdown_switcher_row,
        ft.Row(
            [ft.ElevatedButton(
                "Результат",
                height=buttons_height,
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: get_directory_path_folder(pick_path_output_dialog, selected_path_output)
            ),
                selected_path_output]),
        ft.Row(
            [
                ft.ElevatedButton(
                    "Упаковка",
                    height=buttons_height,
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
                    alignment=ft.MainAxisAlignment.CENTER),
             ft.Row([error_container],
                    alignment=ft.MainAxisAlignment.END),
             # ft.Row([ft.ElevatedButton(
             #     "Стоп",
             #     height=buttons_height,
             #     icon=ft.icons.STOP,
             #     on_click=lambda _: stop_package()
             # ),
             # ],
             #     alignment=ft.MainAxisAlignment.END)
             )

    def update_progress(value):
        progress_bar.value = value
        percentage_meaning = int(value * 100) if int(value * 100) <= 100 else 100
        progress_bar_value.value = str(percentage_meaning) + '%'
        progress_bar.update()
        progress_bar_value.update()
        page.update()

    def monitor_folder(folder_path, total_files, stop_event_progress_bar):
        while not stop_event_progress_bar.is_set():
            current_files = len(os.listdir(folder_path))
            progress = current_files / total_files if total_files > 0 else 0
            update_progress(progress)
            time.sleep(1)

    def start_monitoring(folder_path, total_files):
        stop_event.clear()
        monitor_thread = threading.Thread(target=monitor_folder, args=(folder_path, total_files, stop_event))
        monitor_thread.start()

    stop_event = threading.Event()

    update_module.init(error_container)


if __name__ == "__main__":
    # ensure_admin()
    restart_with_admin()
    ft.app(target=front_main)
