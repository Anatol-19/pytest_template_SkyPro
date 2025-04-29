import pytest
from services.lighthouse.pagespeed_service import SpeedtestService

# 📌 Один роут для тестов
DEFAULT_ROUTES = ["home"]

@pytest.fixture(scope="module")
def service():
    """Создание экземпляра сервиса на весь модуль."""
    return SpeedtestService()

@pytest.mark.performance
@pytest.mark.parametrize("device", ["desktop", "mobile"])
def test_run_local_with_config(service, device):
    """
    Тест: локальный запуск с чтением параметров из config.ini (BASE_URL) и routes.ini.
    """
    service.run_local_tests(None, device, n_iteration=1)  # None → берётся из конфигов

@pytest.mark.performance
@pytest.mark.parametrize("device", ["desktop", "mobile"])
def test_run_local_manual_routes(service, device):
    """
    Тест: локальный запуск с передачей маршрутов напрямую.
    """
    service.run_local_tests(route_keys=DEFAULT_ROUTES, device_type=device, n_iteration=1, base_url="https://www.vrsmash.com")

@pytest.mark.performance
@pytest.mark.parametrize("device", ["desktop", "mobile"])
def test_run_api_with_config(service, device):
    """
    Тест: удалённый запуск через API — с параметрами по умолчанию (из .ini).
    """
    service.run_api_aggregated_tests(route_keys=None, device_type=device, n_iteration=1)

@pytest.mark.performance
@pytest.mark.parametrize("device", ["desktop", "mobile"])
def test_run_api_manual_routes(service, device):
    """
    Тест: удалённый запуск через API с ручными роутами.
    """
    service.run_api_aggregated_tests(route_keys=DEFAULT_ROUTES, device_type=device, n_iteration=1)

@pytest.mark.performance
@pytest.mark.parametrize("device", ["desktop", "mobile"])
def test_run_crux_with_config(service, device):
    """
    Тест: CrUX с параметрами из config.ini.
    """
    service.run_crux_data_collection(route_keys=None, device_type=device)

@pytest.mark.performance
@pytest.mark.parametrize("device", ["desktop", "mobile"])
def test_run_crux_manual_routes(service, device):
    """
    Тест: CrUX запуск с передачей роутов напрямую.
    """
    service.run_crux_data_collection(route_keys=DEFAULT_ROUTES, device_type=device)
