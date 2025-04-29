# Новый каркас для объединённого сервиса генерации плана и интеграции с ZOHO/Google

from services.ZOHO.Zoho_api_client import ZohoAPI
import services.ZOHO.portal_data
from services.Release_Test_Plan.TestPlanGenerator import TestPlanGenerator
import os
import json


class QAService:
    """
    Основной сервис, объединяющий работу с ZOHO API, генератором тест-плана и кэшированием статусов.

    Этот класс предоставляет высокоуровневый интерфейс для:
    - генерации тест-планов в формате Markdown,
    - синхронизации статусов задач и багов из ZOHO,
    - взаимодействия с менеджерами пользователей и статусов.
    """

    def __init__(self):
        """
        Инициализация сервиса. Загружает необходимые менеджеры и клиента ZOHO API.
        """
        self.api = ZohoAPI()  # API-клиент для взаимодействия с ZOHO
        self.users = services.ZOHO.portal_data.user_manager  # Менеджер пользователей (UserManager)
        self.task_statuses = services.ZOHO.portal_data.task_status_manager  # Менеджер статусов задач (TaskStatusManager)
        self.defect_statuses = services.ZOHO.portal_data.defect_status_manager  # Менеджер статусов багов (DefectStatusManager)

        # Генератор тест-плана, которому передаём все зависимости
        self.generator = TestPlanGenerator(
            users_mngr=self.users,
            task_status_mngr=self.task_statuses,
            defect_status_mngr=self.defect_statuses,
            api_client=self.api
        )

    def generate_markdown_plan(self, filters: dict, sprint_name: str, start_date: str, end_date: str):
        """
        Генерирует тест-план в формате Markdown по заданным фильтрам задач.

        :param filters: Словарь фильтров (например, created_after / milestone_id и т.п.)
        :param sprint_name: Название спринта, используется для имени выходного файла
        :param start_date: Начало тестового периода (строка в формате YYYY-MM-DD)
        :param end_date: Конец тестового периода
        """
        self.generator.set_dates(start_date, end_date)
        tasks = self.api.get_entities_by_filter(entity_type="tasks", **filters)
        if tasks:
            self.generator.generate_plan_for_tasks(tasks, output_file=f"plan_{sprint_name}.md")
        else:
            print("⚠️ Не удалось найти задачи по заданным фильтрам.")

    def sync_statuses_from_zoho(self, force=False):
        """
        Загружает и кэширует статусы задач и дефектов из ZOHO API.

        :param force: Если True — принудительно перезаписывает кэш
        """
        cache_path = "services/ZOHO/status_cache.json"
        if force or not os.path.exists(cache_path):
            print("🔄 Синхронизация статусов из Zoho...")
            task_statuses = self.api.get_blueprint_graph()
            bug_statuses = self.api.get_bug_statuses()
            status_data = {
                "task_statuses": task_statuses,
                "bug_statuses": bug_statuses
            }
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
            self.generator.sync_statuses(task_statuses, bug_statuses)
        else:
            print("✅ Кэш статусов уже актуален. Загрузка из файла...")
            with open(cache_path, "r", encoding="utf-8") as f:
                status_data = json.load(f)
            self.generator.sync_statuses(status_data["task_statuses"], status_data["bug_statuses"])


# main.py примеры вызова
if __name__ == "__main__":
    service = QAService()
    filters = {"created_after": "2025-04-15", "created_before": "2025-04-22"}
    service.sync_statuses_from_zoho()
    service.generate_markdown_plan(filters, "Release #20", "2025-04-15", "2025-04-22")
