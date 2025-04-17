class DefectStatus:
    """Класс, представляющий статус дефекта."""

    def __init__(self, sequence: int, status_id: str, status_name: str, is_default: bool, is_closed: bool):
        """
        Инициализирует экземпляр DefectStatus.

        Параметры:
            sequence (int): Порядковый номер статуса.
            status_id (str): Идентификатор статуса.
            status_name (str): Название статуса.
            is_default (bool): Является ли статусом по умолчанию.
            is_closed (bool): Является ли статус закрытым.
        """
        self.sequence = sequence
        self.status_id = status_id
        self.status_name = status_name
        self.is_default = is_default
        self.is_closed = is_closed


class DefectStatusManager:
    """
    Класс для управления статусами дефектов.

    Атрибуты:
        statuses (dict): Словарь статусов, где ключ - идентификатор статуса, значение - экземпляр DefectStatus.
    """

    def __init__(self):
        self.statuses = {}

    def add_status(self, status_id: str, status_name: str, is_default_value: bool, sequence: int) -> None:
        """
        Добавляет новый статус в коллекцию.

        Параметры:
            status_id (str): Идентификатор статуса.
            status_name (str): Название статуса.
            is_default_value (bool): Является ли статусом по умолчанию.
            sequence (int): Порядковый номер статуса.
        """
        self.statuses[status_id] = DefectStatus(
            sequence=sequence,
            status_id=status_id,
            status_name=status_name,
            is_default=is_default_value,
            is_closed=False  # По умолчанию закрытым не считаем
        )

    def get_status_by_id(self, status_id: str) -> DefectStatus | None:
        """
        Получает статус по его ID.

        Параметры:
            status_id (str): Идентификатор статуса.

        Возвращает:
            DefectStatus: Экземпляр DefectStatus, соответствующий переданному ID, или None, если статус не найден.
        """
        return self.statuses.get(status_id)

    def get_status_by_name(self, status_name: str) -> DefectStatus | None:
        """
        Получает статус по его названию.

        Параметры:
            status_name (str): Название статуса.

        Возвращает:
            DefectStatus: Экземпляр DefectStatus, соответствующий переданному названию, или None, если статус не найден.
        """
        for status in self.statuses.values():
            if status.status_name == status_name:
                return status
        return None

    def load_statuses(self, statuses_data: list[dict[str, any]]) -> None:
        """
        Загружает статусы из предоставленных данных.

        Параметры:
            statuses_data (list): Список словарей с данными о статусах.
        """
        for status in statuses_data:
            self.add_status(
                status_id=status['status_id'],
                status_name=status.get('status_name', ''),
                is_default_value=status.get('is_default_value', False),
                sequence=status.get('sequence', 0)
            )