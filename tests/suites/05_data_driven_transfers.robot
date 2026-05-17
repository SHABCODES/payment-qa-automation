*** Settings ***
Resource        ../keywords/payment_keywords.robot
Library         Collections
Library         OperatingSystem
Library         String
Suite Setup     Run Keywords    Create Payment Session    AND    Reset Test State

*** Test Cases ***

Data Driven Transfer Scenarios From CSV
    [Documentation]    Reads transfer_scenarios.csv and executes each scenario
    [Tags]    data-driven    transfer
    ${csv_path}=    Set Variable    ${CURDIR}/../data/transfer_scenarios.csv
    ${raw}=    Get File    ${csv_path}
    ${lines}=    Split To Lines    ${raw}
    ${data_rows}=    Get Slice From List    ${lines}    1
    FOR    ${line}    IN    @{data_rows}
        ${line}=    Strip String    ${line}
        Continue For Loop If    '${line}' == ''
        @{cols}=    Split String    ${line}    ,
        ${sender}=        Strip String    ${cols}[0]
        ${receiver}=      Strip String    ${cols}[1]
        ${amount}=        Convert To Number    ${cols}[2]
        ${currency}=      Strip String    ${cols}[3]
        ${exp_status}=    Convert To Integer    ${cols}[4]
        ${exp_error}=     Strip String    ${cols}[5]
        ${description}=   Strip String    ${cols}[6]
        Log    Testing: ${description}    console=True
        # Reset state before large transfers to avoid balance bleed
        IF    ${amount} > 1000
            Reset Test State
        END
        ${payload}=    Create Dictionary
        ...    sender_iban=${sender}
        ...    receiver_iban=${receiver}
        ...    amount=${amount}
        ...    currency=${currency}
        ...    reference=DD-TEST
        ${resp}=    POST On Session    payment_api    /transfer
        ...    json=${payload}    expected_status=any
        Should Be Equal As Integers    ${resp.status_code}    ${exp_status}
        IF    '${exp_error}' != ''
            ${body}=    Set Variable    ${resp.json()}
            Should Be Equal    ${body}[detail][error]    ${exp_error}
        END
    END
