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
    parser.addoption("--environment", action="store", default=None, help="Environment from URLs/base_urls.ini")
    parser.addoption("--assets-csv", action="store", default=None, help="CSV export with expected content asset paths")
    parser.addoption("--asset-report", action="store", default=None, help="Path for detailed content asset verification report")
    parser.addoption("--asset-summary", action="store", default=None, help="Path for video-level content asset verification summary")
    parser.addoption("--asset-limit", action="store", default=None, help="Limit number of video rows for content asset tests")
    parser.addoption("--check-http", action="store_true", help="Verify signed CDN URLs with HTTP requests")
    # --- Payment ---
    parser.addoption("--pay-tab", action="store", default="monthly", help="Период покупки: monthly|yearly|lifetime (алиасы year/month/life)")
    parser.addoption("--pay-slot", action="store", default="", help="Спец-цены внутри прайс-группы: пусто=Standard, N (напр. 2)=Special (type_prices_from_slot)")
    # --- Allure ---
    parser.addoption("--no-allure", action="store_true", help="Отключить генерацию Allure-отчёта (по умолчанию включён)")


@pytest.fixture
def pay_opts(request):
    """Параметры выбора тарифа из CLI-флагов."""
    slot = request.config.getoption("--pay-slot")
    return {
        "tab": request.config.getoption("--pay-tab"),
        "slot": int(slot) if slot else None,
    }


def pytest_configure(config):
    """Allure включён по умолчанию (--alluredir в pytest.ini). Флаг --no-allure отключает запись."""
    if config.getoption("--no-allure"):
        config.option.allure_report_dir = None


@pytest.fixture
def payment_env(request):
    """Контур для payment-тестов (VRP_* секция из base_urls.ini). Default VRP_STAGE."""
    env = request.config.getoption("--environment") or "VRP_STAGE"
    if not env.startswith("VRP_"):
        pytest.skip(f"Payment-тесты работают только на VRP-контурах, получено: {env}")
    return env


@pytest.fixture
def payment_flow(payment_env):
    """Собранный PaymentFlow для выбранного контура.

    На teardown прикладывает сводку сессии (email, member_id, membership_uuid, invoice_uuid,
    статус, tx) в Allure-отчёт и в лог — для сверки на фронте и в админке.
    """
    import logging

    import allure
    from services.payment.payment_flow import PaymentFlow

    flow = PaymentFlow(environment=payment_env)
    yield flow

    s = flow.session
    lines = [
        f"environment:     {payment_env}",
        f"email:           {s.email}",
        f"password:        {s.password}",
        f"member_id:       {s.member_id}",
        f"membership_uuid: {s.membership_uuid}",
        f"member_status:   {s.member_status}",
        f"invoice_uuid:    {s.invoice_uuid}",
        f"price:           {getattr(s.price, 'membership_id', '')} "
        f"pi={getattr(s.price, 'epoch_pi_code', '')} "
        f"{getattr(s.price, 'amount', '')} {getattr(s.price, 'currency', '')}",
    ]
    if s.is_bundle or s.is_self_separate:
        lines.append(f"bundle:          slaves={list(s.bundle_slave_picodes.keys())} self={s.is_self_separate}")
    if s.is_self_separate:
        lines.append(f"token:           member_id={s.token_member_id} pi={s.token_pi_code} "
                     f"addId={s.additional_subscription_id} amount={s.token_amount}")
    lines.append("--- транзакции (для сверки в админке) ---")
    lines.extend(f"  {i+1}. {t}" for i, t in enumerate(s.tx_log))
    summary = "\n".join(lines) + "\n"
    logging.getLogger("payment").info("Сводка сессии:\n%s", summary)
    try:
        allure.attach(summary, name="Payment session", attachment_type=allure.attachment_type.TEXT)
    except Exception:
        pass  # отчёт отключён через --no-allure


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
