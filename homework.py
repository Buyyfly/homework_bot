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
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение успешно отправлено')
    except Exception as err:
        raise exceptions.MessageError(f'Сообще не отправлено по причине {err}')


def get_api_answer(current_timestamp):
    """Запрос к ENDPOINT."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as err:
        raise ConnectionError(f'Ошибка подключения - {err}')

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
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError('Домашки приходят не в виде списка в ответ от API')
    return homeworks


def parse_status(homework):
    """Получение статуса домашний работы."""
    if 'homework_name' not in homework:
        raise KeyError('Не найден ключ "homework_name"')
    if 'status' not in homework:
        raise KeyError('Не найден ключ "status"')
    hw_status = homework['status']
    if hw_status not in VERDICTS:
        raise ValueError('Не найден статус')
    homework_name = homework['homework_name']
    verdict = VERDICTS[hw_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия токенов."""
    # стало хуже. Что возвращает all()?
    # /
    # Вернет False если хоть один из токенов отсутствует
    return all([PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN])


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
                send_message(bot, str(err))
            except Exception:
                raise exceptions.MessageError(
                    f'Ошибка отправки сообщения об ошибке - {err}'
                )
            raise exceptions.MessageError(
                f'Ошибка отправки сообщения - {err}'
            )
        # тут используем свою ранее написанную функцию,
        # а не метод объекта бота.
        # И проблема предыдущего ревью тут не решена.
        # Подсказка: поможет несколько блоков except
        # /
        # Куда здесь еще блоки? Для чего? Не совмесем понятно.
        # Прошу объяснить
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
