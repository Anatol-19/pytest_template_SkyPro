"""Константы платёжного флоу (значения из Postman-коллекции / run_env.json).

Это не секреты — публичные тестовые константы Epoch sandbox. Реальные учётки в .env.
"""

# Адресные / профильные константы тестового пользователя
ZIP = "91780"
IPADDR = "162.251.108.36"
IPADDR_REFUND = "195.135.215.247"
FIRSTNAME = "QA"
LASTNAME = "Test"
COUNTRY = "US"

# Epoch-специфика
CO_CODE_FLEXPOST = "def"
CO_CODE_DATAPLUS = "VRP"
RESELLER = "qa_tester_19"
RESELLER_CODE = "a"
EPOCH_DIGEST = "b1bd4832368aa4b37c9037ff50c2e90a_qa"
MASTERCODE = "M-607039"
PAYMENT_TYPE = "CC"
DEFAULT_PST_TYPE = "MC"          # MC | VS — payment_subtype / ets_pst_type
SITE = "a"

# Флаг Dynamic Price для master-сайта в бандле (НЕ реальный PiCode)
MASTER_INVOICE_PRODUCT = "invoiceProduct158529"

# Маппинг хост сайта -> invoiceProduct{siteId} (флаг Dynamic Price)
INVOICE_PRODUCT_MAP = {
    "sg.vrporn.com": "invoiceProduct158529",
    "vrporn.com": "invoiceProduct158529",
    "d.vrporn.com": "invoiceProduct158529",
    "t.vrporn.com": "invoiceProduct158529",
    "vrbtrans.com": "invoiceProduct172644",
    "vrbangers.com": "invoiceProduct172642",
    "vrconk.com": "invoiceProduct177630",
    "blowvr.com": "invoiceProduct191525",
}

# Контуры VRP, на которых разрешён мульти-прогон по умолчанию (PROD исключён намеренно)
DEFAULT_CONTOURS = ["VRP_DEV", "VRP_TEST", "VRP_STAGE"]
ALL_CONTOURS = ["VRP_DEV", "VRP_TEST", "VRP_STAGE", "VRP_PROD"]

# Sale Event ключи, настроенные в админке по контурам.
# Обновлять вручную после изменений в админке.
# Тест пропускается (pytest.skip) если нужного ключа нет на контуре.
SALE_EVENT_KEYS: dict[str, list[str]] = {
    "VRP_DEV":   ["mono", "bundle", "super", "self", "ss", "sos"],
    "VRP_TEST":  ["mono", "bundle", "super", "self", "ss", "sos"],
    "VRP_STAGE": ["mono", "bundle", "super", "self", "ss", "sos"],
    "VRP_PROD":  ["ss"],  # DropCard SS подтверждён на проде 2026-06-11
}

# Хосты «своего» сайта (для self-separated: bundledSites отдаёт голый vrporn.com).
# Если bundled-хост входит сюда — это самосепарат (токен), а не slave-сайт.
SELF_HOSTS = {"vrporn.com", "sg.vrporn.com", "d.vrporn.com", "t.vrporn.com"}
