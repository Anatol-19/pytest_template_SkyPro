"""Константы Segpay для тестовых транзакций (sync-handler/segpay).

Подход: запрашиваем get-recurring-payment-url (module=segpay) → берём invoiceId/eticketid/pplist
из ответа, остальное — фиксированные тестовые значения. Многие поля чужой коллекции схлопываются
в наши (paymentaccountid ≈ invoice). merchantid/urlid/postbackconfiguniqueid — из коллекции,
правятся по ошибкам бэка при необходимости.
"""

# Идентификаторы мерчанта (из коллекции смежного проекта — уточнить/править по ошибкам бэка)
MERCHANT_ID = "22186"
URL_ID = "691365"
POSTBACK_CONFIG_UNIQUE_ID = "39632"

# Карта/биллинг — тестовые дефолты
CC_FIRST6 = "999999"
CC_LAST4 = "9999"
CC_BIN_COUNTRY = "US"
CARD_TYPE = "Visa"
PREPAID_INDICATOR = "N"
PAYMENT_TYPE = "CreditCard"
BILL_ZIP = "33060"
BILL_COUNTRY = "US"
BILL_NAME = "QA Tester"
BILL_NAME_FIRST = "QA"
BILL_NAME_LAST = "Tester"
IP_ADDRESS = "255.255.255.255"
IP_COUNTRY = "US"
MERCHANT_NAME = "Swearl, LLC"

# Длительности (дни) — i=initial, r=rebill
INITIAL_INTERVAL = "30"
REBILL_INTERVAL = "30"

# Reason-коды Segpay (публичная дока): 826 = Other
CANCEL_REASON_CODE = "826"
REFUND_REASON_CODE = "826"

DESC = "QA Test SegPay"
