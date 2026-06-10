"""Датаклассы платёжного флоу VRP."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TariffPrice:
    """Тариф, выбранный из ответа /memberships/prices."""

    membership_id: str          # = subscr_id при создании Payment URL
    epoch_pi_code: str
    amount: str                 # money(trial_price ?? price ?? rebill_price)
    currency: str = "USD"
    category: str = "standard"  # standard | bundle | ...
    tab: str = "monthly"        # monthly | yearly | lifetime
    raw: dict = field(default_factory=dict)


@dataclass
class PaymentResult:
    """Результат Create Payment URL."""

    payment_url: str
    invoice_uuid: str
    user_uuid: str
    is_dynamic_url: bool = False   # True = новый join-формат (бандл), False = старый query-формат


@dataclass
class PaymentSession:
    """Состояние, накапливаемое по ходу платёжного сценария.

    Заполняется пошагово: после выбора тарифа, создания URL, FlexPost, авторизации и т.д.
    """

    email: str
    password: str

    # После выбора тарифа (Layer 01)
    price: Optional[TariffPrice] = None

    # После Create Payment URL
    invoice_uuid: str = ""
    user_uuid: str = ""

    # После FlexPost [M]
    member_id: str = ""
    transaction_id: str = ""
    initial_transaction_id: str = ""
    last_dataplus_id: str = ""
    session_id: str = ""          # session_id мастер-FlexPost (токен переиспользует тот же)

    # После Auth + Dashboard
    atoken: str = ""
    rtoken: str = ""
    membership_uuid: str = ""
    member_status: str = ""

    # Активный тариф (может смениться после upgrade) — для DataPlus [N]
    active_pi_code: str = ""
    active_amount: str = ""
    active_currency: str = "USD"

    # Журнал отправленных транзакций (для отчёта/сверки в админке)
    tx_log: list = field(default_factory=list)

    # Бандл (slave-сайты)
    is_bundle: bool = False
    slave_uuids: list = field(default_factory=list)            # → slavePriceUuids
    bundle_slave_picodes: dict = field(default_factory=dict)   # {slug: epoch_pi_code} → x_bundle_slave_{slug}

    # Самосепарат (рекуррентный токен на «своём» сайте)
    is_self_separate: bool = False
    additional_subscription_id: Optional[int] = None           # → additionalSubscriptionId (integer special_prices[0].id)
    token_pi_code: str = ""                                     # special_prices[0].epochPiCode
    token_amount: str = ""                                      # special_prices[0].priceAmount/rebillPrice
    token_currency: str = "USD"
    token_member_id: str = ""                                   # обычно master member_id + 1
    token_transaction_id: str = ""
    token_initial_transaction_id: str = ""
    token_last_dataplus_id: str = ""
