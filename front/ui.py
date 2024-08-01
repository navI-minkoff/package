import ctypes
import sys
from functools import partial

import flet as ft

from main import package


def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)


def front_main(page: ft.Page):
    page.title = "undr"
    page.theme_mode = "dark"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def _package():
        run_as_admin()
        package(folder_path=selected_path_reversals.value, image_teacher_path=selected_path_teacher.value,
                folder_lists_path=selected_path_lists.value, folder_group_path=selected_path_group.value)

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

    pick_path_reversals_dialog = ft.FilePicker(on_result=pick_path_reversals_result)
    selected_path_reversals = ft.Text()

    pick_path_teacher_dialog = ft.FilePicker(on_result=pick_path_teacher_result)
    selected_path_teacher = ft.Text()

    pick_path_lists_dialog = ft.FilePicker(on_result=pick_path_lists_result)
    selected_path_lists = ft.Text()

    pick_path_group_dialog = ft.FilePicker(on_result=pick_path_group_result)
    selected_path_group = ft.Text()

    page.overlay.append(pick_path_reversals_dialog)
    page.overlay.append(pick_path_teacher_dialog)
    page.overlay.append(pick_path_lists_dialog)
    page.overlay.append(pick_path_group_dialog)

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

        ft.Row(
            [
                ft.ElevatedButton(
                    "Списки",
                    icon=ft.icons.FOLDER_OPEN,
                    on_click=lambda _: pick_path_lists_dialog.get_directory_path(
                        initial_directory=selected_path_reversals.value.rsplit("\\", 1)[0]),
                ),
                selected_path_lists,
            ],

        ),

        ft.Row(
            [
                ft.ElevatedButton(
                    "Групповые",
                    icon=ft.icons.FOLDER_OPEN,
                    on_click=lambda _: pick_path_group_dialog.get_directory_path(
                        initial_directory=selected_path_reversals.value.rsplit("\\", 1)[0]),
                ),
                selected_path_group,
            ],

        ),

        ft.Row(
            [
                ft.ElevatedButton(
                    "Печать",
                    icon=ft.icons.PRINT,
                    on_click=lambda _: _package()
                ),

            ],
            alignment=ft.MainAxisAlignment.CENTER
        )

    )


ft.app(target=front_main)
