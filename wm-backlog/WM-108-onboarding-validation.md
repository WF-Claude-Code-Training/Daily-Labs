# WM-108 — New-account onboarding accepts incomplete KYC data

In `compliance/onboarding`, validate that every required KYC field is present before an
account is activated, and don't change the activation API. Run the onboarding test suite
to confirm existing accounts still activate correctly.
