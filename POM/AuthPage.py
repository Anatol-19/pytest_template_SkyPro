from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

class AuthPage:

    def __init__(self, driver) -> None:
        self.__url = "https://app.striveapp.ru/login"
        self.__driver = driver

    def go(self):
        self.__driver.get(self.__url)

    def login_as(self, email: str, password: str):
        self.__driver.find_element(By.CSS_SELECTOR, "").send_keys(email)
