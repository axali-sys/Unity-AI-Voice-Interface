# XParallel Payment Setup V1

- Provider: Ecobank
- Destination: bank account, masked as ****2251
- Billing contact: azalibol74@gmail.com
- Currency: USD by default
- Payment capture: disabled
- Payment requests require explicit authorization.

## Security boundary

Never store the full bank account number, PIN, OTP, online-banking password,
card data, or payment/API secrets in source control.

This module can prepare a payment request, but it cannot move money. Actual
payment initiation requires an authorized bank/payment provider workflow and
explicit human approval.

## Production connection

A regulated payment processor or official bank API may be connected later using
credentials held only in the hosting platform's secret manager.
