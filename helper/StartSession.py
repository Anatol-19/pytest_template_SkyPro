import configparser
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService, Service
from selenium.webdriver.firefox.service import Service as Service_FF
from selenium.webdriver.edge.service import Service as Service_E
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.opera import OperaDriverManager

from config import BROWSER, VERSION, HEADLESS, SCREEN_RESOLUTION, USER_AGENT

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StartSession:
    BASE_URL = None  # Статическая переменная для хранения базового URL

    @staticmethod
    def load_config():
        """Загрузка конфигурации из файла base_urls.ini."""
        config = configparser.ConfigParser()
        config.read('./URLs/base_urls.ini')
        return config

    @classmethod
    def set_base_url(cls):
        """Установка базового URL в зависимости от текущего окружения."""
        config = cls.load_config()
        current_env = config['environments']['current_environment']
        cls.BASE_URL = config[current_env]['BASE_URL']
        logger.info(f"Установлен базовый URL: {cls.BASE_URL}")

    def __init__(self):
        self.driver = None
        self.set_base_url()  # Устанавливаем базовый URL при инициализации

    def start_browser(self):
        """Запуск браузера с учетом конфигурации."""
        try:
            options = None

            if BROWSER == 'chrome' or BROWSER is None:
                options = webdriver.ChromeOptions()
                if HEADLESS:
                    options.add_argument('--headless')
                options.add_argument(f'--window-size={SCREEN_RESOLUTION}')
                options.add_argument(f'user-agent={USER_AGENT}')
                # self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
                self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager(driver_version=VERSION).install()),
                                               options=options)

            elif BROWSER == 'firefox':
                options = webdriver.FirefoxOptions()
                if HEADLESS:
                    options.add_argument('--headless')
                options.set_preference("general.useragent.override", USER_AGENT)
                # self.driver = webdriver.Firefox(service=Service_FF(GeckoDriverManager().install()), options=options)
                self.driver = webdriver.Firefox(service=Service(GeckoDriverManager(version=VERSION).install()),
                                                options=options)

            # ToDo С оперой каккие то неполадки с инициализацией браузера. Так же нужно добавить Сафари!
            # elif BROWSER == 'opera':
            #     options = webdriver.ChromeOptions()  # Opera использует ChromeOptions
            #     if HEADLESS:
            #         options.add_argument('--headless')
            #     options.add_argument(f'--window-size={SCREEN_RESOLUTION}')
            #     options.add_argument(f'user-agent={USER_AGENT}')
            #     self.driver = webdriver.Opera(service=Service(OperaDriverManager(version=VERSION).install()), options=options)

            # elif BROWSER == 'edge':
            #     options = webdriver.EdgeOptions()
            #     if HEADLESS:
            #         options.add_argument('--headless')
            #     options.add_argument(f'user-agent={USER_AGENT}')
            #     self.driver = webdriver.Edge(service=Service(EdgeDriverManager(version=VERSION).install()), options=options)

            else:
                logger.error(f"Неизвестный тип браузера: {BROWSER}")
                raise ValueError(f"Неизвестный тип браузера: {BROWSER}")

            logger.info("Браузер успешно запущен.")
        except Exception as e:
            logger.error(f"Ошибка при запуске браузера: {e}")
            raise

    def open_session(self, tokens):
        """Открытие главной страницы проекта с передачей токенов."""
        try:
            main_page_url = self.load_config()['URLs']['main_page']
            self.driver.get(main_page_url)
            # TODO: Передача токенов для верификации и авторизации
            logger.info("Главная страница успешно открыта.")
        except Exception as e:
            logger.error(f"Ошибка при открытии главной страницы: {e}")
            raise


    def open_page(self, slug):
        """Открытие страницы по-заданному slug."""
        try:
            url = f"{self.BASE_URL}{slug}"  # Формируем полный URL
            self.driver.get(url)
            # Ожидание полной загрузки страницы
            WebDriverWait(self.driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            logger.info(f"Страница {url} успешно открыта.")
        except Exception as e:
            logger.error(f"Ошибка при открытии страницы {slug}: {e}")
            raise

    def close_browser(self):
        """Закрытие браузера."""
        if self.driver:
            self.driver.quit()
            logger.info("Браузер закрыт.")
