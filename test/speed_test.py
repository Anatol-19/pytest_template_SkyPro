import pytest
from services.lighthouse.pagespeed_service import SpeedtestService

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "services", "lighthouse", "configs")

@pytest.fixture
def speedtest_service():
    """Фикстура для создания экземпляра SpeedtestService."""
    return SpeedtestService()


@pytest.fixture(params=["desktop", "mobile"])
def device_config(request):
    """
    Фикстура для загрузки конфигурации в зависимости от режима (desktop или mobile).
    """
    config_file = os.path.join(CONFIG_DIR, f"config_{request.param}.json")
    with open(config_file, "r", encoding="utf-8") as file:
        return json.load(file)

@pytest.mark.performance
def test_run_local_single_route_iterations(speedtest_service):
    """Тест: запуск локального Lighthouse для одного роута с назначаемым количеством итераций."""
    route_keys = ['home']
    device = 'desktop'
    iteration_counts = 3

    speedtest_service.run_local_tests(route_keys, device, iteration_counts)


@pytest.mark.performance
def test_run_local_single_route_mobile(speedtest_service):
    """Тест: запуск локального Lighthouse для одного роута на мобильном устройстве."""
    route_keys = ['home']
    device = 'mobile'
    iteration_count = 2  # Пример: 2 итерации

    speedtest_service.run_local_tests(route_keys, device, iteration_count)


@pytest.mark.performance
def test_run_remote_single_route(speedtest_service):
    """Тест: запуск удалённого Lighthouse API для одного роута."""
    route_keys = ['home']
    device = 'desktop'

    speedtest_service.run_api_tests(route_keys, device)


@pytest.mark.performance
def test_run_local_multiple_routes(speedtest_service):
    """Тест: запуск локального Lighthouse для списка роутов."""
    route_keys = ['home', 'login', 'categories']
    device = 'desktop'
    iteration_count = 3  # Пример: 3 итерации

    speedtest_service.run_local_tests(route_keys, device, iteration_count)


@pytest.mark.performance
def test_run_remote_multiple_routes(speedtest_service):
    """Тест: запуск удалённого Lighthouse API для списка роутов."""
    route_keys = ['home', 'login', 'categories']
    device = 'mobile'

    speedtest_service.run_api_tests(route_keys, device)


@pytest.mark.performance
def test_lighthouse_with_config(config):
    """
    Тест запуска Lighthouse с использованием предустановленных конфигов.
    """
    service = SpeedtestService()
    route_keys = ["home"]  # Пример роута
    device_type = config["device_type"]
    iterations = 2  # Количество итераций

    service.run_local_tests(route_keys, device_type, iterations)