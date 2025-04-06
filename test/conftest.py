import pytest
from selenium.webdriver.remote.webdriver import WebDriver
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pytest
from config import BROWSER, VERSION, HEADLESS, SCREEN_RESOLUTION, USER_AGENT, LOCAL, DOCKER, CONTOUR, TEST_FLAGS

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture
def browser():
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    browser.implicitly_wait(4)
    browser.maximize_window()
    yield browser

    browser.quit()


def get_installed_browser_version(browser):
    """Получение установленной версии браузера."""
    try:
        if browser == 'chrome':
            version = subprocess.check_output(['google-chrome', '--version']).decode().strip()
            return version.split()[-1]  # Возвращаем только номер версии
        elif browser == 'firefox':
            version = subprocess.check_output(['firefox', '--version']).decode().strip()
            return version.split()[-1]  # Возвращаем только номер версии
        elif browser == 'opera':
            version = subprocess.check_output(['opera', '--version']).decode().strip()
            return version.split()[-1]  # Возвращаем только номер версии
        elif browser == 'edge':
            version = subprocess.check_output(['msedge', '--version']).decode().strip()
            return version.split()[-1]  # Возвращаем только номер версии
    except Exception as e:
        print(f"Ошибка при получении версии браузера {browser}: {e}")
        return None

def pytest_addoption(parser):
    parser.addoption("--browser", action="store", default="chrome", help="Type of browser: chrome, opera, firefox, edge")
    parser.addoption("--headless", action="store_true", help="Run in headless mode")
    parser.addoption("--screen-resolution", action="store", default="1920x1080", help="Screen resolution")
    parser.addoption("--user-agent", action="store", default="Mozilla/5.0", help="User agent string")
    parser.addoption("--local", action="store_true", help="Run locally")
    parser.addoption("--docker", action="store_true", help="Run in Docker")
    parser.addoption("--contour", action="store", default="development", help="Test contour")
    parser.addoption("--test-flags", action="store", default="", help="Comma-separated test flags")

@pytest.fixture(scope="session", autouse=True)
def initialize_config(request):
    global BROWSER, HEADLESS, SCREEN_RESOLUTION, USER_AGENT, LOCAL, DOCKER, CONTOUR, TEST_FLAGS, VERSION

    BROWSER = request.config.getoption("--browser")
    HEADLESS = request.config.getoption("--headless")
    SCREEN_RESOLUTION = request.config.getoption("--screen-resolution")
    USER_AGENT = request.config.getoption("--user-agent")
    LOCAL = request.config.getoption("--local")
    DOCKER = request.config.getoption("--docker")
    CONTOUR = request.config.getoption("--contour")
    TEST_FLAGS = request.config.getoption("--test-flags").split(",") if request.config.getoption("--test-flags") else []

    # Определение версии браузера
    if LOCAL:
        VERSION = get_installed_browser_version(BROWSER) or "latest"  # Если версия не найдена, используем "latest"
    else:
        VERSION = "latest"  # В Docker используем "latest" или конкретную версию, если указано

    # Логирование инициализации
    print(f"Initialized configuration: BROWSER={BROWSER}, VERSION={VERSION}, HEADLESS={HEADLESS}, "
          f"SCREEN_RESOLUTION={SCREEN_RESOLUTION}, USER_AGENT={USER_AGENT}, LOCAL={LOCAL}, "
          f"DOCKER={DOCKER}, CONTOUR={CONTOUR}, TEST_FLAGS={TEST_FLAGS}")