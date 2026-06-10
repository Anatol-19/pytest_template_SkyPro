"""Юзер-сценарии платёжного флоу VRP (Epoch, мы master).

Каждая цепочка тестовой оплаты завершается хвостом Cancel → Refund
(lifetime — только Refund). Самосепарат чистит и master, и токен.

Запуск (1 full-run):
  pytest -m payment --environment=VRP_STAGE -v

Бэклог (см. ai/PAYMENT_CASES_MATRIX.md): Sale Events, Layer 01 Tariffs, re-join,
standalone-токены, Dynamic Pricing, бандлы-slave/cross-sale, бандлы с токенами, Segpay.
"""

import allure
import pytest

from services.payment.payment_client import PaymentError


@allure.feature("Payment")
@pytest.mark.payment
class TestUserJoins:
    """Покупки (мы master). Реальные тарифы прайс-группы + бандлы/самосепарат."""

    @allure.story("Join recurring")
    @allure.title("Покупка ({tab}) + rebill → Cancel→Refund")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("tab", ["monthly", "yearly"])
    def test_join_recurring(self, payment_flow, tab):
        payment_flow.select_tariff(tab=tab)
        payment_flow.standard_join()
        payment_flow.login()
        assert payment_flow.refresh_dashboard().get("status"), "мембер должен быть активен"
        payment_flow.rebill()
        payment_flow.finalize()  # Cancel → Refund

    @allure.story("Join lifetime")
    @allure.title("Покупка lifetime (O) → Refund")
    @allure.severity(allure.severity_level.NORMAL)
    def test_join_lifetime(self, payment_flow):
        payment_flow.select_tariff(tab="lifetime")
        payment_flow.lifetime_join()
        payment_flow.login()
        assert payment_flow.refresh_dashboard().get("status")
        payment_flow.finalize(cancel=False)  # lifetime нереккурент → только Refund

    @allure.story("Join bundle / self (master)")
    @allure.title("Бандл/самосепарат event={event} + rebill → Cancel→Refund")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("event,min_slaves,is_self", [
        ("mono", 1, False),   # 1 slave
        ("bundle", 2, False),  # 2 slave
        ("super", 3, False),   # super (4 slave)
        ("self", 0, True),     # самосепарат (токен)
        ("ss", 1, True),       # self + slave
        ("sos", 3, True),      # super + self
    ])
    def test_join_bundle(self, payment_flow, event, min_slaves, is_self):
        payment_flow.select_tariff(event=event, bundle=True)
        s = payment_flow.session
        assert len(s.slave_uuids) >= min_slaves, f"ожидали ≥{min_slaves} slave для {event}"
        assert s.is_self_separate is is_self
        if is_self:
            assert s.additional_subscription_id is not None, "self → additionalSubscriptionId обязателен"
        payment_flow.bundle_join()
        payment_flow.login()
        assert payment_flow.refresh_dashboard().get("status")
        payment_flow.rebill()
        payment_flow.finalize()  # Cancel→Refund (master + токен при self)


@allure.feature("Payment")
@pytest.mark.payment
class TestUserChanges:
    """Изменения подписки (Flexgrade). База — простой месячный мембер. Хвост Cancel→Refund."""

    @allure.story("Change membership")
    @allure.title("{kind} (Flexgrade) + rebill → Cancel→Refund")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("kind", ["upgrade", "downgrade"])
    def test_change_and_rebill(self, payment_flow, kind):
        payment_flow.select_tariff(tab="monthly")
        payment_flow.standard_join()
        payment_flow.login()
        payment_flow.refresh_dashboard()
        try:
            if kind == "upgrade":
                payment_flow.upgrade()
            else:
                payment_flow.easy_cancel_downgrade()
        except PaymentError as exc:
            pytest.skip(f"{kind} недоступен на контуре: {exc}")
        payment_flow.rebill()
        payment_flow.finalize()  # Cancel→Refund


@allure.feature("Payment")
@allure.story("Backlog — Sale Events / re-join")
@pytest.mark.payment
class TestExpiredMember:
    """Re-join истёкшего мембера — часть функционала Sale Events. БЭКЛОГ."""

    @pytest.mark.skip(reason="Бэклог: требует Sale Events + фикстуру expired-мембера")
    def test_rejoin_inactive(self, payment_flow):
        payment_flow.select_tariff()
        payment_flow.rejoin_inactive()
        payment_flow.login()
        payment_flow.refresh_dashboard()
        payment_flow.rebill()
        payment_flow.finalize()
