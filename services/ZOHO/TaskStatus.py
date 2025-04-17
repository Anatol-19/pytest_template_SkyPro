class TaskStatus:
    """Класс, представляющий статус задачи."""

    def __init__(self, status_id: str, status_name: str, is_default_value: bool, sequence: int, status_color_hexcode: str, is_closed: bool):
        """
        Инициализирует экземпляр TaskStatus.

        Параметры:
            status_id (str): Идентификатор статуса.
            status_name (str): Название статуса.
            is_default_value (bool): Является ли статусом по умолчанию.
            sequence (int): Порядковый номер статуса.
            status_color_hexcode (str): Цвет статуса в шестнадцатеричном формате.
            is_closed (bool): Является ли статус закрытым.
        """
        self.status_id = status_id
        self.status_name = status_name
        self.is_default_value = is_default_value
        self.sequence = sequence
        self.status_color_hexcode = status_color_hexcode
        self.is_closed = is_closed


class TaskStatusManager:
    """
    Класс для управления статусами задач.

    Атрибуты:
        statuses (dict[str, TaskStatus]): Словарь статусов, где ключ - идентификатор статуса, значение - экземпляр TaskStatus.
    """
    def __init__(self):
        self.statuses = {}

    def add_status(self, status_id: str, status_name: str, is_default_value: bool, sequence: int, status_color_hexcode: str, is_closed: bool) -> None:
        """
        Добавляет новый статус в коллекцию.

        Параметры:
            status_id (str): Идентификатор статуса.
            status_name (str): Название статуса.
            is_default_value (bool): Является ли статусом по умолчанию.
            sequence (int): Порядковый номер статуса.
            status_color_hexcode (str): Цвет статуса в шестнадцатеричном формате.
            is_closed (bool): Является ли статус закрытым.
        """
        self.statuses[status_id] = TaskStatus(status_id, status_name, is_default_value, sequence, status_color_hexcode, is_closed)

    def get_status_by_id(self, status_id: str) -> TaskStatus | None:
        """
        Получает статус по его ID.

        Параметры:
            status_id (str): Идентификатор статуса.

        Возвращает:
            TaskStatus | None: Экземпляр TaskStatus, соответствующий переданному ID, или None, если статус не найден.
        """
        return self.statuses.get(status_id)

    def get_status_by_name(self, status_name: str) -> TaskStatus | None:
        """
        Получает статус по его названию.

        Параметры:
            status_name (str): Название статуса.

        Возвращает:
            TaskStatus | None: Экземпляр TaskStatus, соответствующий переданному названию, или None, если статус не найден.
        """
        for status in self.statuses.values():
            if status.status_name == status_name:
                return status
        return None

    def load_statuses(self, statuses_data: list[dict[str, any]]) -> None:
        """
        Загружает статусы из предоставленных данных.

        Параметры:
            statuses_data (list[dict[str, any]]): Список словарей с данными о статусах.
        """
        for status in statuses_data:
            self.add_status(
                status_id=status['status_id'],
                status_name=status.get('status_name', ''),
                is_default_value=status.get('is_default_value', False),
                sequence=status.get('sequence', 0),
                status_color_hexcode=status.get('status_color_hexcode', ''),
                is_closed=status.get('is_closed', False)
            )