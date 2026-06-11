"""Генераторы тестовых данных — порт JS-хелперов из Postman pre-scripts.

Epoch принимает синтетические идентификаторы в тестовом режиме (isTest=true).
"""

import random
import re
import time
from datetime import datetime


def _digits(n: int) -> str:
    """Строка из n случайных цифр."""
    return "".join(str(random.randint(0, 9)) for _ in range(n))


def fake_member_id() -> str:
    """Фейковый Epoch member_id: '4219' + 9 цифр."""
    return "4219" + _digits(9)


def fake_transaction_id() -> str:
    """Фейковый transaction_id: '108qa' + 6 цифр."""
    return "108qa" + _digits(6)


def fake_session_id() -> str:
    """Фейковый session_id: 32 цифры + '_qa'."""
    return _digits(32) + "_qa"


def epoch_time() -> str:
    """Текущий unix-timestamp строкой."""
    return str(int(time.time()))


def transaction_date() -> str:
    """Дата транзакции в формате 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def segpay_date() -> str:
    """Дата для Segpay: 'MM/DD/YYYY hh:MM:SS AM/PM' (US, AM/PM)."""
    return datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")


def inc_tx(tx_id: str, step: int = 3) -> str:
    """Инкремент числового хвоста transaction_id (для rebill / конверсии).

    '108qa000123' -> '108qa000126'
    """
    match = re.match(r"^(.*?)(\d+)$", str(tx_id or ""))
    if not match:
        raise ValueError(f"Некорректный transaction_id: {tx_id!r}")
    prefix, number = match.group(1), match.group(2)
    return prefix + str(int(number) + step).zfill(len(number))


def fake_email() -> str:
    """Фейковый email нового мембера: YYYY_MM_DD_HH_MM_SSak@mailhog.plus (порт stamp() из Postman)."""
    stamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    return f"{stamp}an@mailto.plus"


def fake_password(email: str = None) -> str:
    """Пароль = email (Postman: user_password = email)."""
    return email or fake_email()


def money(value) -> str:
    """Денежная сумма строкой с двумя знаками: 19.4 -> '19.40'."""
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return ""
