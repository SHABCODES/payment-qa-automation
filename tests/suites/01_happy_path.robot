*** Settings ***
Resource        ../keywords/payment_keywords.robot
Suite Setup     Create Payment Session

*** Test Cases ***

Health Check
    [Documentation]    API is reachable and reports healthy status
    [Tags]    smoke    health
    API Should Be Healthy

Successful EUR Transfer Between Known Accounts
    [Documentation]    A valid transfer between two known accounts completes
    [Tags]    smoke    transfer    happy-path
    ${resp}=    Send Transfer
    ...    sender=${VALID_SENDER}
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${100.00}
    ${body}=    Transfer Should Succeed    ${resp}
    Should Be Equal    ${body}[currency]    EUR
    Should Be Equal    ${body}[sender_iban]    ${VALID_SENDER}

Transaction Is Retrievable After Transfer
    [Documentation]    A completed transfer can be fetched by its transaction ID
    [Tags]    transfer    happy-path
    ${resp}=    Send Transfer
    ...    sender=${VALID_SENDER}
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${50.00}
    ${body}=    Transfer Should Succeed    ${resp}
    ${tx_id}=    Set Variable    ${body}[transaction_id]
    ${stored}=    Transaction Should Exist    ${tx_id}
    Should Be Equal    ${stored}[amount]    ${50.0}

Transfer With Custom Reference
    [Documentation]    Reference field is stored and returned correctly
    [Tags]    transfer    happy-path
    ${resp}=    Send Transfer
    ...    sender=${VALID_SENDER}
    ...    receiver=${VALID_RECEIVER}
    ...    amount=${25.00}
    ...    reference=INV-2024-001
    ${body}=    Transfer Should Succeed    ${resp}
    Should Be Equal    ${body}[reference]    INV-2024-001

Multi-Currency Transfer GBP
    [Documentation]    Transfer in GBP currency is accepted
    [Tags]    transfer    happy-path    multi-currency
    ${resp}=    Send Transfer
    ...    sender=${VALID_SENDER}
    ...    receiver=GB29NWBK60161331926819
    ...    amount=${75.00}
    ...    currency=GBP
    ${body}=    Transfer Should Succeed    ${resp}
    Should Be Equal    ${body}[currency]    GBP

Valid Finnish IBAN Passes Validation
    [Documentation]    A correctly formatted Finnish IBAN is validated as valid
    [Tags]    validation    happy-path
    ${resp}=    Validate IBAN    FI2112345600000785
    IBAN Should Be Valid    ${resp}

Valid German IBAN Passes Validation
    [Documentation]    A correctly formatted German IBAN is validated as valid
    [Tags]    validation    happy-path
    ${resp}=    Validate IBAN    DE89370400440532013000
    IBAN Should Be Valid    ${resp}

Account Balance Is Returned
    [Documentation]    Balance endpoint returns a positive numeric value
    [Tags]    account    happy-path
    ${resp}=    Get Account Balance    ${VALID_SENDER}
    Should Be Equal As Integers    ${resp.status_code}    200
    ${body}=    Set Variable    ${resp.json()}
    Should Be True    ${body}[balance] > 0
