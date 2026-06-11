# Тела запросов и флоу для Postman-коллекции

> Этот файл — готовый материал для переноса в `Payment_final.json`.
> Генерируется Python-агентом из `epoch_payloads.py` / `segpay_payloads.py`.
> При изменениях в Python-коде — обновить этот файл.
> Последнее обновление: 2026-06-11

---

## Константы (в run_env.json)

### Epoch
```json
{
  "co_code_flexpost":  "def",
  "co_code_dataplus":  "VRP",
  "reseller":          "qa_tester_19",
  "reseller_code":     "a",
  "epoch_digest":      "b1bd4832368aa4b37c9037ff50c2e90a_qa",
  "mastercode":        "M-607039",
  "payment_type":      "CC",
  "pst_type":          "MC",
  "site":              "a",
  "master_invoice_product": "invoiceProduct158529",
  "zip":               "91780",
  "ipaddr":            "162.251.108.36",
  "ipaddr_refund":     "195.135.215.247",
  "country":           "US",
  "firstname":         "QA",
  "lastname":          "Test"
}
```

### Segpay
```json
{
  "sg_merchant_id":    "22186",
  "sg_url_id":         "691365",
  "sg_postback_uid":   "39632",
  "sg_cc_first6":      "9999",
  "sg_cc_last4":       "9999",
  "sg_bill_zip":       "33060",
  "sg_bill_country":   "US",
  "sg_cancel_code":    "826",
  "sg_refund_code":    "826"
}
```

---

## Эндпоинты (Base_url = контур)

| Название | Метод | Путь |
|---|---|---|
| Sale Event | GET | `{{Base_url}}/proxy-user/api/memberships/join-now/user-sale-event` |
| Prices | GET | `{{Base_url}}/proxy-user/api/memberships/prices` |
| Create Payment URL | POST | `{{Base_url}}/api/memberships/join-now/get-recurring-payment-url` |
| Create Payment URL (exist) | POST | `{{Base_url}}/api/memberships/join-now/get-recurring-payment-url-exist` |
| Epoch Sync | POST | `{{Base_url}}/api/payment/sync-handler/epoch` |
| Segpay Sync | POST | `{{Base_url}}/api/payment/sync-handler/segpay` |
| Invoice Status | GET | `{{Base_url}}/api/payment/invoice/status` |
| Auth (payment) | POST | `{{Base_url}}/api/wp/secure/auth/login` |
| Dashboard Info | GET | `{{Base_url}}/proxy-user/api/wp/user/dashboardInfo` |
| Upgrade Rules | GET | `{{Base_url}}/proxy-user/api/memberships/service/price-upgrade-rules` |
| Flexgrade Invoice | POST | `{{Base_url}}/proxy-user/api/payment/recurring-upgrade-url/epoch` |
| Easy Cancel URL | GET | `{{Base_url}}/proxy-user/api/easy-cancel/upgrade-url` |

---

## Layer 01 — Tariffs

### GET Sale Event
```
GET {{Base_url}}/proxy-user/api/memberships/join-now/user-sale-event?event={{sale_event_key}}
```
Pre-request: не нужен.
Test script:
```javascript
const d = pm.response.json();
pm.environment.set("sale_event_id", d.uuid || "");
pm.environment.set("bundled_sites", JSON.stringify(d.bundledSites || []));
pm.test("sale event получен", () => pm.expect(pm.response.code).to.eql(200));
```

### GET Prices
```
GET {{Base_url}}/proxy-user/api/memberships/prices
  ?event_id={{sale_event_id}}    ← только если есть sale event
  &type_prices_from_slot=2       ← только для Special-цен
```
Test script (сохранить monthly тариф):
```javascript
const d = pm.response.json();
const prices = Array.isArray(d.prices) ? d.prices : Object.values(d.prices)[0];
const monthly = prices.find(p => p.price_tab?.slug === "monthly");
pm.environment.set("epoch_pi_code",  monthly.epoch_pi_code);
pm.environment.set("membership_id",  monthly.membership_id);
pm.environment.set("price_amount",   String(parseFloat(monthly.trial_price || monthly.price || monthly.rebill_price)).toFixed(2));
// Self-separate (если есть)
const sp = monthly.special_prices?.[0];
if (sp) {
    pm.environment.set("token_pi_code", sp.epochPiCode);
    pm.environment.set("additional_subscription_id", String(sp.id));
    pm.environment.set("token_amount", String(parseFloat(sp.priceAmount || sp.rebillPrice)).toFixed(2));
}
// Slave (если есть)
const slave = monthly.price_slave_sites?.[0];
if (slave) {
    pm.environment.set("slave_uuid", slave.uuid);
    pm.environment.set("slave_pi_code", slave.epochPiCode);
}
```

---

## Layer 02 — Joins (Epoch)

### Шаг 1: Create Payment URL
```
POST {{Base_url}}/api/memberships/join-now/get-recurring-payment-url
Content-Type: application/json

{
  "affiliate": "",
  "email": "{{email}}",
  "email_marketing": true,
  "js_hit": "",
  "module": "epoch",
  "password": "{{password}}",
  "subscr_id": "{{membership_id}}",
  "slavePriceUuids": [],
  "uuid": ""
}
```
Для бандла добавить `"slavePriceUuids": ["{{slave_uuid}}"]`.
Для самосепарата добавить `"additionalSubscriptionId": {{additional_subscription_id}}`.

Test script:
```javascript
const d = pm.response.json();
const url = d.paymentUrl;
pm.environment.set("invoice_uuid", d.invoiceUuid || new URLSearchParams(new URL(url).search).get("x_invoice"));
pm.environment.set("user_uuid",    d.userUuid    || new URLSearchParams(new URL(url).search).get("x_user"));
pm.test("paymentUrl получен", () => pm.expect(url).to.be.a("string").and.not.empty);
```

### Шаг 2: FlexPost [M] — простая покупка
```
POST {{Base_url}}/api/payment/sync-handler/epoch
Content-Type: application/json

{
  "email":             "{{email}}",
  "username":          "{{email}}",
  "member_id":         "{{member_id}}",
  "transaction_id":    "{{transaction_id}}",
  "transaction_date":  "{{transaction_date}}",
  "pi_code":           "{{epoch_pi_code}}",
  "x_pi_code":         "{{epoch_pi_code}}",
  "trans_amount":      "{{price_amount}}",
  "trans_amount_usd":  "{{price_amount}}",
  "amount":            "{{price_amount}}",
  "localamount":       "{{price_amount}}",
  "order_id":          "{{member_id}}",
  "event_datetime":    "{{epoch_time}}",
  "transaction_date":  "{{transaction_date}}",
  "ans":               "YQATEST|{{transaction_id}}",
  "reseller":          "qa_tester_19",
  "name":              "qa",
  "postalcode":        "91780",
  "zip":               "91780",
  "co_code":           "def",
  "country":           "US",
  "ipaddress":         "162.251.108.36",
  "submit_count":      "1",
  "trans_currency":    "USD",
  "currency":          "USD",
  "payment_type":      "CC",
  "payment_subtype":   "MC",
  "site":              "a",
  "session_id":        "{{session_id}}",
  "epoch_digest":      "b1bd4832368aa4b37c9037ff50c2e90a_qa",
  "x_invoice":         "{{invoice_uuid}}",
  "x_uniq_id":         "{{invoice_uuid}}",
  "x_user":            "{{user_uuid}}",
  "isTest":            true
}
```
Pre-request: генерация `member_id`, `transaction_id`, `session_id`, `epoch_time`, `transaction_date`.
Test script: `pm.test("ok", () => pm.expect(pm.response.json().status).to.eql("ok"));`

### FlexPost [M] — бандл (добавить к телу выше)
```json
"x_is_master_site":          "true",
"pi_code":                   "invoiceProduct158529",
"x_bundle_master_vrporn":    "{{epoch_pi_code}}",
"x_bundle_slave_vrbangers":  "{{slave_pi_code}}"
```

### FlexPost [M] — токен самосепарата (x_is_master_site=false)
```json
"member_id":              "{{token_member_id}}",
"transaction_id":         "{{token_transaction_id}}",
"pi_code":                "invoiceProduct158529",
"x_pi_code":              "{{token_pi_code}}",
"trans_amount":           "{{token_amount}}",
"x_is_master_site":       "false",
"x_invoice":              "{{invoice_uuid}}",
"x_uniq_id":              "{{invoice_uuid}}",
"x_user":                 "{{user_uuid}}",
"x_bundle_master_vrporn": "{{epoch_pi_code}}",
"x_bundle_slave_vrbangers":"{{slave_pi_code}}"
```

### Шаг 3: Invoice Status
```
GET {{Base_url}}/api/payment/invoice/status?invoice_uuid={{invoice_uuid}}
```

### Шаг 4: DataPlus [I] — Initial
```
POST {{Base_url}}/api/payment/sync-handler/epoch
Content-Type: application/x-www-form-urlencoded

ets_transaction_id={{transaction_id}}
&ets_member_idx={{member_id}}
&ets_transaction_date={{transaction_date}}
&ets_transaction_type=I
&ets_co_code=VRP
&ets_pi_code={{epoch_pi_code}}
&ets_reseller_code=a
&ets_transaction_amount={{price_amount}}
&ets_payment_type=CC
&ets_pst_type=MC
&ets_username={{email}}
&ets_password={{password}}
&ets_email={{email}}
&ets_ref_trans_ids=0
&ets_country=US
&ets_state=
&ets_postalcode=91780
&ets_city=
&ets_street=
&ets_ipaddr=162.251.108.36
&ets_firstname=QA
&ets_lastname=Test
&ets_initdate=
&ets_password_expire=
&ets_currency=USD
&ets_amountlocal={{price_amount}}
&ets_mastercode=M-607039
&ets_site_subcat=
&ets_prepaid=
&isTest=true
&x_is_master_site=false
```
Для бандла добавить:
```
&x_is_master_site=true
&x_invoice={{invoice_uuid}}
&x_uniq_id={{invoice_uuid}}
&x_user={{user_uuid}}
&x_bundle_master_vrporn={{epoch_pi_code}}
&x_bundle_slave_vrbangers={{slave_pi_code}}
```
Test script: `pm.environment.set("last_dataplus_id", pm.environment.get("transaction_id"));`

### DataPlus [N] — Rebill
Тело как у [I], но:
- Pre-request: `inc_tx(last_dataplus_id, +3)` → `transaction_id`
- `ets_transaction_type=N`
- `ets_pi_code = {{active_pi_code}}` (может смениться после upgrade)

### DataPlus [O] — Lifetime (one-time)
Тело как у [I], но `ets_transaction_type=O`.

### DataPlus [C] — Refund
```
ets_transaction_type=C
ets_transaction_amount=-{{price_amount}}
ets_ipaddr=195.135.215.247
ets_ref_trans_ids={{last_dataplus_id}}
ets_prepaid=N
```
Бандл: те же x_invoice + x_bundle_*.

### Cancel [cancel]
```
POST {{Base_url}}/api/payment/sync-handler/epoch
Content-Type: application/x-www-form-urlencoded

mcs_or_idx={{member_id}}
&mcs_canceldate={{transaction_date}}
&mcs_cocode=VRP
&mcs_picode={{epoch_pi_code}}
&mcs_reseller=a
&mcs_signupdate={{transaction_date}}
&mcs_email={{email}}
&mcs_username={{email}}
&mcs_reason=TEST Reason
&mcs_passwordremovaldate={{transaction_date}}
&mcs_memberstype=R
&mcs_site_subcat=
&mcs_source=MC
&isTest=true
```

---

## Layer 03 — Changes (Epoch)

### Upgrade: Flexgrade Invoice
```
POST {{Base_url}}/proxy-user/api/payment/recurring-upgrade-url/epoch
Authorization: Bearer {{atoken}}
Content-Type: application/json

{
  "affiliate": "",
  "email": "{{email}}",
  "email_marketing": false,
  "js_hit": "",
  "membership_uuid": "{{membership_uuid}}",
  "module": "epoch",
  "no_redirect": true,
  "price_membership_id": "{{upgrade_membership_id}}",
  "subscr_id": "{{upgrade_membership_id}}",
  "uuid": ""
}
```
Test: `pm.environment.set("flexgrade_invoice", new URLSearchParams(new URL(pm.response.json().paymentUrl).search).get("x_invoice"));`

### FlexGrade [U] — Upgrade
```
POST {{Base_url}}/api/payment/sync-handler/epoch
Content-Type: application/x-www-form-urlencoded

ans=YQAUPGRADE|{{transaction_id}}
&local_amount={{price_amount}}
&amount={{price_amount}}
&currency=USD
&transaction_id={{transaction_id}}
&member_id={{member_id}}
&x_gate_type=flexgrade
&x_invoice={{flexgrade_invoice}}
&x_membership_id={{upgrade_membership_id}}
&isTest=true
```

### Easy Cancel URL (Downgrade)
```
GET {{Base_url}}/proxy-user/api/easy-cancel/upgrade-url?membershipUuid={{membership_uuid}}
Authorization: Bearer {{atoken}}
```
Test: сохранить `x_invoice` из `data.url` → `flexgrade_invoice`.

### FlexGrade [D] — Downgrade
Тело как у Upgrade, но `ans=YQADOWNGRADE|{{transaction_id}}`.

---

## Segpay

### Create URL (module=segpay)
Тело как у Epoch Create Payment URL, но `"module": "segpay"`.
Test script:
```javascript
const url = pm.response.json().paymentUrl;
const qs = new URLSearchParams(new URL(url).search);
pm.environment.set("invoice_uuid",      qs.get("invoiceId") || pm.response.json().invoiceUuid);
pm.environment.set("segpay_eticketid",  qs.get("x-eticketid") || "");
pm.environment.set("segpay_pplist",     qs.get("pplist") || "");
```
Pre-request: генерация `member_id`, `transaction_id` (те же функции что для Epoch).

### Segpay Initial (stage=Initial, trantype=Sale)
```
POST {{Base_url}}/api/payment/sync-handler/segpay
Content-Type: application/x-www-form-urlencoded

stage=Initial
&trantype=Sale
&approved=Yes
&price={{price_amount}}
&authprice={{price_amount}}
&currencycode=USD
&authcurrency=USD
&paymentaccountid={{invoice_uuid}}
&invoiceid={{invoice_uuid}}
&eticketid={{segpay_eticketid}}
&pplist={{segpay_pplist}}
&purchaseid={{member_id}}
&tranid={{transaction_id}}
&merchantid=22186
&urlid=691365
&postbackconfiguniqueid=39632
&billemail={{email}}
&billzip=33060
&billcntry=US
&billname=QA Tester
&billnamefirst=QA
&billnamelast=Tester
&cardtype=Visa
&ccfirst6=9999
&cclast4=9999
&ccbincountry=US
&prepaidindicator=N
&ival={{price_amount}}
&iint=30
&rval={{price_amount}}
&rint=30
&ipaddress=255.255.255.255
&ipcountry=US
&transtime={{segpay_date}}
&processingtime={{segpay_date}}
&paymenttype=CreditCard
&paytype=creditcard
&paymentchoice=cc
&templatetype=PayPage
&template=default
&merchantname=Swearl, LLC
&desc=QA Test SegPay
&standin=0
&xsellnum=0
&transguid={{guid}}
&action=Auth
&method=Post
&browsertype=Chrome
&browserversion=141.0
&ismobiledevice=false
&platform=Mozilla/5.0 (X11; Linux x86_64)
&scarequired=No
&is3dsauthenticated=Yes
&3dsauthenticationtype=
&threedsversion=2.2.0
&issingleusepromo=No
&refurl=
&isTest=true
```
Pre-request: `segpay_date` = `MM/DD/YYYY hh:MM:SS AM/PM` (US, 12-часовой формат), `guid` = `crypto.randomUUID()`.
Test: `pm.test("OK", () => pm.expect(pm.response.text().replace(/"/g,'')).to.eql("OK"));`

### Segpay Recurring (stage=Conversion)
Тело как Initial, но `stage=Conversion`, `refurl` убрать.
Pre-request: `inc_tx(last_dataplus_id, +3)`.

### Segpay Cancel
```
POST {{Base_url}}/api/payment/sync-handler/segpay
Content-Type: application/x-www-form-urlencoded

action=Cancel
&cancelreasoncode=826
&cancelcomment=QA Cancel
&cancelledby={{email}}
&invoiceid={{invoice_uuid}}
&templatetype=PayPage
&paytype=creditcard
&paymentchoice=cc
&purchaseid={{member_id}}
&urlid=000000
&isTest=true
```

### Segpay Refund (trantype=Credit)
Тело как Initial, но:
- `trantype=Credit`
- `price=-{{price_amount}}`
- `authprice=-{{price_amount}}`
- `relatedtranid={{last_dataplus_id}}`
- `refundreasoncode=826`
- `refundedby={{email}}`
- `refundcomment=Test Refund`

---

## Переменные: когда и где устанавливаются

| Переменная | Устанавливается в | Используется в |
|---|---|---|
| `email`, `password` | Pre-request первого запроса в сценарии | все запросы |
| `member_id` | Pre-request FlexPost[M] | все Epoch постбэки |
| `transaction_id` | Pre-request FlexPost[M] | FlexPost, DataPlus |
| `initial_transaction_id` | Test FlexPost[M] | DataPlus[C] (ref_ids) |
| `last_dataplus_id` | Test каждого DataPlus | DataPlus[N], DataPlus[C] |
| `invoice_uuid` | Test Create Payment URL | все x_invoice поля |
| `user_uuid` | Test Create Payment URL | x_user в бандлах |
| `atoken` | Test Auth | Dashboard, Upgrade |
| `membership_uuid` | Test Dashboard | Upgrade, Easy Cancel |
| `segpay_eticketid` | Test Segpay Create URL | Segpay postbacks |
| `segpay_pplist` | Test Segpay Create URL | Segpay postbacks |
| `token_member_id` | Pre-request token FlexPost | token DataPlus |
| `token_transaction_id` | Pre-request token FlexPost | token DataPlus |
