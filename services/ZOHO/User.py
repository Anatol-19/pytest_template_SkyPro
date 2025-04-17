class User:
    """Класс, представляющий пользователя."""

    def __init__(self, user_id: int, user_name: str, role: str, email: str):
        """
        Инициализирует экземпляр User.

        Параметры:
            user_id (int): Идентификатор пользователя.
            user_name (str): Имя пользователя.
            role (str): Роль пользователя.
            email (str): Электронная почта пользователя.
        """
        self.user_id = user_id
        self.user_name = user_name
        self.role = role
        self.email = email


class UserManager:
    """
    Класс для управления пользователями.

    Атрибуты:
        users (dict[int, User]): Словарь пользователей, где ключ - идентификатор пользователя, значение - экземпляр User.
    """
    def __init__(self):
        self.users = {}

    def add_user(self, user_id: int, user_name: str, role: str, email: str) -> None:
        """
        Добавляет нового пользователя в коллекцию.

        Параметры:
            user_id (int): Идентификатор пользователя.
            user_name (str): Имя пользователя.
            role (str): Роль пользователя.
            email (str): Электронная почта пользователя.
        """
        self.users[user_id] = User(user_id, user_name, role, email)

    def get_user_by_id(self, user_id: int) -> User | None:
        """
        Получает пользователя по его ID.

        Параметры:
            user_id (int): Идентификатор пользователя.

        Возвращает:
            User | None: Экземпляр User, соответствующий переданному ID, или None, если пользователь не найден.
        """
        return self.users.get(user_id)

    def get_user_by_name(self, user_name: str) -> User | None:
        """
        Получает пользователя по его имени.

        Параметры:
            user_name (str): Имя пользователя.

        Возвращает:
            User | None: Экземпляр User, соответствующий переданному имени, или None, если пользователь не найден.
        """
        for user in self.users.values():
            if user.user_name == user_name:
                return user
        return None

    def load_users(self, users_data: list[dict[str, any]]) -> None:
        """
        Загружает пользователей из предоставленных данных.

        Параметры:
            users_data (list[dict[str, any]]): Список словарей с данными о пользователях.
        """
        for user in users_data:
            self.add_user(
                user_id=user['id'],
                user_name=user['name'],
                role=user['role'],
                email=user['email']
            )
