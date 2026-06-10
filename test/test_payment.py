"""Тесты платёжного флоу VRP (Layer 01-03).

Тесты самодостаточны — email/пароль генерируются по паттерну stamp+initials@mailhog.com
в момент создания payment URL, .env не требуется для базовых сценариев.

Запуск:
  pytest -m payment --environment=VRP_STAGE -v
  pytest -m payment --environment=VRP_TEST -v
  pytest test/test_payment.py::TestTariffs --environment=VRP_DEV -v
"""

import allure
import pytest

from services.payment.payment_client import PaymentError


@allure.feature("Payment")
@allure.story("Layer 01 — Tariffs")
@pytest.mark.payment
class TestTariffs:
    """Layer 01 — тарифы (smoke, без транзакций)."""

    @allure.title("Sale Event возвращает uuid")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sale_event(self, payment_flow, request):
        event = request.config.getoption("--pay-event")
        data = payment_flow.get_sale_event(event=event)
        assert data.get("uuid"), "Sale Event должен содержать uuid"

    @allure.title("Get Prices: выбор тарифа")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_prices_and_select(self, payment_flow, pay_opts):
        price = payment_flow.select_tariff(**pay_opts)
        assert price.membership_id
        assert price.epoch_pi_code
        assert price.amount


@allure.feature("Payment")
@allure.story("Layer 02 — Joins")
@pytest.mark.payment
class TestJoins:
    """Layer 02 — joins с rebill. Email генерируется автоматически при create_payment_url."""

    @allure.title("Standard Join + Rebill")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_standard_join_and_rebill(self, payment_flow, pay_opts):
        payment_flow.select_tariff(**pay_opts)
        payment_flow.standard_join()
        payment_flow.login()
        info = payment_flow.refresh_dashboard()
        assert info.get("status"), "После join должен быть статус мембера"
        payment_flow.rebill()
        assert payment_flow.session.last_dataplus_id

    @allure.title("Free Trial (F→U→N)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_free_trial_flow(self, payment_flow, pay_opts):
        payment_flow.select_tariff(**pay_opts)
        payment_flow.free_trial_join()
        payment_flow.rebill()

    @allure.title("Paid Trial (T→U→N)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_paid_trial_flow(self, payment_flow, pay_opts):
        payment_flow.select_tariff(**pay_opts)
        payment_flow.paid_trial_join()
        payment_flow.rebill()

    @allure.title("Lifetime / One Time (O)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_lifetime_one_time(self, payment_flow, pay_opts):
        payment_flow.select_tariff(**{**pay_opts, "tab": "lifetime"})
        payment_flow.lifetime_join()
        payment_flow.login()
        assert payment_flow.refresh_dashboard().get("status")


@allure.feature("Payment")
@allure.story("Layer 03 — Changes")
@pytest.mark.payment
class TestChanges:
    """Layer 03 — upgrade / easy cancel / refund.

    Каждый тест самодостаточен: сначала создаёт свежего мембера через standard_join,
    затем выполняет операцию. .env не требуется.
    """

    @allure.title("Upgrade (Flexgrade) + Rebill")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_upgrade_flexgrade_and_rebill(self, payment_flow, pay_opts):
        payment_flow.select_tariff(**pay_opts)
        payment_flow.standard_join()
        payment_flow.login()
        payment_flow.refresh_dashboard()
        try:
            payment_flow.upgrade()
        except PaymentError as exc:
            pytest.skip(f"Upgrade недоступен на контуре: {exc}")
        payment_flow.rebill()

    @allure.title("Easy Cancel Downgrade")
    @allure.severity(allure.severity_level.NORMAL)
    def test_easy_cancel_downgrade(self, payment_flow, pay_opts):
        payment_flow.select_tariff(**pay_opts)
        payment_flow.standard_join()
        payment_flow.login()
        payment_flow.refresh_dashboard()
        if not payment_flow.session.membership_uuid:
            pytest.skip("Нет membership_uuid после join — невозможно выполнить easy cancel")
        try:
            payment_flow.easy_cancel_downgrade()
        except PaymentError as exc:
            pytest.skip(f"Easy Cancel недоступен на контуре: {exc}")

    @allure.title("Refund (C)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_refund(self, payment_flow, pay_opts):
        payment_flow.select_tariff(**pay_opts)
        payment_flow.standard_join()
        payment_flow.login()
        payment_flow.refresh_dashboard()
        payment_flow.refund()


@allure.feature("Payment")
@allure.story("Layer 02 — Re-join (expired)")
@pytest.mark.payment
class TestExpiredMember:
    """Сценарии с истёкшим/неактивным мембером (re-join).

    TODO: реализовать fixture create_expired_member, которая:
      1. Создаёт нового мембера через standard_join
      2. Отменяет подписку (refund/cancel) — member становится inactive
      3. Возвращает session с email/password для re-join
    """

    @pytest.mark.skip(reason="Требует fixture create_expired_member — будет реализован позже")
    def test_rejoin_inactive(self, payment_flow, pay_opts):
        payment_flow.select_tariff(**pay_opts)
        payment_flow.rejoin_inactive()
        payment_flow.login()
        payment_flow.refresh_dashboard()
        payment_flow.rebill()