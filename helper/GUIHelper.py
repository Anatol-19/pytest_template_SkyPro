import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from helper.StartSession import StartSession

# Настройка логирования
logger = logging.getLogger(__name__)


def check_element_properties(element, expected_properties: dict):
    """Проверка свойств элемента."""
    try:
        for prop, expected_value in expected_properties.items():
            actual_value = element.value_of_css_property(prop)
            assert actual_value == expected_value, f"Свойство {prop} не совпадает: ожидаемое {expected_value}, фактическое {actual_value}"
        logger.info("Свойства элемента проверены и совпадают.")
    except Exception as e:
        logger.error(f"Ошибка при проверке свойств элемента: {e}")
        raise


def check_element_size(element):
    """Проверка реальных размеров элемента."""
    try:
        size = element.size
        logger.info(f"Размер элемента: {size}")
        return size
    except Exception as e:
        logger.error(f"Ошибка при получении размера элемента: {e}")
        raise


def check_distance_between_elements(element1, element2, expected_distance):
    """Проверка расстояния между двумя элементами."""
    try:
        location1 = element1.location
        location2 = element2.location
        distance = ((location1['x'] - location2['x']) ** 2 + (location1['y'] - location2['y']) ** 2) ** 0.5
        assert distance == expected_distance, f"Расстояние между элементами не совпадает: ожидаемое {expected_distance}, фактическое {distance}"
        logger.info("Расстояние между элементами проверено и совпадает.")
    except Exception as e:
        logger.error(f"Ошибка при проверке расстояния между элементами: {e}")
        raise


class GUIHelper(StartSession):
    def __init__(self, driver: WebDriver):
        super().__init__()
        self.driver = driver

    def find_element_by_css(self, value: str):
        """Поиск элемента по CSS селектору."""
        try:
            element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, value)))
            logger.info(f"Элемент найден по CSS: {value}")
            return element
        except Exception as e:
            logger.error(f"Ошибка при поиске элемента по CSS: {value} - {e}")
            raise

    def find_element_by_xpath(self, value: str):
        """Поиск элемента по XPATH."""
        try:
            element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, value)))
            logger.info(f"Элемент найден по XPATH: {value}")
            return element
        except Exception as e:
            logger.error(f"Ошибка при поиске элемента по XPATH: {value} - {e}")
            raise

    def interact_with_element(self, element, action: str, value=None):
        """Универсальный метод взаимодействия с элементом."""
        try:
            if action == 'click':
                element.click()
                logger.info("Элемент кликнут.")
            elif action == 'send_keys':
                element.send_keys(value)
                logger.info(f"Отправлены значения: {value}")
            elif action == 'hover':
                # TODO: Реализовать ховер
                logger.info("Ховер на элемент.")
            elif action == 'scroll':
                self.driver.execute_script("arguments[0].scrollIntoView();", element)
                logger.info("Прокрутка к элементу.")
            else:
                logger.error(f"Неизвестное действие: {action}")
                raise ValueError(f"Неизвестное действие: {action}")
        except Exception as e:
            logger.error(f"Ошибка при взаимодействии с элементом: {e}")
            raise
