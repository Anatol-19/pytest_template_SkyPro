import pytest
from Services.lighthouse.pagespeed_service import SpeedtestService
from Services.lighthouse.config_lighthouse import get_base_url, get_route

@pytest.fixture
def speedtest_service():
    """Фикстура для создания экземпляра SpeedtestService."""
    service = SpeedtestService()
    return service


@pytest.mark.performance
def test_run_speedtest(speedtest_service):
    """Тест для проверки работы метода run_speedtest."""
    for route_name in ['home', 'all']:
        url = get_base_url() + get_route(route_name)  # Получаем полный URL
        for iteration in range(1, 3):  # Пример: 2 итерации
            results = speedtest_service.run_speedtest(url, iteration)
            print(results)
            assert results is not None  # Проверяем, что результаты не None
            assert isinstance(results, dict)  # Проверяем, что результаты - это словарь
            # Добавьте дополнительные проверки для конкретных метрик, если необходимо
