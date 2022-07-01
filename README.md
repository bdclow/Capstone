
# Skillshare Project
### MADS Capstone Summer 2022

## Contributors
+ Brian Clow
+ Travis Stowe
+ Ryan Estrada
+ Garrett Amstutz

## To get started:
+ Create virtual environment and activate
+ Install requirements (e.g. pip install -r requirements)
+ Download data

> python download.py

## Goals
### Predict subscriptions, specifically who converts from a free trial to an initial subscription
#### Currently utilized surrogates: 
+ P1 Net of Refunds (P1NR)
+ 3 videos watched in the first 3 days (3N3)
+ 60 minutes of watch time in 1st 30 days (%60)

## Questions
+ Why limiting to 12 month subscriptions?
+ **What information would be available to Skillshare during trial period?**
    - May be good to sort out which columns are target related

## Table info

| table | column name | description |
| --- | --- | --- |
| starts | user_uid | unique user id |
| starts | is_active | active subscription |
| starts | create_time | account creation OR trial start ?? |
| starts | first_payment_time | first time paid |
| starts | last_payment_time | last successful payment |
| starts | next_billing_time | next time will be billed |
| starts | last_payment_attempt | last time payment was tried |
| starts | last_failed_payment_attempt | --- |
| starts | user_cancellation_time | --- |
| starts | cancellation_time | --- |
| starts | refund_time | --- |
| starts | coupon_id | --- |
| starts | coupon_trial_length | --- |
| starts | payment_provider | --- |
| starts | payment_ux | --- |
| starts | is_paused | --- |
| starts | pause_time | --- |
| starts | is_refunded | --- |
| starts | is_resume | --- |
| starts | paid_through | --- |
| starts | is_lapsed | --- |
| starts | is_pending | --- |
| starts | is_cancelled | --- |
| starts | has_paid | --- |
| starts | is_paid | --- |
| starts | trial_end | --- |
| starts | category | --- |
| starts | num_payments | --- |
| starts | num_successful_payments | --- |
| starts | first_payment_currency_code | --- |
| starts | subscription_number | --- |
| starts | paid_subscription_number | --- |
| starts | eligible_subscription_number | --- |
| starts | is_p1_refunded | --- |
| starts | trial_extension_time | --- |
| starts | original_create_time | --- |
| starts | original_trial_end | --- |
| starts | extended_trial_end | --- |
| starts | was_trial_extended | --- |
| starts | is_trial_extension | --- |
| starts | is_split_trial | --- |
| starts | is_paid_reactivation | --- |
| starts | trial_length_days | --- |
| starts | trial_length_offer | --- |
| starts | sub_utm_source | --- |
| starts | sub_utm_campaign | --- |
| starts | sub_utm_medium | --- |
| starts | sub_utm_term | --- |
| starts | sub_utm_channel | --- |
| starts | referral_source | --- |
| starts | eligible_trial_number | --- |
