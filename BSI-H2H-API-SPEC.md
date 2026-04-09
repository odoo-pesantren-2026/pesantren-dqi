# Smart Billing BPI (BSI) - H2H API Full Technical Specification

---

## 1. Overview

H2H API untuk integrasi:

- Bank Syariah Indonesia (BSI)
- Biller System

### Main Flow

```text
AUTH → INQUIRY → PAYMENT → (ADVICE) → RECONCILIATION
````

---

## 2. Base Requirements

### Protocol

- HTTPS (TLS wajib)
- JSON request/response

### Timeout

| Endpoint | Timeout |
| -------- | ------- |
| AUTH     | 10s     |
| INQUIRY  | 10s     |
| PAYMENT  | 10s     |
| ADVICE   | 2s      |

---

## 3. Authentication (AUTH)

### Endpoint

```text
POST /api/bpi-bi-snap/auth
```

### Header

| Header       | Value            |
| ------------ | ---------------- |
| X-TIMESTAMP  | ISO8601          |
| X-CLIENT-KEY | CLIENT_ID        |
| X-SIGNATURE  | RSA-SHA256       |
| Content-Type | application/json |

### Signature

```text
X-SIGNATURE = Sign(CLIENT_ID + "|" + X-TIMESTAMP, PRIVATE_KEY)
```

---

### Request

```json id="auth-req"
{
  "grantType": "client_credentials"
}
```

---

### Response (HTTP 200)

```json id="auth-res"
{
  "responseCode": "2000000",
  "responseMessage": "Auth Success",
  "accessToken": "string",
  "tokenType": "BearerToken",
  "expiresIn": 900
}
```

---

### HTTP Status Mapping

| HTTP | responseCode | Meaning       |
| ---- | ------------ | ------------- |
| 200  | 2000000      | Success       |
| 401  | 4010000      | Unauthorized  |
| 500  | 5000000      | General Error |

---

## 4. Inquiry

### Endpoint

```text
POST /api/bpi-bi-snap/inquiry
```

---

### Header

| Header        | Description          |
| ------------- | -------------------- |
| Authorization | Bearer {accessToken} |
| X-TIMESTAMP   | ISO8601              |
| X-SIGNATURE   | HMAC SHA512          |
| X-PARTNER-ID  | KODE_BPI             |
| CHANNEL-ID    | Channel              |
| X-EXTERNAL-ID | Unique ID            |
| Content-Type  | application/json     |

---

### Signature Formula

```text
stringToSign =
HTTP_METHOD + ":" +
ENDPOINT + ":" +
ACCESS_TOKEN + ":" +
LOWERCASE(HEX(SHA256(minified_body))) + ":" +
TIMESTAMP

X-SIGNATURE = HMAC_SHA512(CLIENT_SECRET, stringToSign)
```

---

### Request

```json id="inq-req"
{
  "partnerServiceId": "____1234",
  "customerNo": "111222333444",
  "trxDateInit": "2023-11-01T17:59:13+07:00",
  "virtualAccountNo": "____1234111222333444",
  "inquiryRequestId": "123456",
  "sourceBankCode": "451"
}
```

---

### Response (HTTP 200)

```json id="inq-res"
{
  "responseCode": "2002400",
  "responseMessage": "Success",
  "virtualAccountData": {
    "customerNo": "111222333444",
    "virtualAccountName": "BUDI",
    "totalAmount": {
      "value": "15000",
      "currency": "IDR"
    }
  }
}
```

---

### Inquiry Response Code Mapping

| HTTP | Code    | Description       |
| ---- | ------- | ----------------- |
| 200  | 2002400 | Success           |
| 400  | 4002401 | Invalid format    |
| 400  | 4002402 | Missing field     |
| 401  | 4012400 | Unauthorized      |
| 401  | 4012401 | Invalid token     |
| 404  | 4042411 | Not payable       |
| 404  | 4042412 | Bill not found    |
| 404  | 4042414 | Already paid      |
| 404  | 4042419 | Invalid VA format |
| 404  | 4042420 | Expired           |
| 500  | 5002400 | General error     |
| 500  | 5002499 | DB error          |
| 504  | 5042400 | Timeout           |

---

## 5. Payment

### Endpoint

```text
POST /api/bpi-bi-snap/payment
```

---

### Request

```json id="pay-req"
{
  "partnerServiceId": "____1234",
  "customerNo": "111222333444",
  "paidAmount": {
    "value": "15000",
    "currency": "IDR"
  },
  "trxDateTime": "2024-06-24T14:54:05+07:00",
  "paymentRequestId": "123456"
}
```

---

### Response (HTTP 200)

```json id="pay-res"
{
  "responseCode": "2002500",
  "responseMessage": "Success"
}
```

---

### Payment Response Code Mapping

| HTTP | Code    | Description    |
| ---- | ------- | -------------- |
| 200  | 2002500 | Success        |
| 400  | 4002501 | Invalid format |
| 400  | 4002502 | Missing field  |
| 401  | 4012500 | Unauthorized   |
| 401  | 4012501 | Invalid token  |
| 404  | 4042512 | Bill not found |
| 404  | 4042513 | Invalid amount |
| 404  | 4042514 | Already paid   |
| 404  | 4042519 | Invalid format |
| 500  | 5002500 | General error  |
| 500  | 5002599 | DB error       |
| 504  | 5042500 | Timeout        |

---

## 6. Advice

### Endpoint

```text
POST /api/bpi-bi-snap/advice
```

---

### Behavior

| Rule     | Value                     |
| -------- | ------------------------- |
| Trigger  | Payment gagal / timeout   |
| Retry    | 1x                        |
| Timeout  | 2 detik                   |
| Response | HARUS sama dengan Payment |

---

### Lookup Strategy

```text
PRIMARY KEY   : paymentRequestId
VALIDATION    : customerNo
CONSISTENCY   : paidAmount, trxDateTime
```

---

### Idempotency Rule

```text
IF paymentRequestId exists:
    return stored response
ELSE:
    process normally
```

---

## 7. Reconciliation

### Endpoint (Custom)

```text
POST /api/bpi-bi-snap/reconciliation
```

---

### Request

```json id="recon-req"
{
  "action": "rekonsiliasi",
  "kodeBankBI": "451",
  "kodeBPI": "1234",
  "data": []
}
```

---

### Response

```json id="recon-res"
[
  {
    "rc": true,
    "idRekon": "123456"
  }
]
```

---

### Rules

- One-time call
- No auto retry from BSI
- Must validate checksum

---

## 8. Billing Format

```text
VA = KODE_BPI (4) + PAYMENT_NUMBER (5–12)
```

### Non-BSI

```text
VA = 900 + KODE_BPI + PAYMENT_NUMBER
```

---

## 9. Channel ID

| Channel        | Code |
| -------------- | ---- |
| ATM            | 6011 |
| Net Banking    | 6014 |
| Mobile Banking | 6027 |
| Simulator      | 6099 |

---

## 10. Security

### Signature Types

| Endpoint | Method      |
| -------- | ----------- |
| AUTH     | RSA SHA256  |
| Others   | HMAC SHA512 |

---

### IP Whitelist

```text
149.129.255.119
202.74.236.178
103.59.161.254
```

---

## 11. Idempotency

### Key

```text
paymentRequestId
```

### Behavior

- Duplicate request → return same response
- No double processing

---

## 12. Error Response Format

```json id="error-format"
{
  "responseCode": "xxxxxxx",
  "responseMessage": "Description"
}
```

---

## 13. Implementation Notes

### Database

- Store:

  - request
  - response
  - status
  - timestamp

### Logging

- All requests must be logged
- Include signature validation result

---

## 14. Best Practices

### Reliability

- Idempotent endpoint
- Retry-safe logic
- Timeout handling

### Performance

- Cache token
- Index DB by `paymentRequestId`

---

## 15. Checklist

- [ ] AUTH working
- [ ] Signature validated
- [ ] Inquiry < 10s
- [ ] Payment idempotent
- [ ] Advice consistent
- [ ] Recon implemented
- [ ] Logging active
- [ ] Security enabled

---

## 16. Final Summary

```text
AUTH → INQUIRY → PAYMENT → ADVICE → RECON
```
