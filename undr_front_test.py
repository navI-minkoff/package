import ctypes
import json
import os
import sys
import threading
import time
import logging
import socket
import flet as ft
import requests
from flet import Theme, Colors

from main_module.package_module import package
from utils import error_message_module
from utils.adding_cover.add_covers import adding_covers_based_on_portrait
from utils.admin_root import ensure_admin, restart_with_admin, run_as_admin
from utils.file_utils import getJpegFilenames, extractNumber
from utils.photoshop_utils import types_album, designs_album
from utils.naming_utils import truncateAfterWordOrLast
from utils.settings_utils import load_settings, save_settings
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

buttons_height = 40

path_to_layout_text = ft.Text()
path_to_layout = None


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except OSError as e:
        logging.error(f"Ошибка проверки статуса администратора: {e}")
        return False


def get_directory_path_folder(dialog, selected_path: ft.Text):
    global path_to_layout_text, path_to_layout
    if not path_to_layout_text.value:
        dialog.get_directory_path()
        path_to_layout_text = selected_path
    elif not path_to_layout:
        path_to_layout = truncateAfterWordOrLast(path_to_layout_text.value)
        dialog.get_directory_path(initial_directory=path_to_layout)
    else:
        dialog.get_directory_path(initial_directory=path_to_layout)


def get_directory_path_file(dialog, selected_path):
    global path_to_layout_text, path_to_layout
    if not path_to_layout_text.value:
        dialog.pick_files()
        path_to_layout_text = selected_path
    elif not path_to_layout:
        path_to_layout = truncateAfterWordOrLast(path_to_layout_text.value)
        dialog.pick_files(initial_directory=path_to_layout)
    else:
        dialog.pick_files(initial_directory=path_to_layout)


def clear_directory_path():
    global path_to_layout_text, path_to_layout
    path_to_layout_text = ft.Text()
    path_to_layout = None


# def load_settings():
#     if os.path.exists(SETTINGS_FILE):
#         with open(SETTINGS_FILE, "r") as f:
#             loaded_settings = json.load(f)
#             # Добавляем недостающие ключи с значениями по умолчанию
#             for key, value in default_settings.items():
#                 if key not in loaded_settings:
#                     loaded_settings[key] = value
#             return loaded_settings
#     else:
#         with open(SETTINGS_FILE, "w") as f:
#             json.dump(default_settings, f, indent=4)
#         return default_settings
#
#
# def save_settings(settings):
#     if os.path.exists(SETTINGS_FILE):
#         with open(SETTINGS_FILE, "w") as f:
#             json.dump(settings, f, indent=4)


settings = load_settings()
load_dotenv()

stop_package_thread = False
stop_package_event = threading.Event()


# Функция-заглушка для проверки токена
# def check_token(token: str) -> tuple[bool, str]:
#     if not token:
#         return False, "Токен не введен"
#     if token == "test123":
#         logging.info("Успешная авторизация")
#         return True, None
#     logging.warning(f"Неверный токен: {token}")
#     return False, "Неверный токен"


def check_token(token: str) -> tuple[bool, str | None]:
    if not token:
        return False, "Токен не введен"

    server_url = os.getenv("SERVER_URL")
    auth_token = os.getenv("AUTH_TOKEN")
    headers = {"accept": "application/json", "Authorization": f"Bearer {auth_token}"}

    try:
        response = requests.post(server_url, params={"token": token}, headers=headers, timeout=5)
        response.raise_for_status()

        result = response.json()

        if result.get("is_valid", False):
            return True, None
        else:
            return False, result.get("message", "Токен недействителен")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return False, "Токен не найден"
        return False, "Ошибка подключения к серверу"
    except requests.exceptions.RequestException as e:
        return False, "Сетевая ошибка: проверьте подключение к интернету"
    except ValueError as e:
        return False, "Ошибка обработки ответа сервера"


# Функция создания диалога авторизации
def create_auth_dialog(page: ft.Page, on_success: callable):
    error_text = ft.Text("", color=Colors.RED_400 if settings["theme"] == "Light" else Colors.RED_300, size=12)
    token_input = ft.TextField(
        label="Введите токен",
        password=True,
        width=250,
        prefix_icon=ft.Icons.LOCK_OUTLINED,
        border_radius=8,
        bgcolor=Colors.WHITE if settings["theme"] == "Light" else Colors.GREY_800,
        border_color=Colors.BLUE_200 if settings["theme"] == "Light" else Colors.BLUE_400,
        focused_border_color=Colors.BLUE_700 if settings["theme"] == "Light" else Colors.BLUE_100,
        text_style=ft.TextStyle(size=14, color=Colors.BLACK if settings["theme"] == "Light" else Colors.WHITE),
        on_change=lambda e: update_button_state(e),
        on_submit=lambda e: authenticate(e)
    )
    loading_indicator = ft.ProgressRing(visible=False, width=20, height=20, color=Colors.BLUE_700)

    def update_button_state(e):
        login_button.disabled = not bool(token_input.value.strip())
        page.update()

    def authenticate(e):
        token = token_input.value.strip()
        loading_indicator.visible = True
        token_input.disabled = True
        page.update()
        time.sleep(1)
        success, error = check_token(token)
        loading_indicator.visible = False
        token_input.disabled = False
        if success:
            settings["token"] = token
            save_settings(settings)
            auth_dialog.opacity = 0
            auth_dialog.update()
            time.sleep(0.3)
            auth_dialog.open = False
            page.update()
            on_success()
        else:
            error_text.value = error
            error_text.update()
            page.update()

    # Кнопки под полем ввода
    login_button = ft.ElevatedButton(
        "Войти",
        on_click=authenticate,
        bgcolor=Colors.BLUE_700 if settings["theme"] == "Light" else Colors.BLUE_200,
        color=Colors.WHITE if settings["theme"] == "Light" else Colors.BLACK,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.only(left=20, right=20, top=8, bottom=8)
        ),
        disabled=True
    )
    exit_button = ft.TextButton(
        "Выйти",
        on_click=lambda _: sys.exit(),
        style=ft.ButtonStyle(
            color=Colors.GREY_600 if settings["theme"] == "Light" else Colors.GREY_400
        )
    )
    buttons_row = ft.Row([login_button, exit_button], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

    auth_dialog = ft.AlertDialog(
        title=ft.Text("Авторизация", size=16, weight=ft.FontWeight.W_500,
                      color=Colors.BLUE_700 if settings["theme"] == "Light" else Colors.BLUE_200),
        content=ft.Container(
            content=ft.Column([
                token_input,
                buttons_row,
                error_text,
                loading_indicator
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            padding=ft.padding.all(15),
            bgcolor=Colors.WHITE if settings["theme"] == "Light" else Colors.GREY_900,
            border_radius=12,
            width=300,
            height=180,
        ),
        actions=[],
        actions_alignment=ft.MainAxisAlignment.CENTER,
        modal=True,
        bgcolor=Colors.TRANSPARENT,
    )

    return auth_dialog


def front_main(page: ft.Page):
    page.title = "undr"
    page.theme_mode = settings["theme"]
    page.theme = Theme(color_scheme=ft.ColorScheme(
        primary=Colors.BLUE_700,
        secondary=Colors.BLUE_200,
        background=Colors.GREY_100 if settings["theme"] == "Light" else Colors.GREY_900
    ))
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    global error_container
    error_container = ft.Container(
        content=ft.Text(value="", color=Colors.WHITE),
        padding=ft.padding.all(10),
        bgcolor=Colors.RED_700,
        border_radius=ft.border_radius.all(8),
        opacity=0.0,
        animate_opacity=300,
        alignment=ft.alignment.bottom_right,
    )

    def open_settings_dialog(e):
        def pick_file_result(e: ft.FilePickerResultEvent):
            if e.files and len(e.files) == 1:
                if psd_file_path_text.value == "Не выбрано!":
                    psd_file_path_text.value = e.files[0].path
                elif excel_path_text.value == "Не выбрано!":
                    excel_path_text.value = e.files[0].path
                else:
                    pass
            else:
                if psd_file_path_text.value == "Не выбрано!":
                    psd_file_path_text.value = "Не выбрано!"
                elif excel_path_text.value == "Не выбрано!":
                    excel_path_text.value = "Не выбрано!"
            psd_file_path_text.update()
            excel_path_text.update()

        def pick_directory_result(e: ft.FilePickerResultEvent):
            if e.path:
                covers_path_text.value = e.path
            else:
                covers_path_text.value = "Не выбрано!"
            covers_path_text.update()

        # Инициализация FilePicker для файлов и директорий
        file_picker = ft.FilePicker(on_result=pick_file_result)
        directory_picker = ft.FilePicker(on_result=pick_directory_result)
        page.overlay.append(file_picker)
        page.overlay.append(directory_picker)

        # Инициализация текстовых полей и чекбокса
        psd_file_path_text = ft.Text(settings["file_path"] if settings["file_path"] else "Не выбрано!", width=300)
        covers_path_text = ft.Text(settings["covers_path"] if settings["covers_path"] else "Не выбрано!", width=300)
        excel_path_text = ft.Text(settings["excel_path"] if settings["excel_path"] else "Не выбрано!", width=300)
        surname_column_text = ft.TextField(
            label="Номер колонки\nс фамилиями",
            value=settings["surname_column"] if "surname_column" in settings else "",
            width=150,
            border_radius=10
        )
        cover_column_text = ft.TextField(
            label="Номер колонки\nс обложками",
            value=settings["cover_column"] if "cover_column" in settings else "",
            width=150,
            border_radius=10
        )
        # header_row_text = ft.TextField(
        #     label="Номер строки\nс заголовками",
        #     value=str(settings["header_row"]) if "header_row" in settings else "",
        #     width=130,
        #     border_radius=10,
        #     keyboard_type=ft.KeyboardType.NUMBER
        # )
        close_psd_file_checkbox = ft.Checkbox(
            label="Закрывать PSD файл",
            value=True if settings["close_psd"] == "True" else False
        )

        def save_and_close(e):
            settings["theme"] = theme_dropdown.value
            if not psd_file_path_text.value or psd_file_path_text.value == "Не выбрано!":
                error_message_module.show_error_message("Не выбран PSD файл")
                return
            elif psd_file_path_text.value.split('.')[-1].lower() != 'psd':
                error_message_module.show_error_message("Выберите файл формата PSD")
                return
            settings["file_path"] = psd_file_path_text.value
            settings["covers_path"] = covers_path_text.value if covers_path_text.value != "Не выбрано!" else ""
            settings["excel_path"] = excel_path_text.value if excel_path_text.value != "Не выбрано!" else ""
            settings["surname_column"] = surname_column_text.value if surname_column_text.value else ""
            settings["cover_column"] = cover_column_text.value if cover_column_text.value else ""
            # settings["header_row"] = int(header_row_text.value) if header_row_text.value.isdigit() else 1
            settings["close_psd"] = str(close_psd_file_checkbox.value)
            save_settings(settings)
            settings_dialog.open = False
            page.theme_mode = settings["theme"]
            page.update()

        # Создание выпадающего списка для темы
        theme_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Light"),
                ft.dropdown.Option("Dark"),
            ],
            value=settings["theme"],
            label="Тема",
            width=200,
            border_radius=10
        )

        # Формирование диалога настроек с увеличенными размерами
        settings_dialog = ft.AlertDialog(
            title=ft.Text("Настройки", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    # Секция выбора темы
                    ft.Text("Выбор темы", size=14, weight=ft.FontWeight.BOLD),
                    theme_dropdown,
                    ft.Divider(height=20, thickness=1),

                    # Секция PSD
                    ft.Text("PSD", size=14, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Text("Путь к PSD:", size=14),
                        ft.IconButton(icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: file_picker.pick_files()),
                        psd_file_path_text,
                    ]),
                    ft.Row([close_psd_file_checkbox]),
                    ft.Divider(height=20, thickness=1),

                    # Секция Excel
                    ft.Text("Excel", size=14, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Text("Путь к Excel таблице:", size=14),
                        ft.IconButton(icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: file_picker.pick_files()),
                        excel_path_text,
                    ]),
                    ft.Container(height=5),
                    ft.Row([
                        surname_column_text,
                        ft.Container(width=10),
                        cover_column_text,
                        # ft.Container(width=10),
                        # header_row_text
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Divider(height=20, thickness=1),

                    # Секция Обложки
                    ft.Text("Обложки", size=14, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Text("Путь к обложкам:", size=14),
                        ft.IconButton(icon=ft.Icons.FOLDER_OPEN,
                                      on_click=lambda _: directory_picker.get_directory_path()),
                        covers_path_text,
                    ]),
                ], spacing=10),  # Включаем прокрутку
                width=550,  # Увеличиваем ширину
                height=500  # Увеличиваем высоту
            ),
            actions=[
                ft.ElevatedButton("Сохранить", on_click=save_and_close, bgcolor=Colors.BLUE_700, color=Colors.WHITE)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            content_padding=20,
            shape=ft.RoundedRectangleBorder(radius=15)
        )

        page.overlay.append(settings_dialog)
        settings_dialog.open = True
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
             "postfix": "000"}
        ]

        if selected_path_individual_lists.value:
            individual_list_jpegs = os.listdir(selected_path_individual_lists.value)
            for list_jpeg in individual_list_jpegs:
                lists_jpeg.append(
                    {"lists_folder_path": selected_path_individual_lists.value,
                     "lists_jpeg_filenames": [list_jpeg],
                     "postfix": list_jpeg.split(' ')[0].zfill(3)}
                )

        groups_jpeg = [
            {"groups_jpeg": selected_path_group.value,
             "group_jpeg_filenames": sorted(getJpegFilenames(selected_path_group.value), key=extractNumber),
             "postfix": "000"}
        ]

        if selected_path_individual_group.value:
            individual_group_folders = os.listdir(selected_path_individual_group.value)
            for folder in individual_group_folders:
                path = selected_path_individual_group.value + f"/{folder}"
                groups_jpeg.append(
                    {"groups_jpeg": path,
                     "group_jpeg_filenames": sorted(getJpegFilenames(path), key=extractNumber),
                     "postfix": folder.split(' ')[0].zfill(3)}
                )

        all_group_pages = 0
        for group in groups_jpeg:
            all_group_pages += len(group['group_jpeg_filenames']) / 2

        total_pages = 2 * len(os.listdir(selected_path_reversals.value)) - 1 + \
                      len(lists_jpeg[0]['lists_jpeg_filenames']) / 2 + \
                      len(lists_jpeg) - 1 + \
                      all_group_pages

        album_design = designs_album[1] if design_switcher.value else designs_album[0]
        full_output_path = os.path.join(selected_path_output.value, dropdown.value, album_design)
        os.makedirs(full_output_path, exist_ok=True)

        start_monitoring(full_output_path, int(total_pages))
        start_adding_covers_based_on_portrait(selected_path_reversals.value, lists_jpeg[0]['lists_folder_path'],
                                              full_output_path,
                                              dropdown.value, album_design)
        package(
            reversals_folder_path=selected_path_reversals.value,
            image_teacher_path=selected_path_teacher.value,
            lists_jpeg=lists_jpeg,
            groups_jpeg=groups_jpeg,
            output_path=full_output_path,
            source_psd_path=settings["file_path"],
            album_version=dropdown.value,
            album_design=album_design,
            auto_close=settings["close_psd"],
        )
        stop_event.set()
        clear_directory_path()
        update_progress_bar(1.0, 'Finish')

    def check_all_paths_specified(lists_jpeg, groups_jpeg):
        if not settings["file_path"]:
            error_message_module.show_error_message("Не выбран PSD файл")
            return True
        if not selected_path_reversals.value or not selected_path_teacher.value \
                or not lists_jpeg[0] or not groups_jpeg[0] \
                or (elevated_button_individual_list in row_lists.controls and not lists_jpeg[1]) \
                or (elevated_button_individual_group in row_group.controls and not groups_jpeg[1]) \
                or not selected_path_output.value:
            error_message_module.show_error_message('Укажите все пути')
            return True
        if not dropdown.value:
            error_message_module.show_error_message('Выберите вид альбома')
            return True
        return False

    def pick_path_reversals_result(e: ft.FilePickerResultEvent):
        selected_path_reversals.value = e.path
        selected_path_reversals.update()

    def pick_path_teacher_result(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) == 1:
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
        icon=ft.Icons.FOLDER_OPEN,
        on_click=lambda _: get_directory_path_folder(pick_path_individual_lists_dialog, selected_path_individual_lists)
    )
    switch1 = ft.Switch(
        label="Индивидуальные списки",
        height=buttons_height,
        on_change=lambda e: switch_changed(e, elevated_button_individual_list, selected_path_individual_lists,
                                           row_lists)
    )

    elevated_button_individual_group = ft.ElevatedButton(
        "Индивидуальные групповые",
        height=buttons_height,
        icon=ft.Icons.FOLDER_OPEN,
        on_click=lambda _: get_directory_path_folder(pick_path_individual_group_dialog, selected_path_individual_group)
    )
    switch2 = ft.Switch(
        label="Индивидуальные групповые",
        height=buttons_height,
        on_change=lambda e: switch_changed(e, elevated_button_individual_group, selected_path_individual_group,
                                           row_group)
    )

    design_switcher = ft.Switch(
        label="Темный",
        value=False,
    )
    dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(opt) for opt in types_album],
        width=200,
        label="Вид альбома",
        border_radius=10
    )

    dropdown_switcher_row = ft.Row(controls=[
        dropdown,
        ft.Text("  Светлый"),
        design_switcher,
    ])

    row_lists = ft.Row([
        ft.ElevatedButton(
            "Списки",
            height=buttons_height,
            icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda _: get_directory_path_folder(pick_path_lists_dialog, selected_path_lists)
        ),
        selected_path_lists
    ])

    row_group = ft.Row([
        ft.ElevatedButton(
            "Групповые",
            height=buttons_height,
            icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda _: get_directory_path_folder(pick_path_group_dialog, selected_path_group)
        ),
        selected_path_group
    ])

    progress_bar = ft.ProgressBar(value=0.0, color=Colors.BLUE_700, height=5, width=600)
    page.add(
        ft.Row([
            ft.Text(''),
            ft.IconButton(
                icon=ft.Icons.SETTINGS,
                icon_size=30,
                on_click=open_settings_dialog,
                alignment=ft.alignment.center_right,
                tooltip="Настройки"
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Row([
            ft.ElevatedButton(
                "Портреты",
                height=buttons_height,
                icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda _: get_directory_path_folder(pick_path_reversals_dialog, selected_path_reversals),
            ),
            selected_path_reversals
        ]),
        ft.Row([
            ft.ElevatedButton(
                "Учителя",
                height=buttons_height,
                icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda _: get_directory_path_file(pick_path_teacher_dialog, selected_path_teacher)
            ),
            selected_path_teacher,
        ]),
        row_lists,
        row_group,
        dropdown_switcher_row,
        ft.Row([
            ft.ElevatedButton(
                "Результат",
                height=buttons_height,
                icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda _: get_directory_path_folder(pick_path_output_dialog, selected_path_output)
            ),
            selected_path_output
        ]),
        ft.Row([
            ft.ElevatedButton(
                "Упаковка",
                height=buttons_height,
                icon=ft.Icons.PRINT,
                on_click=lambda _: _package()
            ),
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([switch1]),
        ft.Row([switch2]),
        ft.Row([progress_bar], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([progress_bar_value], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([error_container], alignment=ft.MainAxisAlignment.END),
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

    def start_adding_covers_based_on_portrait(portrait_files_path, collage_files_path, output_path,
                                              type_album, design_album):
        adding_covers_based_on_portrait(portrait_files_path, collage_files_path, output_path, type_album, design_album)

    stop_event = threading.Event()
    error_message_module.init(error_container)


# Проверка на множественный запуск
def is_already_running():
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock_socket.bind(("127.0.0.1", 9999))
        return False
    except socket.error:
        return True
    finally:
        lock_socket.close()


# Главная функция приложения
def main(page: ft.Page):
    # Устанавливаем минимальные и начальные размеры окна сразу
    page.window_min_width = 800  # Минимальная ширина окна
    page.window_min_height = 600  # Минимальная высота окна
    page.window_width = 800  # Начальная ширина окна
    page.window_height = 600  # Начальная высота окна

    def show_main_interface():
        logging.info("Запуск основного интерфейса")
        page.controls.clear()
        page.update()
        front_main(page)

    # Проверка сохраненного токена
    saved_token = settings.get("token")
    if saved_token:
        success, error = check_token(saved_token)
        if success:
            logging.info("Автоматическая авторизация успешна")
            show_main_interface()
            return
        else:
            logging.warning(f"Сохраненный токен недействителен: {error}")

    # Показываем диалог авторизации
    auth_dialog = create_auth_dialog(page, show_main_interface)
    page.overlay.append(auth_dialog)
    auth_dialog.open = True
    page.update()


if __name__ == "__main__":
    logging.info(f"Запуск приложения, PID: {os.getpid()}")
    # if is_already_running():
    #     logging.warning("Приложение уже запущено")
    #     sys.exit(1)
    # if not is_admin():
    #     logging.info("Приложение не запущено с правами администратора, попытка перезапуска")
    #     try:
    #         restart_with_admin()
    #         sys.exit(0)
    #     except Exception as e:
    #         logging.error(f"Не удалось перезапустить с правами администратора: {e}")
    #         ft.app(target=lambda page: page.add(
    #             ft.Text("Ошибка: Не удалось получить права администратора", color=Colors.RED_700)))
    #         sys.exit(1)
    restart_with_admin()
    ft.app(target=main)
