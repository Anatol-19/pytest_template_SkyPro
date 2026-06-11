"""Сборка form-тел Segpay для прокси /api/payment/sync-handler/segpay.

Модель Segpay: один form-постбэк на событие; тип = trantype (Sale/Credit/Charge) + stage.
Порт из коллекции (смежный проект) с маппингом полей на нашу сторону:
  paymentaccountid ≈ invoice, invoiceid/eticketid/pplist — из get-recurring-payment-url (module=segpay).
"""

import uuid

from services.payment import config_segpay as sg
from services.payment import fakes
from services.payment.models import PaymentSession


def _base(session: PaymentSession, *, amount, trantype, stage, action="Auth", extra=None) -> dict:
    """Общий каркас Segpay-формы. amount — строка (может быть отрицательной для Credit/Charge)."""
    body = {
        "ccfirst6": sg.CC_FIRST6[:6] if False else "9999",
        "cclast4": sg.CC_LAST4,
        "ccbincountry": sg.CC_BIN_COUNTRY,
        "prepaidindicator": sg.PREPAID_INDICATOR,
        "cardtype": sg.CARD_TYPE,
        "authprice": amount,
        "authcurrency": session.active_currency or "USD",
        "issingleusepromo": "No",
        "paymentaccountid": session.invoice_uuid,        # ≈ invoice (наша сторона)
        "paymenttype": sg.PAYMENT_TYPE,
        "scarequired": "No",
        "is3dsauthenticated": "Yes",
        "3dsauthenticationtype": "",
        "threedsversion": "2.2.0",
        "stage": stage,
        "approved": "Yes",
        "trantype": trantype,
        "price": amount,
        "currencycode": session.active_currency or "USD",
        "ipaddress": sg.IP_ADDRESS,
        "eticketid": session.segpay_eticketid,
        "ival": session.active_amount,
        "iint": sg.INITIAL_INTERVAL,
        "rval": session.active_amount,
        "rint": sg.REBILL_INTERVAL,
        "desc": sg.DESC,
        "billname": sg.BILL_NAME,
        "billnamefirst": sg.BILL_NAME_FIRST,
        "billnamelast": sg.BILL_NAME_LAST,
        "billemail": session.email,
        "billzip": sg.BILL_ZIP,
        "billcntry": sg.BILL_COUNTRY,
        "transguid": str(uuid.uuid4()),
        "standin": "0",
        "xsellnum": "0",
        "transtime": fakes.segpay_date(),
        "tranid": session.transaction_id,
        "action": action,
        "method": "Post",
        "browsertype": "Chrome",
        "browserversion": "141.0",
        "ismobiledevice": "false",
        "platform": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "invoiceid": session.invoice_uuid,
        "pplist": session.segpay_pplist,
        "templatetype": "PayPage",
        "ipcountry": sg.IP_COUNTRY,
        "merchantname": sg.MERCHANT_NAME,
        "template": "default",
        "paytype": "creditcard",
        "paymentchoice": "cc",
        "purchaseid": session.member_id,
        "urlid": sg.URL_ID,
        "postbackconfiguniqueid": sg.POSTBACK_CONFIG_UNIQUE_ID,
        "processingtime": fakes.segpay_date(),
        "merchantid": sg.MERCHANT_ID,
        "isTest": "true",
    }
    if extra:
        body.update(extra)
    return body


def build_initial(session: PaymentSession) -> dict:
    """Initial Recurring — stage=Initial, trantype=Sale."""
    return _base(session, amount=session.active_amount, trantype="Sale", stage="Initial",
                 extra={"refurl": ""})


def build_recurring(session: PaymentSession) -> dict:
    """Rebill — stage=Conversion, trantype=Sale."""
    return _base(session, amount=session.active_amount, trantype="Sale", stage="Conversion")


def build_refund(session: PaymentSession) -> dict:
    """Refund — trantype=Credit, отрицательная сумма, relatedtranid = последняя транзакция."""
    return _base(session, amount=f"-{session.active_amount}", trantype="Credit", stage="Initial",
                 extra={"relatedtranid": session.last_dataplus_id,
                        "refundreasoncode": sg.REFUND_REASON_CODE,
                        "refundedby": session.email, "refundcomment": "Test Refund"})


def build_chargeback(session: PaymentSession) -> dict:
    """Chargeback — trantype=Charge, отрицательная сумма."""
    return _base(session, amount=f"-{session.active_amount}", trantype="Charge", stage="Initial",
                 extra={"relatedtranid": session.last_dataplus_id})


def build_upgrade_postback(session: PaymentSession, new_amount=None) -> dict:
    """Segpay Upgrade postback ('Old Upgrade'): подтверждение успешного апгрейда.

    Отправляется после получения upgrade-URL (recurring-upgrade-url/segpay).
    purchaseId — member, transactionId — новая транзакция, newRecurringAmount — цена нового тарифа.
    """
    return {
        "isSuccess": "true",
        "message": "Purchase has been upgraded successfully.",
        "purchaseId": session.member_id,
        "transactionId": session.transaction_id,
        "transactionAmount": session.active_amount,
        "newRecurringAmount": new_amount or session.active_amount,
        "nextTransactionDate": "2053-04-04",
        "transactionAuthCode": "OK:0",
        "isTest": "true",
    }


def build_cancel(session: PaymentSession) -> dict:
    """Cancel — action=Cancel (минимальная форма)."""
    return {
        "cancelreasoncode": sg.CANCEL_REASON_CODE,
        "cancelcomment": "QA Cancel",
        "cancelledby": session.email,
        "action": "Cancel",
        "password": "",
        "invoiceid": session.invoice_uuid,
        "templatetype": "PayPage",
        "paytype": "creditcard",
        "paymentchoice": "cc",
        "purchaseid": session.member_id,
        "urlid": "000000",
        "isTest": "true",
    }
