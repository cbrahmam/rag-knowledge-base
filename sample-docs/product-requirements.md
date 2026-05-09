# Product Requirements Document: Instant Payments Feature

## Document Info
- **Author**: Sarah Chen, Product Manager
- **Last Updated**: February 28, 2024
- **Status**: Approved
- **Target Release**: Q2 2024 (April 15 launch)

## Executive Summary

NovaTech currently supports ACH payments (2-3 business day settlement) and wire transfers (same-day but expensive at $25/transfer). Our customers have consistently requested a faster, cheaper payment option. This PRD outlines "Instant Payments" — a new payment method enabling near-real-time fund transfers at a $4.99 flat fee per transaction.

## Problem Statement

Based on customer interviews (n=47) and support ticket analysis:
- 68% of customers cite payment speed as their #1 frustration
- Average time to payment completion via ACH: 2.4 business days
- 34% of customers have used wire transfers despite the cost, purely for speed
- We're losing 12% of prospects to competitors who offer same-day ACH

## Proposed Solution

### Instant Payments via RTP Network

We will integrate with The Clearing House's RTP (Real-Time Payments) network to offer instant settlement.

**Key Features**:
1. **Near-instant settlement**: Funds available in recipient's account within 60 seconds
2. **Flat fee**: $4.99 per transaction (compared to $25 for wires)
3. **24/7/365 availability**: Unlike ACH, works on weekends and holidays
4. **Transaction limits**: $100,000 per transaction (RTP network limit)
5. **Irrevocable**: Once sent, instant payments cannot be reversed (unlike ACH)
6. **Confirmation**: Real-time confirmation receipt for both sender and recipient

### User Experience Flow

1. User selects "Instant Payment" as payment method during checkout
2. System verifies sender account has sufficient funds + fee
3. User sees confirmation screen: amount, fee ($4.99), estimated arrival ("Within 60 seconds")
4. User confirms payment with 2FA
5. Payment is submitted to RTP network
6. Both parties receive real-time notification upon completion
7. Transaction appears in dashboard immediately

### API Changes

New `method` value: `"instant"` for the Create Payment endpoint.

Additional response field for instant payments:
```json
{
  "method": "instant",
  "fee": 499,
  "completed_at": "2024-03-12T14:30:05Z",
  "confirmation_id": "RTP-2024-abc123"
}
```

## Success Metrics

| Metric | Current | Target (90 days post-launch) |
|--------|---------|------------------------------|
| Payment method adoption | N/A | 30% of all payments use instant |
| Customer satisfaction (CSAT) | 7.2/10 | 8.5/10 |
| Average payment completion time | 2.4 days | < 1 minute for instant |
| Revenue per transaction | $1.50 (ACH) | $4.99 (instant) |
| Monthly payment volume | $12.5M | $15M (20% increase) |

## Technical Requirements

- Integration with The Clearing House RTP network
- Real-time balance checking before payment submission
- Webhook notifications for instant payment events
- Database schema updates for new payment method
- Update fraud detection rules for instant payments (higher risk due to irrevocability)
- Load testing: system must handle 500 instant payments per minute
- 99.95% uptime SLA for the instant payments service

## Risks & Mitigations

1. **Fraud risk**: Instant payments are irrevocable, increasing fraud risk
   - *Mitigation*: Enhanced fraud scoring, $10K initial per-transaction limit, gradual increase based on account age
2. **RTP network downtime**: If the RTP network is unavailable
   - *Mitigation*: Graceful fallback to same-day ACH with clear messaging to user
3. **Cash flow impact**: Instant outflows could cause balance issues
   - *Mitigation*: Real-time balance holds, daily settlement reconciliation

## Timeline

- **March 1-15**: RTP network integration (backend)
- **March 15-31**: Frontend UI updates and API changes
- **April 1-7**: Internal testing and QA
- **April 8-14**: Beta launch (10% of users)
- **April 15**: General availability

## Open Questions

1. Should we offer instant payments for international transfers? (Decision needed by March 10)
2. What is our refund policy for instant payments given they're irrevocable?
3. Do we need a separate approval workflow for instant payments over $50K?
