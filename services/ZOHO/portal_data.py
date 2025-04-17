from TaskStatus import TaskStatusManager
from DefectStatus import DefectStatusManager
from User import UserManager

def create_task_status_manager():
    """
    Создаёт и возвращает экземпляр TaskStatusManager с загруженными статусами задач.
    Возвращает:
        TaskStatusManager: Экземпляр менеджера статусов задач.
    """
    task_statuses_data = [
        {
            "sequence": 0,
            "is_start": False,
            "status_id": "1209515000001653473",
            "is_default_value": False,
            "status_name": "In Progress",
            "status_color_hexcode": "#fbc11e",
            "is_closed": False
        },
        {
            "sequence": 0,
            "is_start": False,
            "status_id": "1209515000003027676",
            "is_default_value": False,
            "status_name": "Code Review",
            "status_color_hexcode": "#8cbabb",
            "is_closed": False
        },
        {
            "sequence": 0,
            "is_start": False,
            "status_id": "1209515000000016071",
            "is_default_value": False,
            "status_name": "Closed",
            "status_color_hexcode": "#db9aca",
            "is_closed": True
        },
        {
            "sequence": 0,
            "is_start": False,
            "status_id": "1209515000006442033",
            "is_default_value": False,
            "status_name": "Pending test deploy",
            "status_color_hexcode": "#a593ff",
            "is_closed": False
        },
        {
            "sequence": 0,
            "is_start": False,
            "status_id": "1209515000002033124",
            "is_default_value": False,
            "status_name": "Pending Test",
            "status_color_hexcode": "#ff7bd7",
            "is_closed": False
        },
        {
            "sequence": 0,
            "is_start": False,
            "status_id": "1209515000000384421",
            "is_default_value": False,
            "status_name": "Testing",
            "status_color_hexcode": "#558dca",
            "is_closed": False
        },
        {
            "sequence": 0,
            "is_start": False,
            "status_id": "1209515000004547102",
            "is_default_value": False,
            "status_name": "PreRelease",
            "status_color_hexcode": "#49e6cf",
            "is_closed": False
        },
        {
            "sequence": 0,
            "is_start": False,
            "status_id": "1209515000000428177",
            "is_default_value": False,
            "status_name": "Release Ready",
            "status_color_hexcode": "#74cb80",
            "is_closed": False
        },
        {
            "sequence": 0,
            "is_start": False,
            "status_id": "1209515000000384499",
            "is_default_value": False,
            "status_name": "HOLD",
            "status_color_hexcode": "#67a0ff",
            "is_closed": False
        },
        {
            "sequence": 0,
            "is_start": True,
            "status_id": "1209515000000016068",
            "is_default_value": True,
            "status_name": "Open",
            "status_color_hexcode": "#a7bcee",
            "is_closed": False
        },
        {
            "sequence": 0,
            "is_start": False,
            "status_id": "1209515000000384469",
            "is_default_value": False,
            "status_name": "Feedback needed",
            "status_color_hexcode": "#f56b62",
            "is_closed": False
        },
        {
            "sequence": 0,
            "is_start": False,
            "status_id": "1209515000013605635",
            "is_default_value": False,
            "status_name": "DEV Analysis",
            "status_color_hexcode": "#f6a96d",
            "is_closed": False
        },
        {
            "sequence": 0,
            "is_start": False,
            "status_id": "1209515000013612330",
            "is_default_value": False,
            "status_name": "Ready to DEV",
            "status_color_hexcode": "#e6cb4c",
            "is_closed": False
        },
        {
            "sequence": 0,
            "is_start": False,
            "status_id": "1209515000013697849",
            "is_default_value": False,
            "status_name": "Reopen",
            "status_color_hexcode": "#ffffff",
            "is_closed": False
        }
    ]

    task_status_mngr = TaskStatusManager()
    task_status_mngr.load_statuses(task_statuses_data)
    return task_status_mngr


def create_defect_status_manager():
    """
    Создаёт и возвращает экземпляр DefectStatusManager с загруженными статусами дефектов.
    Возвращает:
        DefectStatusManager: Экземпляр менеджера статусов дефектов.
    """
    defect_statuses_data = [
        {"sequence": 1, "status_id": "1209515000000007045", "status_name": "Open", "is_default_value": True},
        {"sequence": 2, "status_id": "1209515000006897235", "status_name": "Dev Working", "is_default_value": False},
        {"sequence": 3, "status_id": "1209515000007512002", "status_name": "Pending Test Deploy", "is_default_value": False},
        {"sequence": 4, "status_id": "1209515000006897226", "status_name": "Ready for Test", "is_default_value": False},
        {"sequence": 5, "status_id": "1209515000006898002", "status_name": "BackLog", "is_default_value": False},
        {"sequence": 6, "status_id": "1209515000000007054", "status_name": "Closed", "is_default_value": False},
        {"sequence": 7, "status_id": "1209515000000007057", "status_name": "Reopen", "is_default_value": False},
        {"sequence": 8, "status_id": "1209515000007031151", "status_name": "Complete", "is_default_value": False},
        {"sequence": 9, "status_id": "1209515000000007048", "status_name": "In progress", "is_default_value": False},
        {"sequence": 10, "status_id": "1209515000000007051", "status_name": "To be tested", "is_default_value": False}
    ]

    defect_status_mngr = DefectStatusManager()
    defect_status_mngr.load_statuses(defect_statuses_data)
    return defect_status_mngr


def create_user_manager():
    """
    Создаёт и возвращает экземпляр UserManager с загруженными пользователями.
    Возвращает:
        UserManager: Экземпляр менеджера пользователей.
    """
    users_data = [
        {"id": 64602517, "name": "Boris Smirnoff", "role": "admin", "email": "boris@vrbangers.com",
         "name_ru": "Борис Смирнов"},
        {"id": 8365013, "name": "Сергей Шевцов", "role": "admin", "email": "sergey.shevtsov@itspecial.net",
         "name_ru": "Сергей Шевцов"},
        {"id": 661299265, "name": "Arthur Mirzoev", "role": "SEO", "email": "arthur@vrbangers.com",
         "name_ru": "Артур Мирзоев"},
        {"id": 24264590, "name": "Evgeny Mishenko", "role": "admin", "email": "e.mishenko@itspecial.net",
         "name_ru": "Евгений Мищенко"},
        {"id": 680686059, "name": "Oleg Simakov", "role": "Manager", "email": "oleg@vrbangers.com",
         "name_ru": "Олег Симаков"},
        {"id": 685494071, "name": "Andrey Vasilyev", "role": "admin", "email": "andrey@vrbangers.com",
         "name_ru": "Андрей Васильев"},
        {"id": 743258772, "name": "Sergey Lysenkov", "role": "QA", "email": "s.lysenkov@itspecial.net",
         "name_ru": "Сергей Лысенков"},
        {"id": 762609753, "name": "Denis Turchak", "role": "PM", "email": "d.turchak@itspecial.net",
         "name_ru": "Денис Турчак"},
        {"id": 765918803, "name": "Alexey Demidov", "role": "Dev Ops", "email": "a.demidov@itspecial.net",
         "name_ru": "Алексей Демидов"},
        {"id": 775242826, "name": "Akim Antropov", "role": "PM", "email": "a.antropov@itspecial.net",
         "name_ru": "Аким Антропов"},
        {"id": 780778478, "name": "Vladimir German", "role": "UX/Ui", "email": "vladimir@swearl.com",
         "name_ru": "Владимир Герман"},
        {"id": 780776404, "name": "Vitaliy Davydov", "role": "Manager", "email": "v.davydov@itspecial.net",
         "name_ru": "Виталий Давыдов"},
        {"id": 789623918, "name": "Zakhar Lada", "role": "QA", "email": "z.lada@itspecial.net",
         "name_ru": "Захар Лада"},
        {"id": 804464244, "name": "Alexander Savenkov", "role": "SEO", "email": "a.savenkov@swearl.com",
         "name_ru": "Александр Савенков"},
        {"id": 805221168, "name": "Maria Manyk", "role": "Employee", "email": "maria@swearl.com",
         "name_ru": "Мария Маник"},
        {"id": 811688812, "name": "Vladimir Lisevich", "role": "Dev Back", "email": "v.lisevich@itspecial.net",
         "name_ru": "Владимир Лисевич"},
        {"id": 816882747, "name": "Anatol Kiseleow", "role": "QA", "email": "a.kiselev@itspecial.net",
         "name_ru": "Анатолий Киселев"},
        {"id": 829499008, "name": "Danil Babenkov", "role": "Dev Front", "email": "d.babenkov@itspecial.net",
         "name_ru": "Данил Бабенков"},
        {"id": 831928373, "name": "Fedor Garanin", "role": "Dev Front", "email": "f.garanin@itspecial.net",
         "name_ru": "Федор Гаранин"},
        {"id": 837019002, "name": "Maxim Achapovskiy", "role": "QA", "email": "m.achapovskiy@itspecial.net",
         "name_ru": "Максим Ачаповский"},
        {"id": 850833916, "name": "Maria Alekseeva", "role": "Dev Back", "email": "m.alekseeva@itspecial.net",
         "name_ru": "Мария Алексеева"},
        {"id": 850359581, "name": "Dmitriy Pasichnyk", "role": "Employee", "email": "dp@swearl.com",
         "name_ru": "Дмитрий Пасичник"},
        {"id": 868210973, "name": "Anton Kazakoff", "role": "PM", "email": "a.kazakov@itspecial.net",
         "name_ru": "Антон Казаков"},
        {"id": 868403565, "name": "Nikita Molostov", "role": "QA", "email": "n.molostov@itspecial.net",
         "name_ru": "Никита Молостов"},
        {"id": 868817959, "name": "Stepan Zhiravetckii", "role": "QA", "email": "s.zhiravetskiy@itspecial.net",
         "name_ru": "Степан Жиравецкий"},
        {"id": 871064308, "name": "Vladislav Nezvanov", "role": "Dev Front", "email": "v.nezvanov@itspecial.net",
         "name_ru": "Владислав Незванов"},
        {"id": 874081343, "name": "Danil Kazakov", "role": "QA", "email": "d.kazakov@itspecial.net",
         "name_ru": "Данил Казаков"},
        {"id": 881324026, "name": "Sergey Egorov", "role": "Employee", "email": "s.egorov@itspecial.net",
         "name_ru": "Сергей Егоров"}
    ]

    user_mngr = UserManager()
    user_mngr.load_users(users_data)
    return user_mngr

# Инициализация всех менеджеров
user_manager = create_user_manager()
task_status_manager = create_task_status_manager()
defect_status_manager = create_defect_status_manager()