import pytest
from services.lighthouse.pagespeed_service import SpeedtestService

# 📌 Один роут — минимально, чтобы убедиться в работоспособности
ROUTES = ["home"]

@pytest.fixture(scope="module")
def service():
    """Фикстура: экземпляр сервиса на весь модуль."""
    return SpeedtestService()


@pytest.mark.performance
@pytest.mark.parametrize("device", ["desktop", "mobile"])
def test_run_local_cli(service, device):
    """Проверка локального запуска Lighthouse CLI."""
    service.run_local_tests(ROUTES, device, n_iteration=1)


@pytest.mark.performance
@pytest.mark.parametrize("device", ["desktop", "mobile"])
def test_run_api(service, device):
    """Проверка запуска Lighthouse через API."""
    service.run_api_aggregated_tests(ROUTES, device, n_iteration=1)


@pytest.mark.performance
@pytest.mark.parametrize("device", ["desktop", "mobile"])
def test_run_crux(service, device):
    """Проверка сбора CrUX данных."""
    service.run_crux_data_collection(ROUTES, device)
