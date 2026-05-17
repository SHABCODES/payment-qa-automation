*** Settings ***
Resource        ../keywords/payment_keywords.robot
Suite Setup     Run Keywords    Create Payment Session    AND    Reset Test State

*** Test Cases ***

Transfer At Exact Daily Limit Is Accepted
    [Documentation]    Transfer equal to the daily limit (9999.99) should be accepted
    [Tags]    boundary    limits
    ${resp}=    Send Transfer
    ...    sender=${VALID_SENDER}
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${9999.99}
    Transfer Should Succeed    ${resp}

Transfer One Cent Above Daily Limit Is Rejected
    [Documentation]    Transfer of 10000.00 must be rejected — one cent over the limit
    [Tags]    boundary    limits
    ${resp}=    Send Transfer
    ...    sender=${VALID_SENDER}
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${10000.00}
    Transfer Should Fail With    ${resp}    422    EXCEEDS_DAILY_LIMIT

Minimum Valid Transfer Amount
    [Documentation]    Transfer of 0.01 EUR (one cent) should succeed
    [Tags]    boundary    transfer
    ${resp}=    Send Transfer
    ...    sender=${VALID_SENDER}
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${0.01}
    Transfer Should Succeed    ${resp}

IBAN With Leading And Trailing Spaces Is Normalised
    [Documentation]    Spaces in IBAN input must be stripped before validation
    [Tags]    boundary    validation
    ${resp}=    Validate IBAN    FI21 1234 5600 0007 85
    IBAN Should Be Valid    ${resp}

Balance Is Reduced After Transfer
    [Documentation]    Account balance decreases by the transfer amount
    [Tags]    regression    account
    ${before_resp}=    Get Account Balance    ${VALID_SENDER}
    ${before}=    Set Variable    ${before_resp.json()}[balance]
    Send Transfer
    ...    sender=${VALID_SENDER}
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${100.00}
    ${after_resp}=    Get Account Balance    ${VALID_SENDER}
    ${after}=    Set Variable    ${after_resp.json()}[balance]
    ${expected}=    Evaluate    ${before} - 100.0
    Should Be Equal As Numbers    ${after}    ${expected}

Transaction Timestamp Is UTC ISO Format
    [Documentation]    Completed transactions carry a well-formed ISO 8601 UTC timestamp
    [Tags]    regression    transaction
    ${resp}=    Send Transfer
    ...    sender=${VALID_SENDER}
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${10.00}
    ${body}=    Transfer Should Succeed    ${resp}
    Should Match Regexp    ${body}[timestamp]
    ...    ^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}.*\\+00:00$

Concurrent Sequential Transfers Do Not Overdraw
    [Documentation]    Two sequential transfers that together exceed the balance: second should fail
    [Tags]    regression    funds
    ${resp1}=    Send Transfer
    ...    sender=${LOW_BALANCE}
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${100.00}
    Transfer Should Succeed    ${resp1}
    ${resp2}=    Send Transfer
    ...    sender=${LOW_BALANCE}
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${100.00}
    Transfer Should Fail With    ${resp2}    422    INSUFFICIENT_FUNDS

Transfer Returns All Required Fields
    [Documentation]    Response contains every mandatory field per the API contract
    [Tags]    regression    contract
    ${resp}=    Send Transfer
    ...    sender=${VALID_SENDER}
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${20.00}
    ${body}=    Transfer Should Succeed    ${resp}
    Dictionary Should Contain Key    ${body}    transaction_id
    Dictionary Should Contain Key    ${body}    sender_iban
    Dictionary Should Contain Key    ${body}    receiver_iban
    Dictionary Should Contain Key    ${body}    amount
    Dictionary Should Contain Key    ${body}    currency
    Dictionary Should Contain Key    ${body}    status
    Dictionary Should Contain Key    ${body}    timestamp
