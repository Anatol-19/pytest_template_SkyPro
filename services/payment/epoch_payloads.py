"""Сборка тел запросов к прокси /api/payment/sync-handler/epoch.

Чистые функции без HTTP. Порт логики из Postman pre-scripts.
"""

from services.payment import config_payment as cfg
from services.payment import fakes
from services.payment.models import PaymentSession


def _bundle_x_params(session: PaymentSession) -> dict:
    """x-параметры купленных сайтов. Epoch зеркалит их во ВСЕ постбэки —
    поэтому добавляем и в master, и в token-постбэк."""
    params = {"x_bundle_master_vrporn": session.price.epoch_pi_code}
    for slug, picode in (session.bundle_slave_picodes or {}).items():
        params[f"x_bundle_slave_{slug}"] = picode
    return params


def build_flexpost_body(session: PaymentSession) -> dict:
    """Тело FlexPost [M] — JSON. Генерирует и сохраняет fake-идентификаторы в session."""
    price = session.price
    member_id = fakes.fake_member_id()
    transaction_id = fakes.fake_transaction_id()
    session_id = fakes.fake_session_id()

    session.member_id = member_id
    session.transaction_id = transaction_id
    session.initial_transaction_id = transaction_id
    session.session_id = session_id

    amount = price.amount
    currency = price.currency
    username = session.email.split("@")[0]

    body = {
        "email": session.email,
        "username": session.email,
        "member_id": member_id,
        "transaction_id": transaction_id,
        "pi_code": price.epoch_pi_code,
        "x_pi_code": price.epoch_pi_code,
        "trans_amount": amount,
        "trans_amount_usd": amount,
        "amount": amount,
        "localamount": amount,
        "order_id": member_id,
        "event_datetime": fakes.epoch_time(),
        "ans": f"YQATEST|{transaction_id}",
        "reseller": cfg.RESELLER,
        "name": username,
        "postalcode": cfg.ZIP,
        "zip": cfg.ZIP,
        "co_code": cfg.CO_CODE_FLEXPOST,
        "country": cfg.COUNTRY,
        "ipaddress": cfg.IPADDR,
        "submit_count": "1",
        "trans_currency": currency,
        "currency": currency,
        "payment_type": cfg.PAYMENT_TYPE,
        "payment_subtype": cfg.DEFAULT_PST_TYPE,
        "site": cfg.SITE,
        "session_id": session_id,
        "epoch_digest": cfg.EPOCH_DIGEST,
        "x_invoice": session.invoice_uuid,
        "x_uniq_id": session.invoice_uuid,
        "x_user": session.user_uuid,
        "isTest": True,
    }

    if session.is_bundle:
        body["x_is_master_site"] = "true"
        body["pi_code"] = cfg.MASTER_INVOICE_PRODUCT  # флаг Dynamic Price, не реальный PiCode
        body.update(_bundle_x_params(session))

    return body


def build_token_flexpost_body(session: PaymentSession) -> dict:
    """FlexPost-постбэк токена самосепарата (x_is_master_site=false).

    Зеркалит x-параметры мастера (x_invoice/x_uniq_id/x_user + x_bundle_*), т.к. Epoch
    добавляет их во все постбэки. Без x_invoice бэк считает транзакцию кроссейлом.
    member_id = master+1, тот же session_id, свой x_pi_code/сумма токена.
    """
    if not session.token_member_id:
        try:
            session.token_member_id = str(int(session.member_id) + 1)
        except (TypeError, ValueError):
            session.token_member_id = fakes.fake_member_id()
    tx = fakes.fake_transaction_id()
    session.token_transaction_id = tx
    session.token_initial_transaction_id = tx

    amount = session.token_amount or session.price.amount
    body = {
        "email": session.email,
        "username": session.email,
        "member_id": session.token_member_id,
        "transaction_id": tx,
        "pi_code": cfg.MASTER_INVOICE_PRODUCT,        # invoiceProduct токен-сайта (пока общий)
        "x_pi_code": session.token_pi_code,
        "trans_amount": amount,
        "trans_amount_usd": amount,
        "amount": amount,
        "localamount": amount,
        "order_id": session.token_member_id,
        "event_datetime": fakes.epoch_time(),
        "ans": f"YQATEST|{tx}",
        "reseller": cfg.RESELLER,
        "name": session.email.split("@")[0],
        "postalcode": cfg.ZIP,
        "zip": cfg.ZIP,
        "co_code": cfg.CO_CODE_FLEXPOST,
        "country": cfg.COUNTRY,
        "ipaddress": cfg.IPADDR,
        "submit_count": "1",
        "trans_currency": session.token_currency,
        "currency": session.token_currency,
        "payment_type": cfg.PAYMENT_TYPE,
        "payment_subtype": cfg.DEFAULT_PST_TYPE,
        "site": cfg.SITE,
        "session_id": session.session_id,            # тот же session_id, что у мастера
        "epoch_digest": cfg.EPOCH_DIGEST,
        # x-параметры мастера — обязательно (иначе кроссейл) + зеркалирование купленных сайтов
        "x_invoice": session.invoice_uuid,
        "x_uniq_id": session.invoice_uuid,
        "x_user": session.user_uuid,
        "x_is_master_site": "false",
        "isTest": True,
    }
    body.update(_bundle_x_params(session))
    return body


def build_dataplus_form(session: PaymentSession, tx_type: str) -> dict:
    """Тело DataPlus — form-urlencoded. tx_type: I|N|F|T|U|O|C.

    Сам выставляет transaction_id (инкремент для N/U, исходный для I/F/T/O,
    отрицательная сумма и ref для C).
    """
    price = session.price
    is_increment = tx_type in ("N", "U")

    if is_increment:
        base = session.last_dataplus_id or session.initial_transaction_id
        if not base:
            raise ValueError("Нет last_dataplus_id / initial_transaction_id для инкремента")
        tx_id = fakes.inc_tx(base, 3)
    else:
        tx_id = session.initial_transaction_id
        if not tx_id:
            raise ValueError("Нет initial_transaction_id — сначала FlexPost [M]")
    session.transaction_id = tx_id

    # N использует активный тариф (может смениться после upgrade), остальные — исходный
    if tx_type == "N":
        pi_code = session.active_pi_code or price.epoch_pi_code
        amount = session.active_amount or price.amount
        currency = session.active_currency or price.currency
    else:
        pi_code = price.epoch_pi_code
        amount = price.amount
        currency = price.currency

    ref_ids = "0"
    if tx_type == "C":
        amount = f"-{amount}"
        ref_ids = session.last_dataplus_id or session.initial_transaction_id

    prepaid = "N" if tx_type in ("F", "U", "C") else ""

    form = {
        "ets_transaction_id": tx_id,
        "ets_member_idx": session.member_id,
        "ets_transaction_date": fakes.transaction_date(),
        "ets_transaction_type": tx_type,
        "ets_co_code": cfg.CO_CODE_DATAPLUS,
        "ets_pi_code": pi_code,
        "ets_reseller_code": cfg.RESELLER_CODE,
        "ets_transaction_amount": amount,
        "ets_payment_type": cfg.PAYMENT_TYPE,
        "ets_pst_type": cfg.DEFAULT_PST_TYPE,
        "ets_username": session.email,
        "ets_password": session.password,
        "ets_email": session.email,
        "ets_ref_trans_ids": ref_ids,
        "ets_country": cfg.COUNTRY,
        "ets_state": "",
        "ets_postalcode": cfg.ZIP,
        "ets_city": "",
        "ets_street": "",
        "ets_ipaddr": cfg.IPADDR_REFUND if tx_type == "C" else cfg.IPADDR,
        "ets_firstname": cfg.FIRSTNAME,
        "ets_lastname": cfg.LASTNAME,
        "ets_initdate": "",
        "ets_password_expire": "",
        "ets_currency": currency,
        "ets_amountlocal": amount,
        "ets_mastercode": cfg.MASTERCODE,
        "ets_site_subcat": "",
        "ets_prepaid": prepaid,
        "isTest": "true",
        "x_is_master_site": "true" if session.is_bundle else "false",
    }
    return form


def build_token_dataplus_form(session: PaymentSession, tx_type: str) -> dict:
    """Data+ для рекуррентного токена самосепарата (отдельный сайт на стороне платёжки).

    Использует свои member_id (обычно master+1), tx, pi_code и сумму токена.
    Тип такой же, как у рекуррентной подписки (I/N/U); O/S — для нереккурентных (не здесь).
    """
    amount = session.token_amount
    ref_ids = "0"
    if tx_type == "C":  # рефанд токена
        amount = f"-{session.token_amount}"
        ref_ids = session.token_last_dataplus_id or session.token_initial_transaction_id
    return {
        "ets_transaction_id": session.token_transaction_id,
        "ets_member_idx": session.token_member_id,
        "ets_transaction_date": fakes.transaction_date(),
        "ets_transaction_type": tx_type,
        "ets_co_code": cfg.CO_CODE_DATAPLUS,
        "ets_pi_code": session.token_pi_code,
        "ets_reseller_code": cfg.RESELLER_CODE,
        "ets_transaction_amount": amount,
        "ets_payment_type": cfg.PAYMENT_TYPE,
        "ets_pst_type": cfg.DEFAULT_PST_TYPE,
        "ets_username": session.email,
        "ets_password": session.password,
        "ets_email": session.email,
        "ets_ref_trans_ids": ref_ids,
        "ets_country": cfg.COUNTRY,
        "ets_state": "",
        "ets_postalcode": cfg.ZIP,
        "ets_city": "",
        "ets_street": "",
        "ets_ipaddr": cfg.IPADDR,
        "ets_firstname": cfg.FIRSTNAME,
        "ets_lastname": cfg.LASTNAME,
        "ets_initdate": "",
        "ets_password_expire": "",
        "ets_currency": session.token_currency,
        "ets_amountlocal": amount,
        "ets_mastercode": cfg.MASTERCODE,
        "ets_site_subcat": "",
        "ets_prepaid": "",
        "isTest": "true",
        "x_is_master_site": "false",
    }


def build_token_cancel_form(session: PaymentSession, reason="TEST Reason") -> dict:
    """Cancel токена самосепарата (mcs_ с token member_id/pi)."""
    date = fakes.transaction_date()
    return {
        "mcs_or_idx": session.token_member_id,
        "mcs_canceldate": date,
        "mcs_cocode": cfg.CO_CODE_DATAPLUS,
        "mcs_picode": session.token_pi_code,
        "mcs_reseller": cfg.RESELLER_CODE,
        "mcs_signupdate": date,
        "mcs_email": session.email,
        "mcs_username": session.email,
        "mcs_reason": reason,
        "mcs_passwordremovaldate": date,
        "mcs_memberstype": "R",
        "mcs_site_subcat": "",
        "mcs_source": "MC",
        "isTest": "true",
    }


def build_cancel_form(session: PaymentSession, reason="TEST Reason") -> dict:
    """Тело Cancel [cancel] — form-urlencoded, префикс mcs_."""
    date = fakes.transaction_date()
    return {
        "mcs_or_idx": session.member_id,
        "mcs_canceldate": date,
        "mcs_cocode": cfg.CO_CODE_DATAPLUS,
        "mcs_picode": session.active_pi_code or session.price.epoch_pi_code,
        "mcs_reseller": cfg.RESELLER_CODE,
        "mcs_signupdate": date,
        "mcs_email": session.email,
        "mcs_username": session.email,
        "mcs_reason": reason,
        "mcs_passwordremovaldate": date,
        "mcs_memberstype": "R",
        "mcs_site_subcat": "",
        "mcs_source": "MC",
        "isTest": "true",
    }


def build_flexgrade_form(session: PaymentSession, invoice_params: dict, kind="upgrade") -> dict:
    """Тело FlexGrade (upgrade/downgrade) — form-urlencoded.

    invoice_params — query-параметры из Flexgrade Invoice / Easy Cancel URL
    (x_invoice, x_gate_type/x_membership_id и т.д.).
    """
    tag = "YQAUPGRADE" if kind == "upgrade" else "YQADOWNGRADE"
    tx_id = session.transaction_id or session.initial_transaction_id
    return {
        "ans": f"{tag}|{tx_id}",
        "local_amount": session.active_amount or session.price.amount,
        "amount": session.active_amount or session.price.amount,
        "currency": session.active_currency or session.price.currency,
        "transaction_id": tx_id,
        "member_id": session.member_id,
        "x_gate_type": invoice_params.get("x_gate_type", "flexgrade"),
        "x_invoice": invoice_params.get("x_invoice", session.invoice_uuid),
        "x_membership_id": invoice_params.get("x_membership_id", ""),
        "isTest": "true",
    }
