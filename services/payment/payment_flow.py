"""Оркестратор платёжных сценариев VRP (Layer 01-03).

PaymentFlow склеивает шаги PaymentClient в сквозные сценарии, накапливая состояние
в PaymentSession. Контур задаётся через environment.
"""

import logging
import os

from services.payment import epoch_payloads as payloads
from services.payment import fakes
from services.payment.models import PaymentSession, TariffPrice
from services.payment.payment_client import PaymentClient, PaymentError

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

logger = logging.getLogger(__name__)


class PaymentFlow:
    def __init__(self, environment=None, email=None, password=None):
        if load_dotenv:
            load_dotenv()
        self.client = PaymentClient(environment=environment)
        self.email = email or os.getenv("VRP_PAY_EMAIL")
        self.password = password or os.getenv("VRP_PAY_PASSWORD")
        self.session = PaymentSession(email=self.email, password=self.password)

    # ---------- Layer 01: тарифы ----------

    def get_sale_event(self, event="", event_id=""):
        data = self.client.get_sale_event(event=event, event_id=event_id)
        logger.info("Sale Event: uuid=%s group=%s", data.get("uuid"), data.get("saleEventGroup"))
        return data

    def select_tariff(self, tab="monthly", slot=None, event=None, bundle=False) -> TariffPrice:
        """Layer 01: выбрать тариф по периоду (tab); опц. спец-цены (slot) и бандл (event+bundle).

        tab    — monthly|yearly|lifetime (алиасы year/month/life).
        slot   — None=Standard; N=Special (type_prices_from_slot).
        event  — ключ sale event (?event=) — задаёт состав бандла (bundledSites).
        bundle — True: применить бандл/самосепарат из sale event. False (дефолт): простая покупка
                 ДЕФОЛТНЫМ методом, даже если в sale event есть бандл (требование).
        """
        event_id = ""
        bundled_hosts = []
        if event:
            se = self.get_sale_event(event=event)
            event_id = se.get("uuid", "")
            if bundle:
                bundled_hosts = [b.get("host") for b in se.get("bundledSites", []) if b.get("host")]

        prices_json = self.client.get_prices(slot=slot, event_id=event_id)
        price = self.client.parse_prices(prices_json, tab=tab)
        self.session.price = price
        self.session.active_pi_code = price.epoch_pi_code
        self.session.active_amount = price.amount
        self.session.active_currency = price.currency

        # Сброс bundle-состояния (важно для требования «простая покупка дефолтом»)
        self.session.is_bundle = False
        self.session.is_self_separate = False
        self.session.slave_uuids = []
        self.session.bundle_slave_picodes = {}
        self.session.additional_subscription_id = None

        if bundle and bundled_hosts:
            cfg = self.client.resolve_bundle(price, bundled_hosts)
            self.session.slave_uuids = cfg["slave_uuids"]
            self.session.bundle_slave_picodes = cfg["slave_picodes"]
            self.session.additional_subscription_id = cfg["additional_subscription_id"]
            self.session.is_self_separate = cfg["is_self_separate"]
            self.session.is_bundle = bool(cfg["slave_uuids"]) or cfg["is_self_separate"]
            tok = cfg["token"]
            if tok:
                self.session.token_pi_code = tok["pi_code"]
                self.session.token_amount = tok["amount"]
                self.session.token_currency = tok["currency"]

        logger.info("Выбран тариф: '%s' tab=%s prices=%s bundle=%s self=%s slaves=%s addId=%s | mid=%s pi=%s %s %s",
                    price.raw.get("name"), price.tab, ("special:%s" % slot) if slot else "standard",
                    self.session.is_bundle, self.session.is_self_separate,
                    list(self.session.bundle_slave_picodes.keys()), self.session.additional_subscription_id,
                    price.membership_id, price.epoch_pi_code, price.amount, price.currency)
        return price

    # ---------- Auth + state ----------

    def login(self):
        token = self.client.auth(self.session.email, self.session.password)
        self.session.atoken = token.get("atoken", "")
        self.session.rtoken = token.get("rtoken", "")
        logger.info("Авторизация выполнена")
        return token

    def refresh_dashboard(self) -> dict:
        info = self.client.dashboard_info()
        self.session.member_id = info.get("member_id") or self.session.member_id
        self.session.membership_uuid = info.get("membership_uuid", "")
        self.session.member_status = info.get("status", "")
        logger.info("Dashboard: status=%s membership_uuid=%s", self.session.member_status,
                    self.session.membership_uuid)
        return info

    # ---------- Epoch-шаги ----------

    def _flexpost(self):
        body = payloads.build_flexpost_body(self.session)
        self.client.epoch_sync_json(body)
        self.session.tx_log.append(
            f"FlexPost[M] master member_id={self.session.member_id} tx={self.session.transaction_id} pi={self.session.price.epoch_pi_code}")
        logger.info("FlexPost [M] ok: member_id=%s tx=%s", self.session.member_id,
                    self.session.transaction_id)

    def _dataplus(self, tx_type):
        form = payloads.build_dataplus_form(self.session, tx_type)
        self.client.epoch_sync_form(form, label=f"DataPlus[{tx_type}]")
        self.session.last_dataplus_id = self.session.transaction_id
        self.session.tx_log.append(
            f"DataPlus[{tx_type}] master member_id={self.session.member_id} tx={self.session.transaction_id}")
        logger.info("DataPlus [%s] ok: tx=%s", tx_type, self.session.transaction_id)

    def _create_url(self, exist=False):
        if exist:
            if not self.session.email or not self.session.password:
                raise PaymentError("Re-join требует VRP_PAY_EMAIL / VRP_PAY_PASSWORD в .env")
            result = self.client.create_payment_url_exist(
                self.session.email, self.session.password, self.session.price.membership_id)
        else:
            if not self.session.email:
                email = fakes.fake_email()
                self.session.email = email
                self.session.password = fakes.fake_password(email)
                logger.info("Сгенерированы fake-credentials: %s", email)
            result = self.client.create_payment_url(
                self.session.email, self.session.password, self.session.price.membership_id,
                slave_uuids=self.session.slave_uuids or None,
                additional_subscription_id=self.session.additional_subscription_id)
        self.session.invoice_uuid = result.invoice_uuid
        self.session.user_uuid = result.user_uuid
        logger.info("Create Payment URL ok: invoice=%s dynamic=%s", result.invoice_uuid,
                    result.is_dynamic_url)
        return result

    def _check_invoice(self):
        data = self.client.invoice_status(self.session.invoice_uuid)
        logger.info("Invoice Status: %s purchase_type=%s", data.get("status"),
                    data.get("purchase_type"))
        return data

    # ---------- Layer 02: joins ----------

    def standard_join(self):
        """L02/01: Create URL -> FlexPost -> Invoice -> DataPlus[I]."""
        self._create_url()
        self._flexpost()
        self._check_invoice()
        self._dataplus("I")
        return self.session

    def free_trial_join(self):
        """L02/02: ...FlexPost -> DataPlus[F] -> login -> dashboard -> DataPlus[U]."""
        self._create_url()
        self._flexpost()
        self._check_invoice()
        self._dataplus("F")
        self.login()
        self.refresh_dashboard()
        self._dataplus("U")
        return self.session

    def paid_trial_join(self):
        """L02/03: ...FlexPost -> DataPlus[T] -> login -> dashboard -> DataPlus[U]."""
        self._create_url()
        self._flexpost()
        self._check_invoice()
        self._dataplus("T")
        self.login()
        self.refresh_dashboard()
        self._dataplus("U")
        return self.session

    def lifetime_join(self):
        """L02/04: ...FlexPost -> DataPlus[O]."""
        self._create_url()
        self._flexpost()
        self._check_invoice()
        self._dataplus("O")
        return self.session

    def rejoin_inactive(self):
        """L02/05: login -> dashboard -> Create URL(exist) -> FlexPost -> Invoice -> DataPlus[I]."""
        self.login()
        self.refresh_dashboard()
        self._create_url(exist=True)
        self._flexpost()
        self._check_invoice()
        self._dataplus("I")
        return self.session

    def rebill(self):
        """DataPlus[N] — повторное списание (master; для самосепарата ещё и токен)."""
        self._dataplus("N")
        if self.session.is_self_separate:
            self._token_dataplus("N")
        return self.session

    # ---------- Bundle / Self-separate ----------

    def _token_flexpost(self):
        """FlexPost-постбэк токена (с зеркалированными x_invoice/x_bundle_*)."""
        body = payloads.build_token_flexpost_body(self.session)
        self.client.epoch_sync_json(body)
        self.session.tx_log.append(
            f"FlexPost[token M] member_id={self.session.token_member_id} tx={self.session.token_transaction_id} pi={self.session.token_pi_code}")
        logger.info("FlexPost[token M] ok: member_id=%s tx=%s pi=%s",
                    self.session.token_member_id, self.session.token_transaction_id,
                    self.session.token_pi_code)

    def _token_dataplus(self, tx_type):
        """Отдельная Data+ для рекуррентного токена самосепарата (member_id = master+1)."""
        s = self.session
        if not s.token_member_id:
            try:
                s.token_member_id = str(int(s.member_id) + 1)
            except (TypeError, ValueError):
                s.token_member_id = fakes.fake_member_id()
        if tx_type in ("N", "U"):
            base = s.token_last_dataplus_id or s.token_initial_transaction_id
            tx = fakes.inc_tx(base, 3)
        else:  # I / C — берём исходный tx токена
            tx = s.token_initial_transaction_id or fakes.fake_transaction_id()
            s.token_initial_transaction_id = tx
        s.token_transaction_id = tx
        self.client.epoch_sync_form(payloads.build_token_dataplus_form(s, tx_type),
                                    label=f"DataPlus[token {tx_type}]")
        if tx_type != "C":
            s.token_last_dataplus_id = tx
        s.tx_log.append(f"DataPlus[token {tx_type}] member_id={s.token_member_id} tx={tx}")
        logger.info("DataPlus[token %s] ok: member_id=%s tx=%s pi=%s", tx_type,
                    s.token_member_id, tx, s.token_pi_code)

    def finalize(self, cancel=True):
        """Обязательный хвост очистки тестовой оплаты: Cancel → Refund.

        cancel=True (рекуррент): Cancel[cancel] → DataPlus[C]. Lifetime/нереккурент: cancel=False
        (только Refund). При самосепарате чистим и master, и токен (наш бэк).
        """
        s = self.session
        # master
        if cancel:
            self.client.epoch_sync_form(payloads.build_cancel_form(s), label="Cancel")
            s.tx_log.append(f"Cancel master member_id={s.member_id}")
            logger.info("Cancel ok: member_id=%s", s.member_id)
        self._dataplus("C")
        # токен (наш бэк, member+1)
        if s.is_self_separate:
            if cancel:
                self.client.epoch_sync_form(payloads.build_token_cancel_form(s), label="Cancel[token]")
                s.tx_log.append(f"Cancel[token] member_id={s.token_member_id}")
                logger.info("Cancel[token] ok: member_id=%s", s.token_member_id)
            self._token_dataplus("C")
        self.refresh_dashboard()
        logger.info("Финализация (Cancel→Refund) завершена: status=%s", s.member_status)
        return s

    def bundle_join(self):
        """Бандл/самосепарат: Create URL (slaves+token) → FlexPost[M] → Invoice → DataPlus[I].

        Slave-сайты Epoch обрабатывает сам (Separated Bundle). Для самосепарата (токен —
        тот же бэк) дополнительно шлём DataPlus[I] на токен-слейв.
        """
        self._create_url()
        self._flexpost()
        self._check_invoice()
        self._dataplus("I")
        if self.session.is_self_separate:
            self._token_flexpost()      # M-постбэк токена (x_invoice + x_bundle_*)
            self._token_dataplus("I")
        return self.session

    # ---------- Layer 03: изменения ----------

    def upgrade(self):
        """L03/01: Upgrade rules -> Flexgrade Invoice -> FlexGrade[upgrade]."""
        self.login()
        self.refresh_dashboard()
        rules = self.client.get_upgrade_rules()
        prices = rules.get("prices") or []
        active = [p for p in prices if p.get("active")] or prices
        if not active:
            raise PaymentError("Нет доступных апгрейд-тарифов")
        sel = active[0]
        self.session.membership_uuid = rules.get("membership_uuid", self.session.membership_uuid)
        upgrade_uuid = sel.get("membership_id")
        self.session.active_pi_code = sel.get("epoch_pi_code", self.session.active_pi_code)

        invoice_params = self.client.get_flexgrade_invoice(
            self.session.email, self.session.membership_uuid, upgrade_uuid)
        form = payloads.build_flexgrade_form(self.session, invoice_params, kind="upgrade")
        self.client.epoch_sync_form(form, label="FlexGrade[upgrade]")
        self.session.tx_log.append(f"FlexGrade[upgrade] member_id={self.session.member_id} -> {upgrade_uuid}")
        logger.info("Upgrade ok -> %s", upgrade_uuid)
        self.refresh_dashboard()
        return self.session

    def easy_cancel_downgrade(self):
        """L03/02: Easy Cancel URL -> FlexGrade[downgrade]."""
        self.login()
        self.refresh_dashboard()
        invoice_params = self.client.get_easy_cancel_url(self.session.membership_uuid)
        form = payloads.build_flexgrade_form(self.session, invoice_params, kind="downgrade")
        self.client.epoch_sync_form(form, label="FlexGrade[downgrade]")
        self.session.tx_log.append(f"FlexGrade[downgrade] member_id={self.session.member_id}")
        logger.info("Easy Cancel Downgrade ok")
        self.refresh_dashboard()
        return self.session

    def refund(self):
        """L03/03: Cancel[cancel] -> DataPlus[C]."""
        self.login()
        self.refresh_dashboard()
        self.client.epoch_sync_form(payloads.build_cancel_form(self.session), label="Cancel")
        self._dataplus("C")
        self.refresh_dashboard()
        return self.session
