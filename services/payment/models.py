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

    # После Auth + Dashboard
    atoken: str = ""
    rtoken: str = ""
    membership_uuid: str = ""
    member_status: str = ""

    # Активный тариф (может смениться после upgrade) — для DataPlus [N]
    active_pi_code: str = ""
    active_amount: str = ""
    active_currency: str = "USD"

    # Бандл
    is_bundle: bool = False
    bundle_slave_picodes: dict = field(default_factory=dict)  # {slug: epoch_pi_code}
