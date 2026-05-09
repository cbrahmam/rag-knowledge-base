# NovaTech Payments API Documentation

## Overview

The NovaTech Payments API allows you to integrate business payment processing into your application. Our API supports ACH transfers, wire transfers, and virtual card payments.

**Base URL**: `https://api.novatech.io/v2`
**Authentication**: Bearer token (API keys available in the Dashboard)
**Rate Limits**: 100 requests/minute for standard plans, 1000/minute for enterprise

## Authentication

All API requests must include an `Authorization` header:

```
Authorization: Bearer nt_live_abc123...
```

API keys come in two flavors:
- **Test keys** (`nt_test_*`): Use sandbox environment, no real money moves
- **Live keys** (`nt_live_*`): Production environment, real transactions

## Endpoints

### Create Payment

`POST /payments`

Creates a new payment between two business accounts.

**Request Body**:
```json
{
  "amount": 15000,
  "currency": "USD",
  "method": "ach",
  "sender_account_id": "acct_sender123",
  "recipient_account_id": "acct_recipient456",
  "description": "Invoice #1042 payment",
  "idempotency_key": "unique-key-123",
  "metadata": {
    "invoice_id": "INV-1042",
    "po_number": "PO-2024-789"
  }
}
```

**Response** (201 Created):
```json
{
  "id": "pmt_abc123",
  "status": "pending",
  "amount": 15000,
  "currency": "USD",
  "method": "ach",
  "estimated_arrival": "2024-03-15",
  "created_at": "2024-03-12T14:30:00Z"
}
```

**Payment Statuses**:
- `pending` — Payment created, awaiting processing
- `processing` — Payment is being processed by the banking network
- `completed` — Payment has been delivered to the recipient
- `failed` — Payment failed (see `failure_reason` field)
- `cancelled` — Payment was cancelled before processing

### Get Payment

`GET /payments/{payment_id}`

Retrieves details of a specific payment.

### List Payments

`GET /payments`

**Query Parameters**:
- `status` — Filter by status (e.g., `pending`, `completed`)
- `created_after` — ISO 8601 datetime
- `created_before` — ISO 8601 datetime
- `limit` — Number of results (default: 20, max: 100)
- `offset` — Pagination offset

### Cancel Payment

`POST /payments/{payment_id}/cancel`

Cancels a pending payment. Cannot cancel payments that are already `processing` or `completed`.

### Webhooks

Register webhook endpoints to receive real-time payment status updates.

`POST /webhooks`

```json
{
  "url": "https://yourapp.com/webhooks/payments",
  "events": ["payment.completed", "payment.failed"],
  "secret": "whsec_your_signing_secret"
}
```

**Webhook Events**:
- `payment.created` — New payment initiated
- `payment.processing` — Payment entered processing
- `payment.completed` — Payment delivered successfully
- `payment.failed` — Payment failed
- `payment.cancelled` — Payment was cancelled

### Error Handling

All errors follow this format:

```json
{
  "error": {
    "code": "insufficient_funds",
    "message": "The sender account does not have sufficient funds for this payment.",
    "param": "amount",
    "request_id": "req_xyz789"
  }
}
```

**Common Error Codes**:
- `invalid_request` — Missing or invalid parameters (400)
- `authentication_failed` — Invalid or expired API key (401)
- `insufficient_funds` — Sender account balance too low (402)
- `not_found` — Resource does not exist (404)
- `rate_limited` — Too many requests (429)
- `internal_error` — Server error, retry with exponential backoff (500)

## SDKs

Official SDKs are available for:
- Python: `pip install novatech`
- Node.js: `npm install @novatech/payments`
- Ruby: `gem install novatech`
- Go: `go get github.com/novatech/payments-go`

## Sandbox Testing

Use test API keys to simulate different scenarios:
- Amount ending in `00` — Payment succeeds
- Amount ending in `01` — Payment fails with insufficient funds
- Amount ending in `02` — Payment times out (takes 5 minutes to process)
