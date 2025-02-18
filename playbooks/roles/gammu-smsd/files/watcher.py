#!/usr/bin/env python3
import subprocess
import re
import datetime
import logging

# Настройка логирования в файл и консоль
logging.basicConfig(
    filename="log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logging.getLogger().addHandler(console_handler)

errors = [
    "Probably the phone is not connected. (TIMEOUT[14])",
    "Error at init connection:",
    "Error getting SMS status:",
]


def check_logs():
    try:
        now = datetime.datetime.now()
        time_format = "%Y-%m-%d %H:%M:%S"
        time_threshold = now - datetime.timedelta(minutes=15)
        since_time = time_threshold.strftime(time_format)
        until_time = now.strftime(time_format)

        command = f"journalctl -u gammu-smsd.service --since='{since_time}' --until='{until_time}'"
        log_output = subprocess.check_output(command, shell=True).decode("utf-8")

        for error in errors:
            if re.search(error, log_output):
                logging.warning(
                    "Телефон, вероятно, не подключен или возникла ошибка открытия устройства. Выполняется перезапуск сервиса."
                )
                restart_service()
                break  # Прерываем цикл, если ошибка найдена
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка при выполнении команды journalctl: {e}")
    except Exception as e:
        logging.error(f"Непредвиденная ошибка: {e}")


def restart_service():
    try:
        logging.info("Перезагрузка правил udev...")
        subprocess.run("udevadm control --reload-rules", shell=True, check=True)
        logging.info("Запуск событий udev...")
        subprocess.run("udevadm trigger", shell=True, check=True)
        logging.info("Перезапуск сервиса gammu-smsd...")
        subprocess.run("systemctl restart gammu-smsd.service", shell=True, check=True)
        logging.info("Сервис успешно перезапущен!")
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка при перезапуске сервиса: {e}")


# Запускаем функцию для проверки логов и перезапуска сервиса при необходимости
check_logs()
