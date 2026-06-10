# Payment — матрица кейсов (утверждено)

> Дата: 2026-06-10. Реализовано в `test/test_payment.py`. Прогон: `pytest -m payment --environment=VRP_STAGE`.
> Каждая цепочка завершается хвостом **Cancel → Refund** (lifetime — только Refund).
> Самосепарат чистит и master, и токен (member+1, наш бэк). Все транзакции `isTest=true`.

## СПИСОК A — в работе (1 full-run, 11 кейсов) ✅ прошли на STAGE

| # | Тест | event/tab | Транзакции (мы шлём) | Epoch сам |
|---|---|---|---|---|
| 1 | `TestUserJoins::test_join_recurring[monthly]` | tab=monthly | M→I→N → Cancel→C | — |
| 2 | `TestUserJoins::test_join_recurring[yearly]` | tab=yearly | M→I→N → Cancel→C | — |
| 3 | `TestUserJoins::test_join_lifetime` | tab=lifetime | M→O → C (без Cancel) | — |
| 4 | `TestUserJoins::test_join_bundle[mono]` | event=mono | master M→I→N → Cancel→C | vrconk |
| 5 | `TestUserJoins::test_join_bundle[bundle]` | event=bundle | master M→I→N → Cancel→C | vrbangers, arporn |
| 6 | `TestUserJoins::test_join_bundle[super]` | event=super | master M→I→N → Cancel→C | 4 slave |
| 7 | `TestUserJoins::test_join_bundle[self]` | event=self | master M→I→N + token M→I→N → Cancel→C (оба) | — |
| 8 | `TestUserJoins::test_join_bundle[ss]` | event=ss | master+token M→I→N → Cancel→C (оба) | arporn |
| 9 | `TestUserJoins::test_join_bundle[sos]` | event=sos | master+token M→I→N → Cancel→C (оба) | 4 slave |
| 10 | `TestUserChanges::test_change_and_rebill[upgrade]` | monthly | M→I → FlexGrade[upgrade] → N → Cancel→C | — |
| 11 | `TestUserChanges::test_change_and_rebill[downgrade]` | monthly | M→I → FlexGrade[downgrade] → N → Cancel→C | — |

Обозначения: M=FlexPost initial, I=initial recurring, N=rebill, O=one-time, C=refund.
Бандл slave-транзакции рассылает Epoch (на handlerUrl slave-сайтов) — мы их не шлём.
Токен самосепарата (наш бэк) — шлём FlexPost-M (с зеркалированными x_invoice/x_bundle_*) + DataPlus I/N/C.

## СПИСОК B — бэклог (к разработке)

1. **Sale Events** — выбор прайс-группы; триггеры DropCard / Holiday / Expired / Affiliate / Default.
2. **Layer 01 Tariffs** (sale-event/prices smoke) — в контексте Sale Events.
3. **Re-join** истёкшего мембера (`TestExpiredMember`) — часть Sale Events.
4. **Standalone-токены** (джойн только токенов, без подписки).
5. **Dynamic Pricing** upgrade/downgrade — не на проде пока.
6. **Бандлы где мы slave** + **cross-sale**.
7. **Бандлы с токенами** (двойной/супер с токеном в наборе).
8. **Segpay** (второй в каскаде) + другие платёжки.
9. Методы **F/T/U** (free/paid trial, конверсия) — остаются как строительные блоки `PaymentFlow`, не отдельные юзер-сценарии.

## Event-ключи (Sale Events на TEST/STAGE)

| Ключ | Состав | bundledSites |
|---|---|---|
| `default` | без бандла | `[]` |
| `mono` | 1 slave | vrconk |
| `bundle` | 2 slave | vrbangers, arporn |
| `super` | super (4) | 4 сайта |
| `self` | самосепарат (токен) | vrporn.com |
| `ss` (DropCard) | self + slave | arporn + vrporn.com |
| `sos` (DropCard) | super + self | 4 + vrporn.com |
