import time

import flet as ft

error_container = None


def init(error_cont):
    global error_container
    error_container = error_cont


def show_error_message(message):
    if error_container:
        error_container.content.value = message
        error_container.opacity = 1.0
        error_container.update()

        # Запуск таймера для скрытия сообщения через 3 секунды
        time.sleep(3)
        hide_error_message()


def hide_error_message():
    if error_container:
        error_container.opacity = 0.0
        error_container.update()


def clear_error_message():
    if error_container:
        error_container.opacity = 0.0
        error_container.update()
