import os
import sys
import json
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.ZOHO.Zoho_api_client import ZohoAPI


class TestPlanGenerator:
    """
    Класс для генерации тест-плана релиза.
    """


    def __init__(self, users_mngr, task_status_mngr, defect_status_mngr):
        """
        Инициализирует TestPlanGenerator с менеджерами пользователей, статусов задач и дефектов.
        """
        self.api = ZohoAPI()
        self.user_manager = users_mngr
        self.task_status_manager = task_status_mngr
        self.defect_status_manager = defect_status_mngr
        self.template = self.load_template()
        self.start_date = None
        self.end_date = None
        self.all_tasks = []
        self.milestones_in_sprint = []

    def set_dates(self, start_date: str, end_date: str) -> None:
        """
        Устанавливает даты начала и конца спринта.
        """
        self.start_date = start_date
        self.end_date = end_date

    ###################################################
    # DeBugs Methods

    # Пример функции для сохранения JSON-ответа в файл
    def save_json_to_file(self, data, filename="response.json"):
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print(f"✅ JSON-ответ сохранён в файл: {filename}")

    def print_json_to_console(self, data):
        """
        Выводит JSON-объект в консоль в читаемом формате.
        """
        print(json.dumps(data, indent=4, ensure_ascii=False))
    ##################################################

    def initialize_tasks_and_milestones(self, titles):
        """
        Инициализирует список задач и мейлстоунов для генерации тест-плана.
        """
        for title in titles:
            tasks = self.api.get_tasks_by_title(title)

            # Добавляем задачи, избегая дублирования
            for task in tasks:
                if task not in self.all_tasks:
                    self.all_tasks.append(task)

                # Сохраняем уникальные мейлстоуны
                milestone_id = task.get("milestone_id")
                if milestone_id and milestone_id not in self.milestones_in_sprint:
                    self.milestones_in_sprint.append(milestone_id)


    @staticmethod
    def load_template() -> str:
        """
        Загружает шаблон тест-плана.
        """
        return """
> "Этот документ используется для планирования, координации и отчётности по тестированию задач текущего релиза."

## 1. Продукт и функциональность

> Функции и описание тестируемой системы

### Затронутый функциональность в рамках релиза

{{affected_functionality}}

### Фокус лист

{{focus_list}}

## 2. Задачи в рамках релиза

{{tasks_table}}

## 3. Основные требования
- [Frozen Maket VRS](https://www.figma.com/design/p2PTHvq7gnvN4O28rfbkJU/vrsmash-frozen-03-04-2025?node-id=1609-149106&t=TVn695vjIEkdUVMU-1)
- [ACP Maket](https://www.figma.com/design/wf3rauB0bulldYVuJuUCGy/CREATOR-PORTAL---ADMIN--Copy-11-03-2025-?node-id=12902-17996&t=AVsZbiMSJuxCk76n-1)
- [Документация QA по VRS](https://docs.vrbangers.com/wiki/vrporn/view/Main/)
- [Матрица трассировки по покрытию требований тестами](https://docs.google.com/spreadsheets/d/1O5v8aaTbaYDWrEZa29lLJEUFlK_A9lil/edit?usp=sharing&ouid=100519744549498352317&rtpof=true&sd=true) (В разработке)

## 4. Виды тестирования и планируемое расписание:
| Виды тестирования          | Дата       | Ответственный | Статус        |
| -------------------------- | ---------- | ------------- | ------------- |
{{testing_schedule}}

## Тестовая документация
{{regression_report}}
"""


    @staticmethod
    def generate_tasks_table(tasks: list[dict]) -> str:
        """
        Генерирует таблицу задач для указанного мейлстоуна.
        """
        header = "| Задача (ID, название) | Мейлстоун/Таск-лист | Приоритет | QA  | Dev  | Статус   |\n"
        header += "| --------------------- | ------------------- | --------- | --- | ---- | -------- |\n"

        def format_owners(t_owners: list[dict], role: str) -> str:
            return ", ".join(
                owner["full_name"] for owner in t_owners if owner.get("role") == role
            ) or "Не назначен"

        tasks_table = ""
        for task in tasks:
            milestone_or_tasklist = f"{task.get('milestone_name', 'Не указан')} / {task.get('tasklist')}"
            owners = task.get("details", {}).get("owners", [])
            qa_list = format_owners(owners, "QA")
            dev_list = format_owners(owners, "Dev")
            tasks_table += (
                f"| [{task['key']}]({task['link']['web']['url']}) - {task['name']} | "
                f"{milestone_or_tasklist} | {task.get('priority', 'Не указан')} | "
                f"{qa_list} | {dev_list} | {task['status']['name']} |\n"
            )
        return header + tasks_table


    def generate_testing_schedule(self) -> str:
        """
        Генерирует расписание тестирования.
        """
        # Преобразуем дату начала спринта в объект datetime
        start_date = datetime.strptime(self.start_date, "%Y-%m-%d")

        # Вычисляем даты для тестирования
        test_start_date = start_date + timedelta(days=4)  # 5-й день спринта
        test_end_date = start_date + timedelta(days=6)  # 7-й день спринта
        stage_date = start_date + timedelta(days=7)  # 8-й день спринта (четверг)
        prod_date = start_date + timedelta(days=9)  # 10-й день спринта (вторник)

        tasks = self.api.get_tasks_in_date_range(self.start_date, self.end_date)
        return (
            f"| Тестирование задач спринта | {self.start_date} - {self.end_date}| QA Team | 🟡 В процессе |\n"
            f"| Регресс пула задач спринта на [TEST] | {test_start_date.strftime('%d%m%y')} - {test_end_date.strftime('%d%m%y')} | QA1, QA2 | 🔴 Не начато |\n"
            f"| Регресс релизной ветки на [STAGE] | {stage_date.strftime('%d%m%y')} | QA1, QA2 | 🔴 Не начато |\n"
            f"| Регресс на [PROD] | {prod_date.strftime('%d%m%y')} | QA3 | 🟢 Готово |\n"
        )


    def generate_focus_list(self) -> str:
        """
        Генерирует фокус-лист для тест-плана.
        """
        tasks = self.api.get_tasks_in_date_range(self.start_date, self.end_date)
        return (
            "- 📌 _Ключевые изменения (новый функционал, доработки, рефакторинг)_\n"
            "- 🐞 _Регрессные дефекты (новые баги, возникшие снова)_\n"
            "- ⚠️ _Флакующие тесты (нестабильные тесты, требующие анализа)_\n"
            "- *За каждым функционалом закрепляется специалист QA*\n"
            "- *После 2х релизов без дефектов в функционале — он покидает этот список*\n"
            f"- Найдено задач: {len(tasks)}\n"
        )

    def generate_affected_functionality(self, functionality_map: dict) -> str:
        """
        Определяет затронутый функционал на основе задач в указанном диапазоне дат.
        """
        if not self.start_date or not self.end_date:
            raise ValueError("Даты начала и конца спринта не установлены.")

        tasks = self.api.get_entities_by_filter(
            entity_type="tasks",
            created_after=self.start_date,
            created_before=self.end_date
        )

        affected_functionality = set()
        for task in tasks:
            tags = task.get("tags", [])
            for tag in tags:
                if isinstance(tag, dict):
                    tag = tag.get("name", "")
                if tag in functionality_map:
                    affected_functionality.add(functionality_map[tag])
        return "\n".join(f"- {func}" for func in sorted(affected_functionality)) or "Нет данных"

    def generate_defects_table(self, defects: list[dict]) -> str:
        """
        Генерирует таблицу дефектов.
        """
        header = "| Дефект (ID, название) | Приоритет | Серьёзность | QA  | Dev  | Статус   |\n"
        header += "| --------------------- | --------- | ----------- | --- | ---- | -------- |\n"

        def format_owners(d_owners: list[dict], role: str) -> str:
            return ", ".join(
                owner["name_ru"] for owner in d_owners if owner.get("role") == role
            ) or "Не назначен"

        defects_table = ""
        for defect in defects:
            # self.print_json_to_console(defect)  # Для вывода в консоль
            # self.save_json_to_file(defect)  # Для сохранения в файл
            owners = defect.get("details", {}).get("owners", [])
            qa_list = format_owners(owners, "QA")
            dev_list = format_owners(owners, "Dev")
            defects_table += (
                f"| [{defect['key']}]({defect['link']['web']['url']}) - {defect['title']} | "
                f"{defect.get('priority', 'Не указан')} | {defect.get('severity', 'Не указана')} | "
                f"{qa_list} | {dev_list} | {defect['status']['type']} |\n"
            )
        return header + defects_table


    def generate_regression_report(self) -> str:
        """
        Формирует отчёт о регрессе.
        """
        if not self.start_date or not self.end_date:
            raise ValueError("Даты начала и конца спринта не установлены.")

        # Получаем баги в указанном диапазоне дат
        defects = self.api.get_entities_by_filter(
            entity_type="bugs",
            created_after=self.start_date,
            created_before=self.end_date
        )
        closed_defects = self.api.get_entities_by_filter(
            entity_type="bugs",
            closed_after=self.start_date,
            closed_before=self.end_date
        )

        # Генерируем таблицу дефектов
        defects_table = self.generate_defects_table(defects)

        return (
            f"### Обнаруженные дефекты (с {self.start_date} по {self.end_date})\n{defects_table or 'Нет данных'}\n\n"
            f"### Закрытые дефекты (с {self.start_date} по {self.end_date})\n"
            f"{self.generate_defects_table(closed_defects) or 'Нет данных'}\n"
        )


    def generate_plan_for_tasks(self, tasks: list[dict], output_file="test_plan.md") -> None:
        """
        Генерирует тест-план и сохраняет его в файл.
        """
        tasks_table = self.generate_tasks_table(tasks)
        testing_schedule = self.generate_testing_schedule()
        focus_list = self.generate_focus_list()
        affected_functionality = self.generate_affected_functionality(functionality_map={})
        regression_report = self.generate_regression_report()

        plan = (
            self.template
            .replace("{{tasks_table}}", tasks_table)
            .replace("{{testing_schedule}}", testing_schedule)
            .replace("{{focus_list}}", focus_list)
            .replace("{{affected_functionality}}", affected_functionality)
            .replace("{{regression_report}}", regression_report)
        )

        with open(output_file, "w", encoding="utf-8") as file:
            file.write(plan)

        print(f"✅ Тест-план успешно сгенерирован и сохранён в файл {output_file}")