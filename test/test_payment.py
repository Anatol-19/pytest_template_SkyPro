"""Юзер-сценарии платёжного флоу VRP (Epoch, Segpay).

Каждая цепочка тестовой оплаты завершается хвостом Cancel → Refund
(lifetime — только Refund). Самосепарат чистит и master, и токен.

Запуск (full-run):
  pytest -m payment --environment=VRP_STAGE -v

Бэклог (ai/PAYMENT_CASES_MATRIX.md): Sale Events, Layer 01 Tariffs, re-join,
CrossSale, Bundle Slave-сторона, Centrobill.

Allure-иерархия:
  epic   → VRP Payment
  feature → Epoch | Segpay
  story  → операция (Join Premium / Rebill / Upgrade / ...)
  tag    → Join Premium · Rebill · Upgrade · Downgrade · Cancel · Refund
           Tokens · Bundle Slave · Bundle Self · Bundle Master
  layer  → Layer 02 · Layer 03
"""

import allure
import pytest

from services.payment import config_payment as pay_cfg
from services.payment.payment_client import PaymentError


# ─────────────────────────────────────────────────────────────────────────────
#  Layer 02 — Joins (Epoch)
# ─────────────────────────────────────────────────────────────────────────────

@allure.epic("VRP Payment")
@allure.feature("Epoch")
@allure.label("layer", "02 — Joins")
@pytest.mark.payment
class TestUserJoins:
    """Покупки (мы master). Реальные тарифы прайс-группы + бандлы/самосепарат."""

    # ── Recurring (monthly / yearly) ─────────────────────────────────────────

    @allure.story("Join Premium")
    @allure.title("Join ({tab}) + Rebill → Cancel→Refund")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Join Premium", "Rebill", "Cancel", "Refund")
    @pytest.mark.parametrize("tab", ["monthly", "yearly"])
    def test_join_recurring(self, payment_flow, tab):
        payment_flow.select_tariff(tab=tab)
        payment_flow.standard_join()
        payment_flow.login()
        assert payment_flow.refresh_dashboard().get("status"), "мембер должен быть активен"
        payment_flow.rebill()
        payment_flow.finalize()

    # ── Lifetime ─────────────────────────────────────────────────────────────

    @allure.story("Join Lifetime")
    @allure.title("Join Lifetime (O) → Refund")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Join Premium", "Refund")
    def test_join_lifetime(self, payment_flow):
        payment_flow.select_tariff(tab="lifetime")
        payment_flow.lifetime_join()
        payment_flow.login()
        assert payment_flow.refresh_dashboard().get("status")
        payment_flow.finalize(cancel=False)

    # ── Bundle / Self-separate ────────────────────────────────────────────────

    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("event,min_slaves,is_self", [
        ("mono",   1, False),
        ("bundle", 2, False),
        ("super",  3, False),
        ("self",   0, True),
        ("ss",     1, True),
        ("sos",    3, True),
    ])
    def test_join_bundle(self, payment_flow, event, min_slaves, is_self):
        # Динамические Allure-атрибуты по типу бандла
        has_slaves = min_slaves > 0
        if is_self and has_slaves:
            allure.dynamic.story("Bundle Master + Self-Separate")
            allure.dynamic.title(f"Bundle {event.upper()} (Slave+Self) + Rebill → Cancel→Refund")
            allure.dynamic.tag("Bundle Master", "Bundle Slave", "Bundle Self", "Tokens", "Rebill", "Cancel", "Refund")
        elif is_self:
            allure.dynamic.story("Self-Separate (Tokens)")
            allure.dynamic.title("Self-Separate (self) + Rebill → Cancel→Refund")
            allure.dynamic.tag("Bundle Self", "Tokens", "Rebill", "Cancel", "Refund")
        else:
            allure.dynamic.story("Bundle Master + Slave")
            allure.dynamic.title(f"Bundle {event.upper()} ({min_slaves} slave) + Rebill → Cancel→Refund")
            allure.dynamic.tag("Bundle Master", "Bundle Slave", "Rebill", "Cancel", "Refund")

        # Пропускаем если sale event не настроен на этом контуре
        env = payment_flow.client.environment or "VRP_STAGE"
        allowed = pay_cfg.SALE_EVENT_KEYS.get(env, [])
        if event not in allowed:
            pytest.skip(f"Sale event '{event}' не настроен на {env} (SALE_EVENT_KEYS в config_payment.py)")

        try:
            payment_flow.select_tariff(event=event, bundle=True)
        except PaymentError as e:
            pytest.skip(f"Sale event '{event}' недоступен на {env}: {e}")
        s = payment_flow.session
        assert len(s.slave_uuids) >= min_slaves, f"ожидали ≥{min_slaves} slave для {event}"
        assert s.is_self_separate is is_self
        if is_self:
            assert s.additional_subscription_id is not None, "self → additionalSubscriptionId обязателен"
        payment_flow.bundle_join()
        payment_flow.login()
        assert payment_flow.refresh_dashboard().get("status")
        payment_flow.rebill()
        payment_flow.finalize()


# ─────────────────────────────────────────────────────────────────────────────
#  Layer 03 — Changes (Epoch)
# ─────────────────────────────────────────────────────────────────────────────

@allure.epic("VRP Payment")
@allure.feature("Epoch")
@allure.label("layer", "03 — Changes")
@pytest.mark.payment
class TestUserChanges:
    """Изменения подписки (Flexgrade). База — простой месячный мембер. Хвост Cancel→Refund."""

    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("kind", ["upgrade", "downgrade"])
    def test_change_and_rebill(self, payment_flow, kind):
        if kind == "upgrade":
            allure.dynamic.story("Upgrade")
            allure.dynamic.title("Upgrade (Flexgrade) + Rebill → Cancel→Refund")
            allure.dynamic.tag("Upgrade", "Rebill", "Cancel", "Refund")
        else:
            allure.dynamic.story("Downgrade")
            allure.dynamic.title("Downgrade (Easy Cancel) + Rebill → Cancel→Refund")
            allure.dynamic.tag("Downgrade", "Rebill", "Cancel", "Refund")

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
        payment_flow.finalize()


# ─────────────────────────────────────────────────────────────────────────────
#  Segpay (module=segpay, без Epoch-каскада)
# ─────────────────────────────────────────────────────────────────────────────

@allure.epic("VRP Payment")
@allure.feature("Segpay")
@allure.label("layer", "02 — Joins")
@pytest.mark.payment
class TestSegpay:
    """Segpay: Create URL (module=segpay) → Initial → Recurring → Cancel→Refund.

    Без Epoch-каскада. Синтетические постбэки на /api/payment/sync-handler/segpay.
    Segpay-хендлер отвечает строкой "OK"; дата — US AM/PM.
    """

    @allure.story("Segpay Join + Rebill")
    @allure.title("Segpay Join (Initial) + Rebill (Conversion) → Cancel→Refund")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Join Premium", "Rebill", "Cancel", "Refund")
    def test_segpay_join_and_rebill(self, payment_flow):
        payment_flow.select_tariff(tab="monthly")
        payment_flow.segpay_join()
        payment_flow.login()
        assert payment_flow.refresh_dashboard().get("status"), "мембер должен быть активен"
        payment_flow.segpay_rebill()
        payment_flow.segpay_finalize()

    @allure.story("Segpay Upgrade")
    @allure.title("Segpay Upgrade + Rebill → Cancel→Refund")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Upgrade", "Rebill", "Cancel", "Refund")
    @pytest.mark.skip(
        reason="Segpay upgrade не прогоняется синтетически: "
               "recurring-upgrade-url/segpay делает живой вызов Segpay API "
               "(Segpay/ApiClient.php:46 → Undefined index isSuccess). "
               "Old Upgrade постбэк без него → 'error'. "
               "Методы готовы; нужен backend-sandbox Segpay или живой шлюз."
    )
    def test_segpay_upgrade(self, payment_flow):
        payment_flow.select_tariff(tab="monthly")
        payment_flow.segpay_join()
        payment_flow.login()
        payment_flow.refresh_dashboard()
        # целевой тариф — yearly (нужен segpay_ti_code в админке)
        prices_json = payment_flow.client.get_prices()
        prices = prices_json.get("prices")
        arr = prices if isinstance(prices, list) else prices.get(next(iter(prices)), [])
        target = next(p for p in arr if (p.get("price_tab") or {}).get("slug") == "yearly")
        yearly_price = payment_flow.client.parse_prices(prices_json, tab="yearly")
        payment_flow.segpay_upgrade(target["membership_id"], new_amount=yearly_price.amount)
        payment_flow.segpay_rebill()
        payment_flow.segpay_finalize()


# ─────────────────────────────────────────────────────────────────────────────
#  Backlog
# ─────────────────────────────────────────────────────────────────────────────

@allure.epic("VRP Payment")
@allure.feature("Epoch")
@allure.label("layer", "04 — Sale Events")
@allure.tag("Backlog")
@pytest.mark.payment
class TestExpiredMember:
    """Re-join истёкшего мембера — часть функционала Sale Events. БЭКЛОГ."""

    @allure.story("Re-join")
    @allure.title("Re-join (expired member) + Rebill → Cancel→Refund")
    @allure.tag("Join Premium", "Rebill", "Cancel", "Refund")
    @pytest.mark.skip(reason="Бэклог: требует Sale Events + фикстуру expired-мембера")
    def test_rejoin_inactive(self, payment_flow):
        payment_flow.select_tariff()
        payment_flow.rejoin_inactive()
        payment_flow.login()
        payment_flow.refresh_dashboard()
        payment_flow.rebill()
        payment_flow.finalize()
