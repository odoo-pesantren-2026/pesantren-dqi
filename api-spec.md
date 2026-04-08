# Smart Billing BPI (BSI) - H2H API Specification v3.2

## Overview

Host-to-Host (H2H) digunakan untuk komunikasi real-time antara:

- **Bank (BSI)**
- **Biller (Client System)**

### Operasi Utama

1. **AUTH** → Mendapatkan access token
2. **INQUIRY** → Mengambil data tagihan
3. **PAYMENT** → Konfirmasi pembayaran
4. **ADVICE (Optional)** → Cek status pembayaran

---

## Authentication (AUTH)

### Endpoint Purpose

Mendapatkan `accessToken` (OAuth 2.0)

### Header

- `X-TIMESTAMP`
- `X-CLIENT-KEY` (CLIENT_ID)
- `X-SIGNATURE` (RSA SHA256)
- `Content-Type: application/json`

### Request

```json
{
  "grantType": "client_credentials"
}
````

### Response

```json
{
  "responseCode": "2000000",
  "responseMessage": "Auth Success",
  "accessToken": "token",
  "tokenType": "BearerToken",
  "expiresIn": 900
}
```

### Notes

- Token berlaku **15 menit**
- Wajib dipanggil sebelum Inquiry & Payment

---

## Inquiry

### Purpose

Mengambil informasi tagihan

#### Header

- `Authorization: Bearer {accessToken}`
- `X-SIGNATURE` (HMAC SHA512)
- `X-PARTNER-ID` (KodeBPI)
- `CHANNEL-ID`
- `X-EXTERNAL-ID`

#### Request

```json
{
  "partnerServiceId": "____1234",
  "customerNo": "111222333444",
  "trxDateInit": "2023-11-01T17:59:13+07:00",
  "virtualAccountNo": "____1234111222333444",
  "inquiryRequestId": "123456",
  "sourceBankCode": "451"
}
```

### Response (Success)

```json
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

### Error Codes (Contoh)

| HTTP | Code    | Description    |
| ---- | ------- | -------------- |
| 404  | 4042412 | Bill not found |
| 404  | 4042414 | Already paid   |
| 500  | 5002400 | General error  |

---

## Payment

### Purpose

Menandai tagihan sebagai **dibayar**

### Request

```json
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

### Response

```json
{
  "responseCode": "2002500",
  "responseMessage": "Success"
}
```

### Error Codes

| Code    | Description    |
| ------- | -------------- |
| 4042513 | Invalid amount |
| 4042514 | Already paid   |
| 5002500 | General error  |

---

## Advice (Optional)

### Purpose

Validasi status pembayaran sebelumnya

### Notes

- Dipanggil jika Payment gagal
- Response harus sama dengan Payment
- Timeout: **2 detik**

---

## Billing Number Format

```
[KODE_BPI (4 digit)] + [Payment Number (5–12 digit)]
```

### Virtual Account (Non-BSI)

```
900 + KODE_BPI + Payment Number
```

---

## Channel ID

| Channel        | ID   |
| -------------- | ---- |
| ATM            | 6011 |
| Net Banking    | 6014 |
| Mobile Banking | 6027 |
| Simulator      | 6099 |

---

## Reconciliation

### Schedule

- **00:00 – 22:00 → D+1 (09:30)**
- **22:00 – 24:00 → D+1 (20:30)**

### File Format (CSV)

```
rekon_451_[kode_biller]_[tanggal]_[jumlah]_rev[time].csv
```

### Field Example

```
id_rekon;kode_biller;total_pembayaran;nama;wkt_transaksi;status
```

---

## Web Service Reconciliation

### Request

```json
{
  "action": "rekonsiliasi",
  "kodeBankBI": "451",
  "kodeBPI": "1234",
  "data": [...]
}
```

### Response

```json
[
  {"rc": true, "idRekon": "123456"}
]
```

---

## Security

- RSA Signature (AUTH)
- HMAC SHA512 (Inquiry & Payment)
- IP Whitelist:

  - 149.129.255.119
  - 202.74.236.178
  - 103.59.161.254

---

## Summary Flow

```
AUTH → INQUIRY → PAYMENT → (ADVICE)
```

---

## Notes for Implementation

- Semua response dalam **JSON**
- Gunakan **responseCode + responseMessage**
- Timeout:

  - Inquiry: 10s
  - Payment: 10s
  - Advice: 2s
