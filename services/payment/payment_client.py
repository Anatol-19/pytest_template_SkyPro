"""HTTP-клиент платёжного флоу VRP.

Каждый публичный метод = один запрос Postman-коллекции. Парсеры ответов вынесены
в staticmethods. Контур задаётся через BaseApiClient(environment=...).
"""

from urllib.parse import parse_qs, urlparse

from REST.base_client import BaseApiClient
from services.payment import config_payment as cfg
from services.payment.fakes import money
from services.payment.models import PaymentResult, TariffPrice


class PaymentError(Exception):
    """Ошибка платёжного флоу."""


class PaymentClient(BaseApiClient):
    """Клиент Join/Payment API. Наследует резолвинг base_url/routes от BaseApiClient."""

    # ---------- Контур ----------

    @property
    def self_host(self) -> str:
        """Хост текущего контура (для self-separated бандла). Без хардкода."""
        return urlparse(self.base_url).netloc

    # ---------- Auth ----------

    def auth(self, email, password):
        """POST /api/wp/secure/auth/login — авторизация мембера, сохранение токенов."""
        data = self.post_json("auth_payment", json={"email": email, "password": password})
        token = (data.get("data") or {}).get("token") or {}
        atoken = token.get("atoken")
        if not atoken:
            raise PaymentError(f"Auth: нет data.token.atoken в ответе: {data}")
        self.set_bearer_token(atoken)
        self.session.cookies.set("atoken", atoken)
        rtoken = token.get("rtoken")
        if rtoken:
            self.session.cookies.set("rtoken", rtoken)
        return token

    # ---------- Layer 01: тарифы ----------

    def get_sale_event(self, event="", event_id=""):
        """GET user-sale-event. Опциональные event/event_id."""
        params = {}
        if event:
            params["event"] = event
        if event_id:
            params["event_id"] = event_id
        return self.get_json("join_sale_event", params=params or None)

    def get_prices(self, slot=None, event_id="", event=""):
        """GET /memberships/prices.

        slot=N    -> Special прайс внутри прайс-группы (type_prices_from_slot).
        event_id  -> привязка к конкретному Sale Event (нужен для бандлов/спец-цен).
        Без параметров -> Standard прайс.
        """
        params = {}
        if slot:
            params["type_prices_from_slot"] = slot
        if event_id:
            params["event_id"] = event_id
            params["event"] = event
        return self.get_json("join_prices", params=params or None)

    # ---------- Layer 02: создание оплаты ----------

    def create_payment_url(self, email, password, subscr_id, slave_uuids=None,
                           additional_subscription_id=None, module="epoch"):
        """POST get-recurring-payment-url (новый мембер).

        module — платёжная система: "epoch" | "segpay" (тот же роут, разные шлюзы).
        Идентификация тарифа в трёх местах (как на фронте):
          - subscr_id — UUID мастер/дефолтного тарифа,
          - slavePriceUuids — массив UUID slave-сайтов (бандл),
          - additionalSubscriptionId — integer id рекуррентного токена (самосепарат).
        """
        payload = {
            "affiliate": "",
            "email": email,
            "email_marketing": True,
            "js_hit": "",
            "module": module,
            "password": password,
            "subscr_id": subscr_id,
            "slavePriceUuids": slave_uuids or [],
            "uuid": "",
        }
        if additional_subscription_id is not None:
            payload["additionalSubscriptionId"] = additional_subscription_id
        return self.parse_payment_url(self.post_json("payment_url_new", json=payload))

    @staticmethod
    def parse_segpay_extras(payment_url):
        """Из Segpay paymentUrl достать поля для транзакции: eticketid, pplist (=segpay_ti_code),
        x-auth-link, x-decl-link, invoiceId."""
        from urllib.parse import unquote
        qs = parse_qs(urlparse(payment_url).query)
        return {
            "eticketid": qs.get("x-eticketid", [""])[0],
            "pplist": qs.get("pplist", [""])[0],
            "auth_link": unquote(qs.get("x-auth-link", [""])[0]),
            "decl_link": unquote(qs.get("x-decl-link", [""])[0]),
            "invoice_id": qs.get("invoiceId", [""])[0],
        }

    def resolve_bundle(self, price, bundled_hosts):
        """По sale_event.bundledSites и выбранному прайсу собрать состав бандла/самосепарата.

        Возвращает dict:
          slave_uuids[], slave_picodes{slug: epochPiCode}, additional_subscription_id (int|None),
          token (dict|None: pi_code/amount/currency/recurring), is_self_separate (bool).
        """
        slave_uuids = []
        slave_picodes = {}
        additional_subscription_id = None
        token = None
        is_self = False

        slaves = price.raw.get("price_slave_sites") or []
        specials = price.raw.get("special_prices") or []

        for host in bundled_hosts:
            if host in cfg.SELF_HOSTS:
                # Самосепарат: рекуррентный токен из special_prices[0] (новая логика, внутри прайса)
                if specials:
                    sp = specials[0]
                    additional_subscription_id = sp.get("id")
                    token = {
                        "pi_code": sp.get("epochPiCode", ""),
                        "amount": money(sp.get("priceAmount") or sp.get("rebillPrice")),
                        "currency": sp.get("currency") or price.currency,
                        "recurring": bool(sp.get("isRecurring")),
                    }
                    is_self = True
            else:
                slave = next((s for s in slaves if s.get("siteHost") == host), None)
                if slave:
                    slave_uuids.append(slave.get("uuid"))
                    slug = host.replace(".com", "")
                    slave_picodes[slug] = slave.get("epochPiCode", "")
        return {
            "slave_uuids": slave_uuids,
            "slave_picodes": slave_picodes,
            "additional_subscription_id": additional_subscription_id,
            "token": token,
            "is_self_separate": is_self,
        }

    def create_payment_url_exist(self, email, password, subscr_id, additional_subscription_id=""):
        """POST get-recurring-payment-url-exist (re-join неактивного/истёкшего)."""
        payload = {
            "affiliate": "",
            "email": email,
            "email_marketing": True,
            "js_hit": "",
            "module": "epoch",
            "password": password,
            "subscr_id": subscr_id,
            "additionalSubscriptionId": additional_subscription_id,  # строка, НЕ []
            "slavePriceUuids": [],
            "uuid": "",
        }
        return self.parse_payment_url(self.post_json("payment_url_exist", json=payload))

    # ---------- Epoch sync (прокси) ----------

    def epoch_sync_json(self, body: dict):
        """POST /api/payment/sync-handler/epoch — JSON (FlexPost [M])."""
        return self._epoch_ok(self.post_json("epoch_sync", json=body), "FlexPost")

    def epoch_sync_form(self, data: dict, label="DataPlus"):
        """POST /api/payment/sync-handler/epoch — form-urlencoded (DataPlus/Cancel/FlexGrade)."""
        headers = {"content-type": "application/x-www-form-urlencoded"}
        response = self.request("POST", "epoch_sync", data=data, headers=headers)
        response.raise_for_status()
        return self._epoch_ok(response.json(), label)

    def segpay_upgrade_url(self, email, membership_uuid, upgrade_price_uuid, js_hit=""):
        """POST recurring-upgrade-url/segpay — тело как у epoch-апгрейда, module=segpay."""
        payload = {
            "affiliate": "",
            "email": email,
            "email_marketing": False,
            "js_hit": js_hit,
            "membership_uuid": membership_uuid,
            "module": "segpay",
            "no_redirect": True,
            "price_membership_id": upgrade_price_uuid,
            "subscr_id": upgrade_price_uuid,
            "uuid": "",
        }
        return self.post_json("upgrade_url_segpay", json=payload)

    def segpay_sync_form(self, data: dict, label="Segpay"):
        """POST /api/payment/sync-handler/segpay — form-urlencoded (Initial/Recurring/Cancel/Refund).

        Segpay-хендлер отвечает строкой "OK" (а не {"status":"ok"}, как epoch)."""
        headers = {"content-type": "application/x-www-form-urlencoded"}
        response = self.request("POST", "segpay_sync", data=data, headers=headers)
        response.raise_for_status()
        text = (response.text or "").strip().strip('"')
        if text.upper() != "OK":
            raise PaymentError(f"{label}: Segpay вернул не OK: {response.text[:200]}")
        return text

    @staticmethod
    def _epoch_ok(data, label):
        if data.get("status") != "ok":
            raise PaymentError(f"{label}: прокси вернул статус != ok: {data}")
        return data

    # ---------- Проверки состояния ----------

    def invoice_status(self, invoice_uuid):
        """GET /api/payment/invoice/status."""
        return self.get_json("invoice_status", params={"invoice_uuid": invoice_uuid})

    def dashboard_info(self):
        """GET /proxy-user/api/wp/user/dashboardInfo (требует atoken)."""
        return self.parse_dashboard(self.get_json("dashboard_info"))

    # ---------- Layer 03: изменения ----------

    def get_upgrade_rules(self):
        """GET price-upgrade-rules — доступные апгрейд-тарифы + membership_uuid."""
        return self.get_json("upgrade_rules")

    def get_flexgrade_invoice(self, email, membership_uuid, upgrade_price_uuid, js_hit=""):
        """POST recurring-upgrade-url/epoch — инвойс апгрейда."""
        payload = {
            "affiliate": "",
            "email": email,
            "email_marketing": False,
            "js_hit": js_hit,
            "membership_uuid": membership_uuid,
            "module": "epoch",
            "no_redirect": True,
            "price_membership_id": upgrade_price_uuid,
            "subscr_id": upgrade_price_uuid,
            "uuid": "",
        }
        data = self.post_json("upgrade_url_epoch", json=payload)
        if not data.get("paymentUrl"):
            raise PaymentError(f"Flexgrade Invoice: пустой paymentUrl: {data}")
        return self.parse_url_query(data["paymentUrl"])

    def get_easy_cancel_url(self, membership_uuid):
        """GET easy-cancel/upgrade-url — URL даунгрейда."""
        data = self.get_json("easy_cancel_upgrade_url", params={"membershipUuid": membership_uuid})
        if not data.get("url"):
            raise PaymentError(f"Easy Cancel URL: пустой url: {data}")
        return self.parse_url_query(data["url"])

    # ---------- Парсеры ----------

    @staticmethod
    def parse_payment_url(data: dict) -> PaymentResult:
        """Разбор ответа Create Payment URL: dynamic (бандл) vs old (query)."""
        payment_url = data.get("paymentUrl")
        if not payment_url:
            raise PaymentError(f"Create Payment URL: нет paymentUrl: {data}")
        if data.get("invoiceUuid"):
            return PaymentResult(
                payment_url=payment_url,
                invoice_uuid=data["invoiceUuid"],
                user_uuid=data.get("userUuid", ""),
                is_dynamic_url=True,
            )
        qs = parse_qs(urlparse(payment_url).query)
        return PaymentResult(
            payment_url=payment_url,
            invoice_uuid=qs.get("x_invoice", [""])[0],
            user_uuid=qs.get("x_user", [""])[0],
            is_dynamic_url=False,
        )

    @staticmethod
    def parse_url_query(url: str) -> dict:
        """Query-параметры URL в dict (для flexgrade/easy-cancel)."""
        return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}

    @staticmethod
    def parse_dashboard(data: dict) -> dict:
        """Разбор dashboardInfo -> info первого мембера."""
        rows = data.get("data") or []
        if not rows:
            raise PaymentError(f"Dashboard: пустой data: {data}")
        info = rows[0].get("info") or {}
        if not info.get("member_id"):
            raise PaymentError(f"Dashboard: нет info.member_id: {info}")
        return info

    # Нормализация пользовательских значений таба к реальным slug
    _TAB_ALIASES = {
        "month": "monthly", "monthly": "monthly", "m": "monthly",
        "year": "yearly", "yearly": "yearly", "y": "yearly", "annual": "yearly",
        "life": "lifetime", "lifetime": "lifetime", "lt": "lifetime",
    }

    def parse_prices(self, prices_json: dict, tab="monthly") -> TariffPrice:
        """Выбор тарифа из ответа /prices по периоду (tab).

        tab — monthly|yearly|lifetime, с нормализацией алиасов (year->yearly).
        Категория (ключ prices[...]) задаётся бэкендом — берём первую доступную.
        Никогда не выбирает таб «молча»: если tab не найден — бросает PaymentError
        со списком доступных значений.
        """
        prices = prices_json.get("prices")
        if not prices:
            raise PaymentError(f"В ответе /prices нет тарифов: {prices_json}")
        # prices может быть dict по категориям ({'bundle': [...]}) или плоским списком
        if isinstance(prices, dict):
            category = next(iter(prices))
            by_category = prices.get(category) or []
        else:
            category = ""
            by_category = prices
        if not by_category:
            raise PaymentError(f"Список тарифов пуст: {prices}")

        tab_slug = self._TAB_ALIASES.get(str(tab).lower(), str(tab).lower())
        candidates = [p for p in by_category if (p.get("price_tab") or {}).get("slug") == tab_slug]
        if not candidates:
            available = ", ".join(sorted({(p.get("price_tab") or {}).get("slug")
                                          for p in by_category if p.get("price_tab")}))
            raise PaymentError(f"Tab '{tab}' (slug='{tab_slug}') не найден. Доступные: {available}")

        price = candidates[0]
        if not price.get("membership_id"):
            raise PaymentError(f"У тарифа нет membership_id: {price}")
        if not price.get("epoch_pi_code"):
            raise PaymentError(f"У тарифа нет epoch_pi_code: {price}")

        amount = money(price.get("trial_price") or price.get("price") or price.get("rebill_price"))
        return TariffPrice(
            membership_id=price["membership_id"],
            epoch_pi_code=price["epoch_pi_code"],
            amount=amount,
            currency=price.get("price_currency") or price.get("currency") or "USD",
            category=category,
            tab=(price.get("price_tab") or {}).get("slug", tab),
            raw=price,
        )
