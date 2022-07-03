class ConnectError(Exception):
    """Подключение не выполнено."""
    pass


class TokenError(Exception):
    """Некорректные токены."""
    pass


class MessageError(Exception):
    """Ошибка отправки сообщения."""
    pass
