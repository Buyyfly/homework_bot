import os
import time
import logging
from dotenv import load_dotenv
import telegram
import requests

import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.info('Сообщение успешно отправлено')


def get_api_answer(current_timestamp):
    """Запрос к ENDPOINT."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
    except Exception as err:
        raise Exception(f'Ошибка подключения - {err}')

    if response.status_code != 200:
        raise exceptions.ConnectError('Подкючение не удалось')
    homework_statuses = response.json()
    return homework_statuses


def check_response(response):
    """Проверка ответа API."""
    if not isinstance(response, dict):
        raise TypeError('Не корректный ответ от API')
    if 'homeworks' not in response:
        raise KeyError('Ключ не найден')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Домашки приходят не в виде списка в ответ от API')
    return response.get('homeworks')


def parse_status(homework):
    """Получение статуса домашний работы."""
    if 'homework_name' not in homework:
        raise KeyError('Не найден ключ "homework_name"')
    if 'status' not in homework:
        raise KeyError('Не найден ключ "status"')

    if homework['status'] not in VERDICTS:
        raise ValueError('Не найден статус')
    homework_name = homework['homework_name']
    verdict = VERDICTS.get(homework['status'])
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия токенов."""
    if all([PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN]):
        return True
    return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if not check_tokens():
        raise exceptions.TokenError('Не заполнены токены')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            status = parse_status(homeworks[0])
            send_message(bot, status)
        except Exception as err:
            try:
                bot.send_message(TELEGRAM_CHAT_ID, str(err))
            except Exception:
                raise
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler(__file__ + '.log', encoding='UTF-8')
    ]
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=handlers,
        format=(
            '%(asctime)s, %(levelname)s, %(funcName)s, %(lineno)d, %(message)s'
        ))
    main()
