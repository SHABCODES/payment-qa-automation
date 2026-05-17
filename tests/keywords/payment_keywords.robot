*** Settings ***
Library     RequestsLibrary
Library     Collections
Library     String
Library     OperatingSystem

*** Variables ***
${BASE_URL}         http://localhost:8001
${VALID_SENDER}     FI2112345600000785
${VALID_RECEIVER}   DE89370400440532013000
${LOW_BALANCE}      FI1234567890123456
${TIMEOUT_IBAN}     FI0000000000000000


# --------------------------------------------------------------------------- #
# Session management
# --------------------------------------------------------------------------- #
*** Keywords ***
Create Payment Session
    [Documentation]    Opens a requests session to the payment API
    Create Session    payment_api    ${BASE_URL}    verify=False

API Should Be Healthy
    [Documentation]    Verifies the API health endpoint returns OK
    ${resp}=    GET On Session    payment_api    /health
    Should Be Equal As Integers    ${resp.status_code}    200
    ${body}=    Set Variable    ${resp.json()}
    Should Be Equal    ${body}[status]    ok


# --------------------------------------------------------------------------- #
# Transfer helpers
# --------------------------------------------------------------------------- #
Send Transfer
    [Documentation]    POSTs a transfer and returns the response object
    [Arguments]    ${sender}    ${receiver}    ${amount}    ${currency}=EUR    ${reference}=test-ref
    ${payload}=    Create Dictionary
    ...    sender_iban=${sender}
    ...    receiver_iban=${receiver}
    ...    amount=${amount}
    ...    currency=${currency}
    ...    reference=${reference}
    ${resp}=    POST On Session    payment_api    /transfer
    ...    json=${payload}    expected_status=any
    RETURN    ${resp}

Transfer Should Succeed
    [Documentation]    Asserts a transfer response is COMPLETED and returns the body
    [Arguments]    ${resp}
    Should Be Equal As Integers    ${resp.status_code}    200
    ${body}=    Set Variable    ${resp.json()}
    Should Be Equal    ${body}[status]    COMPLETED
    Should Not Be Empty    ${body}[transaction_id]
    RETURN    ${body}

Transfer Should Fail With
    [Documentation]    Asserts a transfer fails with a specific HTTP status and error code
    [Arguments]    ${resp}    ${expected_status}    ${expected_error}
    Should Be Equal As Integers    ${resp.status_code}    ${expected_status}
    ${body}=    Set Variable    ${resp.json()}
    Should Be Equal    ${body}[detail][error]    ${expected_error}


# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #
Validate IBAN
    [Documentation]    POSTs to /validate and returns the response
    [Arguments]    ${iban}    ${currency}=EUR
    ${payload}=    Create Dictionary    iban=${iban}    currency=${currency}
    ${resp}=    POST On Session    payment_api    /validate
    ...    json=${payload}    expected_status=any
    RETURN    ${resp}

IBAN Should Be Valid
    [Arguments]    ${resp}
    Should Be Equal As Integers    ${resp.status_code}    200
    ${body}=    Set Variable    ${resp.json()}
    Should Be True    ${body}[valid]

IBAN Should Be Invalid
    [Arguments]    ${resp}    ${expected_reason}
    Should Be Equal As Integers    ${resp.status_code}    200
    ${body}=    Set Variable    ${resp.json()}
    Should Not Be True    ${body}[valid]
    Should Be Equal    ${body}[reason]    ${expected_reason}


# --------------------------------------------------------------------------- #
# Transaction lookup helpers
# --------------------------------------------------------------------------- #
Get Transaction
    [Documentation]    GETs a transaction by ID
    [Arguments]    ${tx_id}
    ${resp}=    GET On Session    payment_api    /transaction/${tx_id}
    ...    expected_status=any
    RETURN    ${resp}

Transaction Should Exist
    [Arguments]    ${tx_id}
    ${resp}=    Get Transaction    ${tx_id}
    Should Be Equal As Integers    ${resp.status_code}    200
    ${body}=    Set Variable    ${resp.json()}
    Should Be Equal    ${body}[transaction_id]    ${tx_id}
    RETURN    ${body}


# --------------------------------------------------------------------------- #
# Account helpers
# --------------------------------------------------------------------------- #
Get Account Balance
    [Arguments]    ${iban}
    ${resp}=    GET On Session    payment_api    /account/${iban}/balance
    ...    expected_status=any
    RETURN    ${resp}

Reset Test State
    [Documentation]    Resets API accounts and transactions to initial state
    POST On Session    payment_api    /testing/reset    expected_status=200
