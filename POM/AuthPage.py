# ./POM/AuthPage.py
from helper.StartSession import StartSession
from helper.GUIHelper import GUIHelper
from URLs.routes import ROUTES  # Импортируем словарь с роутами
from POM.selectors import SELECTORS  # Импортируем селекторы
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

class AuthPage:
    def __init__(self, session: StartSession):
        self.session = session
        self.gui_helper = GUIHelper(session.driver)

    def go(self):
        """Переход на страницу авторизации."""
        try:
            auth_page_slug = ROUTES['auth_page']  # Получаем slug из словаря
            self.session.open_page(auth_page_slug)  # Открываем страницу
            logger.info("Перешли на страницу авторизации.")
        except Exception as e:
            logger.error(f"Ошибка при переходе на страницу авторизации: {e}")
            raise

    def login_as(self, email: str, password: str):
        """Вход на сайт с использованием email и пароля."""
        try:
            email_input = self.gui_helper.find_element_by_css(SELECTORS['email_input'])
            password_input = self.gui_helper.find_element_by_css(SELECTORS['password_input'])
            login_button = self.gui_helper.find_element_by_css(SELECTORS['login_button'])

            self.gui_helper.interact_with_element(email_input, 'send_keys', email)
            self.gui_helper.interact_with_element(password_input, 'send_keys', password)
            self.gui_helper.interact_with_element(login_button, 'click')

            logger.info("Успешный вход с использованием email и пароля.")
        except Exception as e:
            logger.error(f"Ошибка при входе: {e}")
            raise

    def check_login_success(self):
        """Проверка успешного входа на сайт."""
        try:
            success_element = self.gui_helper.find_element_by_css(SELECTORS['welcome_message'])  # Пример селектора
            assert success_element.is_displayed(), "Успешный вход не подтвержден."
            logger.info("Вход успешен.")
        except Exception as e:
            logger.error(f"Ошибка при проверке успешного входа: {e}")
            raise
