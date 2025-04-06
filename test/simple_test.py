from helper.StartSession import StartSession
from POM.AuthPage import AuthPage
import pytest


@pytest.fixture
def gui_service():
    session = StartSession()
    session.start_browser()
    yield session
    # Закрытие браузера после теста
    session.close_browser()

@pytest.mark.functional
def test_login(gui_service):
    auth_page = AuthPage(session)
    auth_page.go()
    auth_page.login_as("kiseleow.anatol@yandex.ru", "8ph-Ui3-2ap-HxA")
    auth_page.check_login_success()
    pass
