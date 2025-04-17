import requests
import os
from dotenv import load_dotenv


class ZohoAPI:
    """
        Класс для взаимодействия с API Zoho.

        Атрибуты:
            client_id (str): Идентификатор клиента.
            client_secret (str): Секрет клиента.
            refresh_token (str): Токен обновления.
            access_token (str): Токен доступа.
            project_id (str): Идентификатор проекта.
            portal_name (str): Название портала.
            session (requests.Session): Сессия для повторного использования соединений.
            base_url (str): Базовый URL для API запросов.
        """


    def __init__(self):
        env_path = os.path.join(os.path.dirname(__file__), "config_zoho.env")
        load_dotenv(env_path)  # Загружаем переменные из config_zoho.env

        self.client_id = os.getenv("ZOHO_CLIENT_ID")
        self.client_secret = os.getenv("ZOHO_CLIENT_SECRET")
        self.refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
        self.access_token = os.getenv("ZOHO_ACCESS_TOKEN")
        self.project_id = os.getenv("ZOHO_PROJECT_ID")
        self.authorization_code = os.getenv("ZOHO_AUTHORIZATION_CODE")
        self.redirect_uri = os.getenv("ZOHO_REDIRECT_URI")
        self.portal_name = os.getenv("ZOHO_PORTAL_NAME")

        self.session = requests.Session()  # Используем сессию для повторного использования соединений
        self.base_url = self.get_base_url()
        self.check_and_refresh_tokens()


    def get_base_url(self) -> str:
        """
        Определяет правильный API-домен в зависимости от региона.

        Возвращает:
            str: Базовый URL для API запросов.
        """
        domains = {
            "com": "projectsapi.zoho.com",
            "eu": "projectsapi.zoho.eu",
            "in": "projectsapi.zoho.in",
            "cn": "projectsapi.zoho.com.cn"
        }
        region = os.getenv("ZOHO_REGION", "com")  # По умолчанию .com
        return f"https://{domains.get(region, domains['com'])}/restapi/portal/{self.portal_name}"


    def check_and_refresh_tokens(self) -> None:
        """
        Проверяет наличие и валидность токенов. Если токены отсутствуют или недействительны, обновляет их.
        """
        if not self.refresh_token:
            print("🔄 Получение нового refresh_token...")
            self.refresh_token = self.get_refresh_token()
            self.save_tokens(self.access_token, self.refresh_token)

        if not self.access_token or not self.check_access_token():
            print("🔄 Обновление access_token...")
            self.access_token = self.do_access_token()
            self.save_tokens(self.access_token, self.refresh_token)


    def check_access_token(self) -> bool:
        """
        Проверяет, действует ли текущий access_token.
        :return bool: True, если токен действителен, иначе False.
        """
        url = f"{self.base_url}/projects/"
        headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
        response = self.session.get(url, headers=headers)
        return response.status_code == 200


    def request_token(self, grant_type: str, additional_params: dict = None) -> dict:
        """
        Универсальный метод для получения токенов (access_token или refresh_token).
        :param grant_type: Тип запроса токена ('authorization_code' или 'refresh_token').
        :param additional_params: Дополнительные параметры для запроса.
        :return dict: Ответ API с токенами.
        """
        url = "https://accounts.zoho.com/oauth/v2/token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": grant_type,
        }
        if additional_params:
            params.update(additional_params)

        try:
            response = self.session.post(url, data=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка при запросе токена: {e}")
            raise


    def do_access_token(self) -> str:
        """
        Обновляет и получает access_token через refresh_token.
        :return str: Новый токен доступа.
        """
        if not self.refresh_token:
            raise ValueError("Отсутствует refresh_token для обновления access_token.")

        response_data = self.request_token(
            grant_type="refresh_token",
            additional_params={"refresh_token": self.refresh_token}
        )
        new_access_token = response_data.get("access_token")
        if not new_access_token:
            raise ValueError("Не удалось получить новый access_token.")
        print("✅ Новый access_token успешно получен.")
        return new_access_token

    def get_refresh_token(self) -> str:
        """
        Получает refresh_token с использованием ZOHO_AUTHORIZATION_CODE.
        """
        if not self.authorization_code:
            raise ValueError(
                "Отсутствует ZOHO_AUTHORIZATION_CODE для получения refresh_token. "
                "Получите новый код авторизации."
            )

        response_data = self.request_token(
            grant_type="authorization_code",
            additional_params={
                "code": self.authorization_code,
                "redirect_uri": self.redirect_uri,
            }
        )
        new_refresh_token = response_data.get("refresh_token")
        if not new_refresh_token:
            print(f"❌ Ответ от сервера: {response_data}")
            raise ValueError("Не удалось получить новый refresh_token.")
        print("✅ Новый refresh_token успешно получен.")
        return new_refresh_token


    @staticmethod
    def save_tokens(access_token: str, refresh_token: str) -> None:
        """
        Сохраняет access_token и refresh_token в config_zoho.env.
        :param access_token: Новый токен доступа.
        :param refresh_token: Новый токен обновления.
        """
        env_path = os.path.join(os.path.dirname(__file__), "config_zoho.env")
        with open(env_path, "r") as file:
            lines = file.readlines()

        with open(env_path, "w") as file:
            for line in lines:
                if line.startswith("ZOHO_ACCESS_TOKEN="):
                    file.write(f"ZOHO_ACCESS_TOKEN={access_token}\n")
                elif line.startswith("ZOHO_REFRESH_TOKEN="):
                    file.write(f"ZOHO_REFRESH_TOKEN={refresh_token}\n")
                else:
                    file.write(line)


    def send_request(self, url: str, params: dict = None) -> dict | None:
        """
        Универсальный метод для отправки запросов к API Zoho.
        :param url: URL для запроса.
        :param params: Параметры запроса.
        :return dict | None: Ответ API в формате JSON или None в случае ошибки.
        """
        try:
            headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
            response = self.session.get(url, headers=headers, params=params)

            if response.status_code == 401:
                print("🔄 access_token устарел, обновляем...")
                self.access_token = self.do_access_token()
                save_tokens(self.access_token, self.refresh_token)

                # Повторяем запрос с новым токеном
                headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
                response = self.session.get(url, headers=headers, params=params)

            if response.status_code == 403:
                print(f"❌ Ошибка доступа: {response.status_code}, {response.text}")
                return None

            return self.handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return None

    @staticmethod
    def handle_response(response: requests.Response) -> dict | None:
        """
        Обрабатывает HTTP-ответ, проверяет ошибки.
        :param response: HTTP-ответ.
        :return dict | None: Ответ API в формате JSON или None в случае ошибки.
        """
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Ошибка запроса: {response.status_code}, {response.text}")
            return None


    def get_portals(self) -> dict | None:
        """
        Получает список порталов.
        :return dict | None: Список порталов или None в случае ошибки.
        """
        url = f"{self.base_url}/portals/"
        return self.send_request(url)


    def get_entities_by_filter(self, entity_type: str,
                               created_after: str = None,
                               created_before: str = None,
                               closed_after: str = None,
                               closed_before: str = None,
                               owner_id: str = None,
                               tags: list[str] = None,
                               milestone_id: str = None,
                               tasklist_id: str = None
                               ) -> list[dict]:
        """
        Получает сущности (задачи или баги) по фильтру.
         :param entity_type: Тип сущности ('tasks', 'bugs', 'milestones', 'tasklists').
        :param created_after: Дата создания (YYYY-MM-DD), начиная с которой сущности будут включены.
        :param created_before: Дата создания (YYYY-MM-DD), до которой сущности будут включены.
        :param closed_after: Дата закрытия (YYYY-MM-DD), начиная с которой сущности будут включены.
        :param closed_before: Дата закрытия (YYYY-MM-DD), до которой сущности будут включены.
        :param owner_id: ID ответственного пользователя.
        :param tags: Список тегов для фильтрации.
        :param milestone_id: ID мейлстоуна для фильтрации.
        :param tasklist_id: ID таск-листа для фильтрации.
        :return list[dict]: Список сущностей, соответствующих фильтру.
        """
        if entity_type not in ["tasks", "bugs", "milestones", "tasklists"]:
            raise ValueError("Тип сущности должен быть 'tasks', 'bugs', 'milestones' или 'tasklists'.")

        url = f"{self.base_url}/projects/{self.project_id}/{entity_type}/"
        params = {}
        if created_after:
            params["created_date_start"] = created_after
        if created_before:
            params["created_date_end"] = created_before
        if closed_after:
            params["closed_date_start"] = closed_after
        if closed_before:
            params["closed_date_end"] = closed_before
        if owner_id:
            params["owner"] = owner_id
        if tags:
            params["tags"] = ",".join(tags)
        if milestone_id:
            params["milestone_id"] = milestone_id
        if tasklist_id:
            params["tasklist_id"] = tasklist_id

        print(f"🔍 Отправка запроса: URL={url}, Параметры={params}")  # Логирование запроса
        response = self.send_request(url, params=params)
        if response is None:
            print(f"❌ Не удалось получить {entity_type}. Проверьте права доступа.")
            return []
        return response.get(entity_type, [])


    def get_users(self, search_term: str = None) -> list[dict]:
        """
        Получает список пользователей в проекте.
        :param search_term: Строка для поиска пользователей по имени или email.
        :return list[dict]: Список пользователей.
        """
        url = f"{self.base_url}/projects/{self.project_id}/users/"
        params = {}
        if search_term:
            params["search"] = search_term
        return self.send_request(url).get("users", [])


    def get_tasks_by_milestone(self, milestone_id: str) -> list[dict]:
        """
        Получает задачи, связанные с мейлстоуном.
        """
        return self.get_entities_by_filter("tasks", milestone_id=milestone_id)


    def get_tasks_by_tasklist(self, tasklist_id: str) -> list[dict]:
        """
        Получает задачи, связанные с таск-листом.
        """
        return self.get_entities_by_filter("tasks", tasklist_id=tasklist_id)


    def get_tasks_by_title(self, title: str) -> list[dict]:
        """
        Ищет задачи по названию таск-листа или мейлстоуна.
        Сначала ищет по таск-листам, затем по мейлстоунам.
        """
        # Сначала ищем по таск-листам
        tasklist_id = self.get_tasklist_id_by_name(title)
        if tasklist_id:
            return self.get_entities_by_filter("tasks", tasklist_id=tasklist_id)

        # Если не найдено, ищем по мейлстоунам
        milestone_id = self.get_milestone_id_by_name(title)
        if milestone_id:
            return self.get_entities_by_filter("tasks", milestone_id=milestone_id)

        # Если ничего не найдено, возвращаем пустой список
        return []


    def get_tasklist_id_by_name(self, tasklist_name: str) -> str | None:
        """
        Получает ID таск-листа по его названию.
        """
        tasklists = self.get_entities_by_filter("tasklists")
        for tasklist in tasklists:
            if tasklist["name"].lower() == tasklist_name.lower():
                return tasklist["id"]
        return None


    def get_milestone_id_by_name(self, milestone_name: str) -> str | None:
        """
        Получает ID мейлстоуна по его названию.
        """
        milestones = self.get_entities_by_filter("milestones")
        for milestone in milestones:
            if milestone["name"].lower() == milestone_name.lower():
                return milestone["id"]
        return None


    def get_tasks_in_date_range(self, start_date: str, end_date: str) -> list[dict]:
        """
        Получает задачи, созданные в указанном диапазоне дат.
        :param start_date: Начальная дата (YYYY-MM-DD).
        :param end_date: Конечная дата (YYYY-MM-DD).
        :return: Список задач.
        """
        return self.get_entities_by_filter("tasks", created_after=start_date, created_before=end_date)


    def get_blueprint_graph(self) -> dict | None:
        """
        Получает граф Blueprint.
        :return dict | None: Граф Blueprint или None в случае ошибки.
        """
        url = f"{self.base_url}/automation/blueprint/{self.project_id}/graph"
        return self.send_request(url)


    def get_bug_statuses(self) -> list[dict]:
        """
        Получает статусы багов в проекте.
        :return list[dict]: Список статусов багов.
        """
        url = f"{self.base_url}/projects/{self.project_id}/bugs/defaultfields/"
        return self.send_request(url).get("defaultfields", {}).get("status_details", [])


    def get_project_tags(self) -> list[dict]:
        """
        Получает теги проекта.
        :return list[dict]: Список тегов проекта.
        """
        url = f"{self.base_url}/projects/{self.project_id}/tags/"
        response = self.send_request(url)
        return response.get("tags", [])


    def manage_tag(self, tag_id: str, entity_id: str, entity_type: int, action: str) -> bool:
        """
        Ассоциирует или диссоциирует тег с сущностью.

        :param tag_id: ID тега.
        :param entity_id: ID сущности.
        :param entity_type: Тип сущности (5 - задача, 6 - баг).
        :param action: Действие ('associate' или 'dissociate').
        :return bool: Успешность операции.
        """
        if action not in ["associate", "dissociate"]:
            raise ValueError("Действие должно быть 'associate' или 'dissociate'.")

        url = f"{self.base_url}/projects/{self.project_id}/tags/{action}"
        data = {"tag_id": tag_id, "entity_id": entity_id, "entityType": entity_type}
        response = self.send_request(url, params=data)
        return response is not None


    def create_bug(self, title: str, description: str, assignee_id: str = None, priority: str = None) -> dict | None:
        """
        Создаёт баг в проекте.
        :param title: Название бага.
        :param description: Описание бага.
        :param assignee_id: ID ответственного (опционально).
        :param priority: Приоритет бага (опционально).
        :return: dict | None: Ответ API с данными о созданном баге.
        """
        url = f"{self.base_url}/projects/{self.project_id}/bugs/"
        data = {
            "title": title,
            "description": description,
            "assignee_id": assignee_id,
            "priority": priority,
        }
        return self.send_request(url, params=data)
