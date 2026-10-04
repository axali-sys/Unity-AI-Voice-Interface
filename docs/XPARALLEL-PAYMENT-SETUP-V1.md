# XParallel Payment Setup V1

## Purpose

Provide a safe payment/payout configuration boundary around the organization's
Ecobank destination and billing contact.

## Configured references

- Provider: Ecobank
- Destination: bank account, masked as ****2251
- Billing contact: azalibol74@gmail.com
- Currency: USD by default
- Payment capture: disabled
- Payment requests: authorization required

## Security boundary

The repository must never contain the full bank account number, PIN, OTP,
online-banking password, card data, or payment/API secrets.

The application can generate an invoice/payment request, but it cannot move
money automatically. Actual payment initiation must occur through an
authorized banking/payment provider workflow and explicit human approval.

## Runtime variables

- XP_BILLING_EMAIL
- XP_BILLING_CURRENCY
- XP_PAYOUT_PROVIDER

No bank credentials are represented as environment variables in this setup.

## Next production connection

Connect a regulated payment processor or bank collection/payout API only after
the organization has authorized the provider account and supplied its official
credentials through the hosting platform's secret manager.
