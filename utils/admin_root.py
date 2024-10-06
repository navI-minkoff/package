import ctypes
import subprocess
import sys


def ensure_admin():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            # Перезапуск скрипта с правами администратора
            script = sys.executable
            params = ' '.join([f'"{arg}"' for arg in sys.argv])  # Добавляем кавычки к каждому аргументу
            subprocess.run(['powershell', '-Command', f'Start-Process "{script}" -ArgumentList {params} -Verb RunAs'])
            # sys.exit(0)
    except OSError as e:
        print(f"Error checking admin status: {e}")
        sys.exit(1)


def restart_with_admin():
    # Проверяем, запущена ли программа с правами администратора
    if ctypes.windll.shell32.IsUserAnAdmin():
        # Программа уже запущена с правами администратора, ничего не делаем
        sys.exit()
    else:
        # Запускаем новый экземпляр программы с правами администратора
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 0
        )
        # Закрываем старый процесс
        # sys.exit()


def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 0)
