*** Settings ***
Resource        ../keywords/payment_keywords.robot
Suite Setup     Create Payment Session

*** Test Cases ***

Transfer With Insufficient Funds
    [Documentation]    Transfer amount exceeding account balance is rejected
    [Tags]    error    funds
    ${resp}=    Send Transfer
    ...    sender=${LOW_BALANCE}
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${9999.00}
    Transfer Should Fail With    ${resp}    422    INSUFFICIENT_FUNDS

Transfer Exceeding Daily Limit
    [Documentation]    Transfer above the daily limit is rejected
    [Tags]    error    limits
    ${resp}=    Send Transfer
    ...    sender=${VALID_SENDER}
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${10000.00}
    Transfer Should Fail With    ${resp}    422    EXCEEDS_DAILY_LIMIT

Transfer From Unknown Account
    [Documentation]    Sending from a non-existent account returns 404
    [Tags]    error    account
    ${resp}=    Send Transfer
    ...    sender=FI9999999999999999
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${100.00}
    Transfer Should Fail With    ${resp}    404    ACCOUNT_NOT_FOUND

Transfer To Timeout IBAN Returns 504
    [Documentation]    Transfers to the designated timeout IBAN simulate a gateway timeout
    [Tags]    error    timeout    performance
    ${resp}=    Send Transfer
    ...    sender=${VALID_SENDER}
    ...    receiver=${TIMEOUT_IBAN}
    ...    amount=${10.00}
    Transfer Should Fail With    ${resp}    504    TIMEOUT

Transfer With Zero Amount Is Rejected
    [Documentation]    Amount of zero is a boundary condition — must be rejected at the API level
    [Tags]    error    boundary
    ${payload}=    Create Dictionary
    ...    sender_iban=${VALID_SENDER}
    ...    receiver_iban=${VALID_RECEIVER}
    ...    amount=${0}
    ...    currency=EUR
    ${resp}=    POST On Session    payment_api    /transfer
    ...    json=${payload}    expected_status=any
    Should Be Equal As Integers    ${resp.status_code}    422

Transfer With Negative Amount Is Rejected
    [Documentation]    Negative amounts must be rejected at the API level
    [Tags]    error    boundary
    ${payload}=    Create Dictionary
    ...    sender_iban=${VALID_SENDER}
    ...    receiver_iban=${VALID_RECEIVER}
    ...    amount=${-50}
    ...    currency=EUR
    ${resp}=    POST On Session    payment_api    /transfer
    ...    json=${payload}    expected_status=any
    Should Be Equal As Integers    ${resp.status_code}    422

Invalid Sender IBAN Format
    [Documentation]    Malformed sender IBAN is rejected at input validation
    [Tags]    error    validation    boundary
    ${payload}=    Create Dictionary
    ...    sender_iban=NOT-AN-IBAN
    ...    receiver_iban=${VALID_RECEIVER}
    ...    amount=${100}
    ...    currency=EUR
    ${resp}=    POST On Session    payment_api    /transfer
    ...    json=${payload}    expected_status=any
    Should Be Equal As Integers    ${resp.status_code}    422

Unsupported Currency Is Rejected
    [Documentation]    Currency codes outside the allowed set are rejected
    [Tags]    error    validation
    ${payload}=    Create Dictionary
    ...    sender_iban=${VALID_SENDER}
    ...    receiver_iban=${VALID_RECEIVER}
    ...    amount=${100}
    ...    currency=XYZ
    ${resp}=    POST On Session    payment_api    /transfer
    ...    json=${payload}    expected_status=any
    Should Be Equal As Integers    ${resp.status_code}    422

Fetch Non-Existent Transaction Returns 404
    [Documentation]    Looking up a random UUID as a transaction ID returns 404
    [Tags]    error    transaction
    ${resp}=    Get Transaction    00000000-0000-0000-0000-000000000000
    Should Be Equal As Integers    ${resp.status_code}    404

Invalid IBAN Format Fails Validation
    [Documentation]    A clearly malformed IBAN string is flagged as invalid
    [Tags]    error    validation
    ${resp}=    Validate IBAN    NOTANIBAN123
    IBAN Should Be Invalid    ${resp}    INVALID_FORMAT

Unsupported Country IBAN Fails Validation
    [Documentation]    An IBAN from an unsupported country is rejected
    [Tags]    error    validation
    ${resp}=    Validate IBAN    ZZ99123456789012
    IBAN Should Be Invalid    ${resp}    UNSUPPORTED_COUNTRY
