import pytest
from services.lighthouse.pagespeed_service import SpeedtestService

ROUTES = ["home"]

@pytest.fixture(scope="module")
def service():
    return SpeedtestService()

@pytest.mark.performance
@pytest.mark.parametrize("device", ["desktop", "mobile"])
def test_run_cli(service, device):
    """Lighthouse CLI: локальный запуск."""
    service.run_local_tests(ROUTES, device, n_iteration=10)

@pytest.mark.performance
@pytest.mark.parametrize("device", ["desktop", "mobile"])
def test_run_api(service, device):
    """Lighthouse API: запуск через Google API."""
    service.run_api_aggregated_tests(ROUTES, device, n_iteration=10)

@pytest.mark.performance
@pytest.mark.parametrize("device", ["desktop", "mobile"])
def test_run_crux(service, device):
    """CrUX: сбор 28-дневных пользовательских метрик."""
    service.run_crux_data_collection(ROUTES, device)
