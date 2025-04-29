import sys
import os

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.ZOHO.portal_data import user_manager, task_status_manager, defect_status_manager
from services.ZOHO.Zoho_api_client import ZohoAPI
from services.Release_Test_Plan.TestPlanGenerator import TestPlanGenerator


def get_tasks_by_milestone_name(milestone__name: str) -> list[dict]:
    """
    Получает задачи по названию мейлстоуна.
    Параметры:
        milestone_name (str): Название мейлстоуна.
    Возвращает:
        list[dict]: Список задач для указанного мейлстоуна.
    """
    api = ZohoAPI()

    # Получаем ID мейлстоуна по его названию
    milestone_id = api.get_milestone_id_by_name(milestone__name)
    if milestone_id:
        print(f"✅ Найден мейлстоун: {milestone__name} (ID: {milestone_id})")

        # Получаем задачи для найденного мейлстоуна
        tasks = api.get_tasks(milestone_id)
        if tasks:
            print(f"✅ Найдено {len(tasks)} задач в мейлстоуне '{milestone__name}'")
            return tasks
        else:
            print(f"❌ Не удалось получить задачи для мейлстоуна '{milestone__name}'")
    else:
        print(f"❌ Мейлстоун с названием '{milestone__name}' не найден")

    return []


def generate_test_plan(milestones: list[str]) -> None:
    """
    Генерирует тест-план для указанного мейлстоуна.
    :param milestones : Название мейлстоуна.
    :return: None
    """
    api = ZohoAPI()
    all_tasks = []

    for milestone_name in milestones:
        if not milestone_name.strip():  # Пропускаем пустые или некорректные названия
            print("⚠️ Пропущено пустое или некорректное название мейлстоуна.")
            continue
        milestone_id = api.get_milestone_id_by_name(milestone_name)
        if milestone_id:
            print(f"✅ Найден мейлстоун: {milestone_name} (ID: {milestone_id})")
            tasks = api.get_tasks(milestone_id)
            if tasks:
                print(f"✅ Найдено {len(tasks)} задач в мейлстоуне '{milestone_name}'")
                all_tasks.extend(tasks)
            else:
                print(f"❌ Не удалось получить задачи для мейлстоуна '{milestone_name}'")
        else:
            print(f"❌ Мейлстоун с названием '{milestone_name}' не найден")

    if all_tasks:
        generator = TestPlanGenerator(user_manager, task_status_manager, defect_status_manager)
        generator.generate_plan_for_tasks(all_tasks)
    else:
        print("❌ Не удалось сгенерировать тест-план, так как задачи не найдены.")


    def get_tasks_in_date_range(self, start_date: str, end_date: str) -> list[dict]:
        """
        Получает задачи, созданные в указанном диапазоне дат.
        :param start_date: Начальная дата (YYYY-MM-DD).
        :param end_date: Конечная дата (YYYY-MM-DD).
        :return: Список задач.
        """
        return self.get_entities_by_filter("tasks", created_after=start_date, created_before=end_date)

    def get_bugs_in_date_range(self, start_date: str, end_date: str) -> list[dict]:
        """
        Получает баги, созданные в указанном диапазоне дат.
        :param start_date: Начальная дата (YYYY-MM-DD).
        :param end_date: Конечная дата (YYYY-MM-DD).
        :return: Список багов.
        """
        return self.get_entities_by_filter("bugs", created_after=start_date, created_before=end_date)

    def get_closed_bugs_in_date_range(self, start_date: str, end_date: str) -> list[dict]:
        """
        Получает баги, закрытые в указанном диапазоне дат.
        :param start_date: Начальная дата (YYYY-MM-DD).
        :param end_date: Конечная дата (YYYY-MM-DD).
        :return: Список закрытых багов.
        """
        return self.get_entities_by_filter("bugs", closed_after=start_date, closed_before=end_date)


if __name__ == "__main__":
    # Загружаем переменные окружения
    from dotenv import load_dotenv

    load_dotenv()

    # Инициализируем API
    api = ZohoAPI()

    # Задаём параметры запуска
    start_date = "2025-04-15"
    end_date = "2025-04-22"
    milestone_names = [
        "Release #20"
    ]  # Замените на нужное название мейлстоуна

    # Используем уже инициализированные менеджеры из portal_data
    generator = TestPlanGenerator(user_manager, task_status_manager, defect_status_manager)

    # Устанавливаем даты
    generator.set_dates(start_date, end_date)

    # Собираем задачи из всех мейлстоунов
    all_tasks = []
    for milestone_name in milestone_names:
        tasks = generator.api.get_tasks_by_title(milestone_name)
        all_tasks.extend(tasks)  # Добавляем задачи в общий список

    # Генерируем общий тест-план
    if all_tasks:
        generator.generate_plan_for_tasks(all_tasks)